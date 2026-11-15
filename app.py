"""AI Education Assessment & Personalized Learning Evaluator (Streamlit)."""
import os

import pandas as pd
import streamlit as st

import samples
from evaluator import Criterion, evaluate_response, find_gaps, generate_practice
from llm import GeminiLLM, LLMError, MockLLM
from rag import Retriever, chunk_text, load_document
from report import DISCLAIMER, build_report_html

st.set_page_config(page_title="Assessment & Learning Evaluator", page_icon="📝", layout="wide")


def md_safe(text: str) -> str:
    for ch in "\\`*_#<>":
        text = text.replace(ch, "\\" + ch)
    return text.replace("\n", " ")


# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("Evaluator", ["Demo mode (no API key)", "Google Gemini"])
    api_key = model = ""
    if provider == "Google Gemini":
        api_key = st.text_input("Gemini API key", type="password",
                                value=os.getenv("GEMINI_API_KEY", ""),
                                help="Free key from Google AI Studio. Never share or commit it.")
        model = st.text_input("Model name", value=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
                              help="Use any current Gemini model name from AI Studio.")
    threshold_pct = st.slider("Treat a criterion as a learning gap below (% of its marks)", 10, 100, 60, 5)
    n_questions = st.slider("Practice questions per gap", 1, 4, 2)

    st.divider()
    st.subheader("Course material (RAG)")
    uploads = st.file_uploader("Upload notes or textbook (PDF / TXT)", type=["pdf", "txt", "md"],
                               accept_multiple_files=True)
    use_sample_notes = st.checkbox("Also use built-in sample notes (photosynthesis)", value=True)

st.title("📝 AI Assessment & Personalized Learning Evaluator")
st.caption(DISCLAIMER)
if provider.startswith("Demo"):
    st.warning("Demo mode: marks come from simple keyword matching, not a language model. "
               "Switch to Google Gemini in the sidebar for real meaning-based evaluation.")

# ----------------------------------------------------------------------------- inputs
st.subheader("1. Question, rubric and student response")
question = st.text_area("Question", value=samples.SAMPLE_QUESTION, height=80, key="question")
st.markdown("**Marking rubric** (add, edit or delete rows)")
rubric_df = st.data_editor(
    pd.DataFrame(samples.SAMPLE_RUBRIC), num_rows="dynamic", key="rubric_editor",
    column_config={"Max marks": st.column_config.NumberColumn(min_value=0.5, step=0.5)},
)
response_text = st.text_area("Student response", value=samples.SAMPLE_RESPONSE, height=160, key="response")


def build_retriever():
    chunks = []
    for f in uploads or []:
        chunks += chunk_text(load_document(f.name, f.getvalue()), f.name)
    if use_sample_notes:
        chunks += chunk_text(samples.SAMPLE_NOTES, samples.SAMPLE_NOTES_NAME)
    return Retriever(chunks)


def make_llm():
    if provider.startswith("Demo"):
        return MockLLM()
    if not api_key:
        raise LLMError("Enter your Gemini API key in the sidebar.")
    return GeminiLLM(api_key, model)


if st.button("Evaluate response", type="primary"):
    criteria = []
    for row in rubric_df.to_dict("records"):
        name = str(row.get("Criterion") or "").strip()
        if not name or pd.isna(row.get("Max marks")):
            continue
        criteria.append(Criterion(name, str(row.get("Description") or "").strip(), float(row["Max marks"])))
    if not criteria:
        st.error("Add at least one rubric criterion with a name and max marks.")
    elif not response_text.strip() or not question.strip():
        st.error("Question and student response cannot be empty.")
    else:
        try:
            with st.spinner("Evaluating against the rubric..."):
                llm = make_llm()
                retriever = build_retriever()
                results, ai_overall, chunks = evaluate_response(llm, retriever, question, criteria, response_text)
                gaps = generate_practice(llm, retriever, question, results,
                                         threshold=threshold_pct / 100, n_questions=n_questions)
            st.session_state["evaluation"] = {
                "id": st.session_state.get("eval_counter", 0) + 1,
                "question": question, "response": response_text, "results": results,
                "ai_overall": ai_overall, "chunks": chunks, "gaps": gaps,
                "mode": llm.label + (f" ({model})" if provider == "Google Gemini" else ""),
            }
            st.session_state["eval_counter"] = st.session_state["evaluation"]["id"]
        except LLMError as err:
            st.error(str(err))
        except Exception as err:  # noqa: BLE001
            st.error(f"Something went wrong: {err}")

