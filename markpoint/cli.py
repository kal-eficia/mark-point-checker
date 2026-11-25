"""markpoint command line.

  markpoint check examples/questions.json logic-gate "It takes inputs and gives an output"
  markpoint batch examples/questions.json answers.csv -o marked.csv
  markpoint try   examples/questions.json            (type answers, see feedback)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from . import __version__
from .core import mark


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    qs = data["questions"] if isinstance(data, dict) else data
    return {q["id"]: q for q in qs}


def show(q, answer):
    r = mark(answer, q)
    print(f"{r.score}/{r.max_marks}  {r.feedback()}")
    for p in r.points:
        tick = "✓" if p.got else "·"
        why = f"  ({p.evidence})" if p.evidence else (f"  (blocked by \"{p.blocked_by}\")" if p.blocked_by else "")
        print(f"  {tick} {p.label}{why}")
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="markpoint", description="Mark short answers against marking points.")
    ap.add_argument("--version", action="version", version=f"markpoint {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("questions"); c.add_argument("id"); c.add_argument("answer")
    b = sub.add_parser("batch", help="CSV with columns student,question_id,answer")
    b.add_argument("questions"); b.add_argument("answers"); b.add_argument("-o", "--output")
    t = sub.add_parser("try"); t.add_argument("questions")
    a = ap.parse_args(argv)

    qs = load(a.questions)
    if a.cmd == "check":
        if a.id not in qs:
            ap.error(f"no question with id {a.id!r}; have: {', '.join(qs)}")
        show(qs[a.id], a.answer)
        return 0
    if a.cmd == "batch":
        rows = list(csv.DictReader(open(a.answers, newline="", encoding="utf-8")))
        out = open(a.output, "w", newline="", encoding="utf-8") if a.output else sys.stdout
        w = csv.writer(out)
        w.writerow(["student", "question_id", "score", "max", "got", "missing", "feedback"])
        for row in rows:
            q = qs[row["question_id"]]
            r = mark(row["answer"], q)
            w.writerow([row.get("student", ""), row["question_id"], r.score, r.max_marks,
                        "; ".join(p.id for p in r.got), "; ".join(p.id for p in r.missing), r.feedback()])
        return 0
    for qid, q in qs.items():
        print(f"\n{q['q']}  [{q.get('marks', len(q['points']))} marks]")
        try:
            ans = input("> ")
        except EOFError:
            break
        show(q, ans)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
