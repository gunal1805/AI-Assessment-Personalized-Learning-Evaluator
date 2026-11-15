"""LLM access. GeminiLLM talks to the real API; MockLLM is an offline demo stand-in."""
import json
import re
from collections import Counter


class LLMError(Exception):
    pass


def parse_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


class GeminiLLM:
    label = "Google Gemini"

    def __init__(self, api_key: str, model: str = "gemini-3.8-flash"):
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise LLMError("Install the SDK first:  python -m pip install google-genai") from e
        self._client = genai.Client(api_key=api_key)
        self._types = types
        self.model = model

    def generate_json(self, prompt, task=None, data=None, temperature=0.0):
        last_error = None
        for _ in range(2):                      # one retry on bad JSON / transient error
            try:
                resp = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=temperature,
                    ),
                )
                return parse_json(resp.text)
            except Exception as e:              # noqa: BLE001
                last_error = e
        raise LLMError(f"Gemini request failed: {last_error}")


# ----------------------------------------------------------------------------
# Demo mode: simple keyword overlap. NOT real AI grading - only for trying the UI.
# ----------------------------------------------------------------------------
_STOP = set("""a an the and or of to in on for with by is are was were be been it its this that these
those as at from into than then so such can will which who whom how why what when where their there
they them states explains explain distinguishes uses used produced produce""".split())


def _stems(text):
    return {w[:6] for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) > 2}


class MockLLM:
    label = "Demo mode (keyword matching)"

    def generate_json(self, prompt, task=None, data=None, temperature=0.0):
        if task == "evaluate":
            return self._evaluate(data)
        if task == "practice":
            return self._practice(data)
        if task == "questions":
            return self._questions(data)
        raise LLMError("Demo mode does not support this task.")

    def _evaluate(self, data):
        response = data["response"]
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", response.strip()) if s]
        resp_stems = _stems(response)
        out = []
        for c in data["criteria"]:
            crit = _stems(c["description"]) or _stems(c["name"])
            frac = len(crit & resp_stems) / len(crit) if crit else 0.0
            marks = round(min(frac / 0.6, 1.0) * c["max_marks"] * 2) / 2
            best, best_n = "", 0
            for s in sentences:
                n = len(crit & _stems(s))
                if n > best_n:
                    best, best_n = s, n
            if frac >= 0.7 or frac == 0:
                conf = "high"
            elif 0.25 <= frac < 0.5:
                conf = "low"
            else:
                conf = "medium"
            out.append({
                "name": c["name"],
                "marks_awarded": marks,
                "max_marks": c["max_marks"],
                "evidence": best,
                "reasoning": (f"DEMO MODE: {round(frac * 100)}% of the key terms in this criterion "
                              f"appear in the response. A real LLM judges meaning, not keywords."),
                "confidence": conf,
                "needs_teacher_review": conf == "low",
                "review_reason": "Partial keyword match - meaning unclear." if conf == "low" else "",
            })
        return {"criteria": out,
                "overall_comment": "DEMO MODE: marks are based on keyword overlap only."}

    def _practice(self, data):
        gaps = []
        for g in data["gaps"]:
            gaps.append({
                "criterion": g["criterion"],
                "concept": g["criterion"],
                "practice_questions": [
                    {"question": f"In your own words, define and describe: {g['criterion']}.",
                     "difficulty": "easy", "hint": "Start from the definition in your notes."},
                    {"question": f"Give an example that shows why '{g['criterion']}' matters, and explain it step by step.",
                     "difficulty": "medium", "hint": "Link cause and effect."},
                ],
            })
        return {"gaps": gaps}

    def _questions(self, data):
        passages, n, marks = data["passages"], data["n"], data["marks"]
        out = []
        used_topics = {}
        for k in range(n):
            p = passages[k % len(passages)]
            sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", p["text"]) if len(x.split()) >= 6]
            if not sents:
                continue
            reuse = k // len(passages)
            chosen = sents[reuse * 2: reuse * 2 + 3] or sents[:3]
            words = [w for w in re.findall(r"[a-z]{5,}", " ".join(chosen).lower()) if w not in _STOP]
            topics = used_topics.setdefault(p["number"], set())
            topic = next((word for word, _ in Counter(words).most_common() if word not in topics),
                         "this topic")
            topics.add(topic)
            each = max(round(marks / len(chosen) * 2) / 2, 0.5)
            suffix = f" (set {reuse + 1})" if reuse else ""
            out.append({
                "question": f"Discuss the key ideas about '{topic}' covered in this part of the material.{suffix}",
                "source_passage": p["number"],
                "rubric": [{"name": self._point_name(sent, j), "description": sent, "max_marks": each}
                           for j, sent in enumerate(chosen)],
            })
        return {"questions": out}

    @staticmethod
    def _point_name(sentence, j):
        words = [w for w in re.findall(r"[A-Za-z]{5,}", sentence) if w.lower() not in _STOP]
        return f"Understands '{max(words, key=len).lower()}'" if words else f"Key point {j + 1}"
