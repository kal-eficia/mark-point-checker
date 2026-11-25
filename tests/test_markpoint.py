import json
import shutil
import subprocess
import unittest
from pathlib import Path

from markpoint import mark
from markpoint.core import close_enough, negated, normalise

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = {q["id"]: q for q in json.loads((ROOT / "examples/questions.json").read_text())["questions"]}
CASES = json.loads((ROOT / "tests/cases.json").read_text())


class SharedCases(unittest.TestCase):
    """The same cases run against the JavaScript twin below."""

    def test_python_cases(self):
        for c in CASES:
            r = mark(c["answer"], QUESTIONS[c["q"]])
            with self.subTest(answer=c["answer"]):
                self.assertEqual(r.score, c["score"])
                self.assertEqual([p.id for p in r.got], c["got"])

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_javascript_twin_matches(self):
        script = (
            "const M=require(process.argv[1]);const Q=require(process.argv[2]).questions;"
            "const C=require(process.argv[3]);const byId=Object.fromEntries(Q.map(q=>[q.id,q]));"
            "console.log(JSON.stringify(C.map(c=>{const r=M.mark(c.answer,byId[c.q]);"
            "return [r.score,r.got.map(p=>p.id),r.feedback]})))"
        )
        out = subprocess.run(["node", "-e", script, str(ROOT / "markpoint.js"), str(ROOT / "examples/questions.json"),
                              str(ROOT / "tests/cases.json")], capture_output=True, text=True, check=True)
        js = json.loads(out.stdout)
        for c, (score, got, feedback) in zip(CASES, js):
            py = mark(c["answer"], QUESTIONS[c["q"]])
            with self.subTest(answer=c["answer"]):
                self.assertEqual(score, py.score)
                self.assertEqual(got, [p.id for p in py.got])
                self.assertEqual(feedback, py.feedback())


class Matching(unittest.TestCase):
    def test_spelling_slips(self):
        self.assertTrue(close_enough("imputs", "input"))
        self.assertTrue(close_enough("assending", "ascending"))
        self.assertTrue(close_enough("unplugged", "unplug"))
        self.assertFalse(close_enough("cat", "car"))

    def test_negation_stops_at_clause_break(self):
        t = normalise("not descending, ascending")
        self.assertTrue(negated(t, t.index("descending")))
        self.assertFalse(negated(t, t.index("ascending")))

    def test_min_words_flag(self):
        q = dict(QUESTIONS["logic-gate"], minWords=10)
        self.assertIn("Write a little more", mark("input output", q).feedback())


if __name__ == "__main__":
    unittest.main()
