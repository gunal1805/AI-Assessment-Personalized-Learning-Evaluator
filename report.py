"""Builds self-contained, printable HTML evaluation reports."""
import datetime
from html import escape as e

DISCLAIMER = ("This report is AI-assisted. Marks were suggested by a language model against the "
              "teacher's rubric. They are not fully objective and may contain errors, so they must be "
              "reviewed and approved by a teacher before they are used.")

CSS = """
body{font-family:Segoe UI,Helvetica,Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 20px;color:#1f2933;line-height:1.5}
h1{margin-bottom:0} h2{border-bottom:2px solid #d9e2ec;padding-bottom:4px;margin-top:32px}
table{width:100%;border-collapse:collapse} th,td{border:1px solid #d9e2ec;padding:8px;vertical-align:top;text-align:left}
th{background:#f0f4f8} .num{text-align:center;white-space:nowrap} .small{font-size:.85em;color:#52606d}
blockquote{margin:0 0 6px;padding:4px 10px;border-left:3px solid #9fb3c8;background:#f7f9fb}
.banner{background:#fff8e1;border:1px solid #f0d98c;padding:10px 14px;border-radius:6px}
.status{font-weight:600} .flags{color:#b44;margin:4px 0;padding-left:18px} .teacher{background:#eef7ee;padding:6px}
@media print{body{margin:0}}
"""


def _page(title, body):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{e(title)}</title>'
            f"<style>{CSS}</style></head><body>{body}</body></html>")


def _table(results, final_marks=None, comments=None):
    show_final = final_marks is not None
    comments = comments or [""] * len(results)
    rows = []
    for idx, r in enumerate(results):
        flags = "".join(f"<li>{e(f)}</li>" for f in r["flags"])
        flag_html = f'<ul class="flags">{flags}</ul>' if flags else ""
        ev = f"<blockquote>{e(r['evidence'])}</blockquote>" if r["evidence"] else "<em>No evidence quoted.</em>"
        final_cell = ""
        if show_final:
            fm = final_marks[idx]
            changed = " (changed)" if abs(fm - r["ai_marks"]) > 1e-9 else ""
            final_cell = f'<td class="num"><strong>{fm:g}</strong>{changed}</td>'
        cm = comments[idx]
        teacher = f'<p class="teacher"><strong>Teacher comment:</strong> {e(cm)}</p>' if cm.strip() else ""
        rows.append(f"""<tr><td><strong>{e(r['name'])}</strong><div class="small">{e(r['description'])}</div></td>
<td class="num">{r['ai_marks']:g} / {r['max_marks']:g}</td>{final_cell}
<td>{ev}<p>{e(r['reasoning'])}</p><div class="small">Confidence: {e(r['confidence'])}</div>{flag_html}{teacher}</td></tr>""")
    head = "<th>Criterion</th><th>AI marks</th>" + ("<th>Final marks</th>" if show_final else "") + "<th>Evidence and reasoning</th>"
    return f"<table><tr>{head}</tr>{''.join(rows)}</table>"


def _gaps_html(gaps):
    html = ""
    for g in gaps:
        qs = "".join(
            f"<li>{e(q.get('question', ''))} <span class='small'>[{e(str(q.get('difficulty', '')))}]"
            f"{' Hint: ' + e(str(q.get('hint', ''))) if q.get('hint') else ''}</span></li>"
            for q in g["practice_questions"])
        html += f"<h3>{e(g['concept'])} <span class='small'>({e(g['criterion'])})</span></h3><ol>{qs}</ol>"
    return html or "<p>No learning gaps detected at the chosen threshold.</p>"


def _refs_html(chunks):
    refs = "".join(f"<li><strong>{e(c.source)}, passage {c.index}:</strong> {e(c.text)}</li>" for c in chunks)
    return (f"<ol class='small'>{refs}</ol>" if refs else
            "<p class='small'>No reference material was used; the model relied on general knowledge.</p>")


def _header(title, mode_label, status):
    return (f"<h1>{e(title)}</h1><p class='small'>Generated {datetime.datetime.now():%d %b %Y, %H:%M} "
            f"&middot; Evaluator: {e(mode_label)}</p><p class='banner'>{e(DISCLAIMER)}</p>"
            f"<p class='status'>Status: {e(status)}</p>")


def build_report_html(question, response, results, final_marks, comments, gaps,
                      ai_overall, teacher_overall, reviewed, mode_label, chunks):
    ai_total, final_total = sum(r["ai_marks"] for r in results), sum(final_marks)
    max_total = sum(r["max_marks"] for r in results)
    status = "Reviewed and confirmed by teacher" if reviewed else "DRAFT - not yet confirmed by a teacher"
    body = (_header("Rubric-based Evaluation Report", mode_label, status)
            + f"<h2>Question</h2><p>{e(question)}</p><h2>Student response</h2><blockquote>{e(response)}</blockquote>"
            + f"<h2>Marks</h2><p><strong>AI-suggested total:</strong> {ai_total:g} / {max_total:g} &nbsp;|&nbsp; "
              f"<strong>Final total (teacher):</strong> {final_total:g} / {max_total:g}</p>"
            + _table(results, final_marks, comments)
            + f"<p><strong>AI overall comment:</strong> {e(ai_overall) or '-'}</p>"
              f"<p><strong>Teacher overall comment:</strong> {e(teacher_overall) or '-'}</p>"
            + f"<h2>Learning gaps and targeted practice</h2>{_gaps_html(gaps)}"
            + f"<h2>Reference passages used</h2>{_refs_html(chunks)}")
    return _page("Evaluation report", body)


def build_quiz_report_html(items, gaps, mode_label):
    """items: list of dicts with question, source, response, answered, results, overall, chunks."""
    total = sum(r["ai_marks"] for it in items for r in it["results"])
    max_total = sum(r["max_marks"] for it in items for r in it["results"])
    body = _header("Quiz Evaluation Report", mode_label, "AI-suggested marks - not reviewed by a teacher")
    body += f"<h2>Score</h2><p><strong>AI-suggested total:</strong> {total:g} / {max_total:g}</p>"
    for n, it in enumerate(items, 1):
        q_total = sum(r["ai_marks"] for r in it["results"])
        q_max = sum(r["max_marks"] for r in it["results"])
        src = f"<p class='small'>Source: {e(it['source'])}</p>" if it.get("source") else ""
        ans = e(it["response"]) if it["answered"] else "<em>No answer submitted.</em>"
        body += (f"<h2>Question {n} ({q_total:g} / {q_max:g})</h2><p>{e(it['question'])}</p>{src}"
                 f"<blockquote>{ans}</blockquote>{_table(it['results'])}")
    body += f"<h2>Learning gaps and targeted practice</h2>{_gaps_html(gaps)}"
    return _page("Quiz evaluation report", body)
