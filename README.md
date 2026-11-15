# AI Assessment & Personalized Learning Evaluator (TP10)

Evaluates a descriptive answer against a teacher's rubric, explains every mark, finds
learning gaps, generates targeted practice questions, and produces a report that a teacher
reviews and confirms. **Marks are AI suggestions, not objective grades.**

## Run it
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Use the same Python for both commands (important if you have several Pythons installed).

**AI question generation from a PDF:** choose "Google Gemini" in the sidebar and enter a
key from Google AI Studio (or set the `GEMINI_API_KEY` environment variable). Upload a
text-based PDF in the main page and click *Generate questions*. The backend extracts its
text and sends selected passages to Gemini to write questions and rubrics. Scanned PDFs
need OCR first. Do not commit your key.

**Demo mode** works with no API key for trying the interface and sample notes. It uses
keyword matching rather than AI and cannot generate questions from uploaded PDFs.

## Two modes (tabs)
**Quiz from subject PDF** - upload the subject PDF in the main page, choose the number of questions and marks, click
*Generate questions*, let the student type answers, then *Submit answers*. The app writes the questions and a marking
rubric for each from the PDF (`quiz.py`), evaluates every answer, shows criterion-level marks, finds learning gaps
and downloads a quiz report. Blank answers score 0.
**Evaluate one answer (teacher)** - the teacher enters their own question and rubric, evaluates one answer, and can
override each mark before confirming the report.

## How it works
1. `rag.py`   - reads PDF/TXT notes, splits them into chunks, indexes them (TF-IDF) and retrieves relevant passages (RAG).
2. `evaluator.py` - builds a rubric prompt, asks the LLM for per-criterion marks, evidence quote, reasoning and confidence, then validates the output.
3. Guardrails - marks are clamped to the allowed range; quoted evidence must appear word-for-word in the answer; low confidence, missing or unsupported marks are flagged for teacher review; the student's text is treated as data, not instructions.
4. Learning gaps - criteria below the threshold become gaps; the LLM writes targeted practice questions using the notes.
5. `quiz.py`  - picks passages spread across the PDF and asks the LLM for questions with rubrics (validated before use).
6. `app.py`   - teacher can override each mark, add comments, confirm the review, and download `report.py`'s HTML report (print to PDF if needed).

## Requirement checklist
| Requirement | Where |
|---|---|
| Question + rubric + student response | `app.py` inputs |
| Evaluate against rubric, not exact wording | LLM prompt in `evaluator.py` |
| Marks with criterion-level explanations | per-criterion evidence, reasoning, confidence |
| Learning gaps + targeted practice | `find_gaps`, `generate_practice` |
| Transparent reasoning + teacher review | flags, override fields, confirm checkbox, report status |
| No claim of objective grading | disclaimer in app and report |

## Known limits / ideas to extend
- Retrieval uses TF-IDF; swap `Retriever` for embeddings + a vector database for better matching.
- Scanned PDFs have no text layer; run OCR first (the app warns when a PDF has almost no readable text).
- Upload the student response as PDF/image (OCR) instead of typing it.
- Let the teacher review and edit generated questions and rubrics before the student sees them.
- Evaluate a whole class and show per-concept weaknesses across students.
- Compare AI marks with teacher marks over time to measure agreement.