# ----------------------------------------------------------------------------- results
ev = st.session_state.get("evaluation")
if ev:
    eid, results = ev["id"], ev["results"]
    final_default = [r["ai_marks"] for r in results]
    final_now = [float(st.session_state.get(f"final_{eid}_{i}", d)) for i, d in enumerate(final_default)]
    max_total = sum(r["max_marks"] for r in results)
    flagged = sum(1 for r in results if r["flags"])

    st.divider()
    st.subheader("2. Criterion-level evaluation and teacher review")
    c1, c2, c3 = st.columns(3)
    c1.metric("AI-suggested total", f"{sum(final_default):g} / {max_total:g}")
    c2.metric("Final total (after your review)", f"{sum(final_now):g} / {max_total:g}")
    c3.metric("Criteria flagged for review", f"{flagged} of {len(results)}")
    if not ev["chunks"]:
        st.warning("No reference material was found for this question, so the evaluator relied on "
                   "general knowledge. Treat these marks with extra caution.")

    for i, r in enumerate(results):
        with st.container(border=True):
            head, marks_col = st.columns([4, 1])
            icon = "⚠️" if r["flags"] else "✅"
            head.markdown(f"**{icon} {r['name']}**  \n:gray[{r['description']}]")
            marks_col.markdown(f"### {r['ai_marks']:g} / {r['max_marks']:g}")
            if r["evidence"]:
                tag = "" if r["evidence_verified"] else "  *(not found word-for-word in the answer)*"
                st.markdown(f"> {md_safe(r['evidence'])}{tag}")
            else:
                st.markdown("*No evidence quoted from the answer.*")
            st.markdown(f"**Reasoning:** {md_safe(r['reasoning'])}  \n:gray[Model confidence: {r['confidence']}]")
            for flag in r["flags"]:
                st.markdown(f":orange[⚑ {md_safe(flag)}]")
            a, b = st.columns([1, 3])
            a.number_input("Final marks", min_value=0.0, max_value=float(r["max_marks"]), step=0.5,
                           value=float(r["ai_marks"]), key=f"final_{eid}_{i}")
            b.text_input("Teacher comment (optional)", key=f"comment_{eid}_{i}")

    if ev["ai_overall"]:
        st.info(f"**AI overall comment:** {ev['ai_overall']}")
    teacher_overall = st.text_area("Teacher overall comment (optional)", key=f"overall_{eid}")

    with st.expander(f"Reference passages the evaluator used ({len(ev['chunks'])})"):
        for c in ev["chunks"]:
            st.markdown(f"**{c.source}, passage {c.index}**")
            st.caption(c.text)

    st.divider()
    st.subheader("3. Learning gaps and targeted practice")
    if not ev["gaps"]:
        st.success("No learning gaps at the chosen threshold.")
    for g in ev["gaps"]:
        with st.container(border=True):
            st.markdown(f"**{g['concept']}**  :gray[(criterion: {g['criterion']})]")
            for n, q in enumerate(g["practice_questions"], 1):
                hint = f"  \n:gray[Hint: {q.get('hint')}]" if q.get("hint") else ""
                st.markdown(f"{n}. {q.get('question', '')} :gray[[{q.get('difficulty', '')}]]{hint}")

    st.divider()
    st.subheader("4. Report")
    reviewed = st.checkbox("I have reviewed these marks and confirm them", key=f"reviewed_{eid}")
    comments = [st.session_state.get(f"comment_{eid}_{i}", "") for i in range(len(results))]
    html = build_report_html(ev["question"], ev["response"], results, final_now, comments, ev["gaps"],
                             ev["ai_overall"], teacher_overall, reviewed, ev["mode"], ev["chunks"])
    st.download_button("Download evaluation report (HTML)", data=html, file_name="evaluation_report.html",
                       mime="text/html", type="primary")
    st.caption("Open the file in a browser and use Print → Save as PDF if you need a PDF.")
