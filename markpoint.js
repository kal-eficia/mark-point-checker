/*! markpoint.js v1.0.0 · MIT · github.com/kal-eficia/mark-point-checker
 * The browser twin of markpoint/core.py. Same rules, same results:
 * both are run against tests/cases.json.
 */
(function (root) {
  "use strict";
  const NEGATIONS = new Set(["not", "no", "never", "cannot", "cant", "dont", "doesnt", "isnt", "arent", "wont", "without", "neither", "nor"]);
  const WINDOW = 3;
  const SUFFIXES = ["ing", "ed", "es", "s", "ly"];

  function normalise(text) {
    const t = String(text).normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/['’]/g, "").replace(/ but /g, " , ");
    return t.match(/[a-z0-9]+|[,;.!?:]/g) || [];
  }
  function stem(w) {
    for (const suf of SUFFIXES) {
      if (w.length > suf.length + 3 && w.endsWith(suf)) {
        w = w.slice(0, -suf.length);
        if ((suf === "ed" || suf === "ing") && w.length > 3 && w[w.length - 1] === w[w.length - 2]) w = w.slice(0, -1);
        return w;
      }
    }
    return w;
  }
  const isWord = (t) => /[a-z0-9]/.test(t[0]);
  function closeEnough(a, b) {
    if (!isWord(a) || !isWord(b)) return false;
    if (a === b) return true;
    a = stem(a); b = stem(b);
    if (a === b) return true;
    if (Math.min(a.length, b.length) < 5 || Math.abs(a.length - b.length) > 1) return false;
    if (a.length === b.length) {
      const d = [];
      for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) d.push(i);
      if (d.length === 1) return true;
      return d.length === 2 && d[1] === d[0] + 1 && a[d[0]] === b[d[1]] && a[d[1]] === b[d[0]];
    }
    const [s, l] = a.length < b.length ? [a, b] : [b, a];
    for (let i = 0; i < l.length; i++) if (l.slice(0, i) + l.slice(i + 1) === s) return true;
    return false;
  }
  function findPhrase(tokens, phrase) {
    const words = normalise(phrase);
    const hits = [];
    if (!words.length) return hits;
    for (let i = 0; i <= tokens.length - words.length; i++) {
      if (words.every((w, j) => closeEnough(tokens[i + j], w))) hits.push(i);
    }
    return hits;
  }
  function negated(tokens, index) {
    for (let i = index - 1; i >= Math.max(0, index - WINDOW); i--) {
      if (!isWord(tokens[i])) return false;
      if (NEGATIONS.has(tokens[i])) return true;
    }
    return false;
  }
  function groupHit(tokens, group) {
    for (const word of group) for (const idx of findPhrase(tokens, word)) if (!negated(tokens, idx)) return word;
    return null;
  }
  function checkPoint(tokens, point) {
    const base = { id: point.id, label: point.label || point.id, got: false, evidence: "", blockedBy: "" };
    for (const bad of point.forbid || []) {
      if (findPhrase(tokens, bad).some((i) => !negated(tokens, i))) return { ...base, blockedBy: bad };
    }
    for (const phrasing of point.accept || []) {
      const parts = typeof phrasing === "string" ? [phrasing] : phrasing;
      const groups = parts.map((p) => (typeof p === "string" ? [p] : p));
      const found = [];
      let ok = true;
      for (const g of groups) {
        const hit = groupHit(tokens, g);
        if (hit === null) { ok = false; break; }
        found.push(hit);
      }
      if (ok) return { ...base, got: true, evidence: found.join(" + ") };
    }
    return base;
  }
  function mark(answer, question) {
    const tokens = normalise(answer);
    const points = question.points.map((p) => checkPoint(tokens, p));
    const maxMarks = Number(question.marks || points.length);
    const score = Math.min(maxMarks, points.filter((p) => p.got).length);
    const flags = [];
    if (question.minWords && tokens.filter(isWord).length < question.minWords) flags.push(`Write a little more: aim for at least ${question.minWords} words.`);
    for (const p of points) if (p.blockedBy) flags.push(`Check "${p.blockedBy}": that isn't right here.`);
    const got = points.filter((p) => p.got), missing = points.filter((p) => !p.got);
    const parts = [!got.length ? "Not yet." : !missing.length || score >= maxMarks ? "Full marks." : "Good start."];
    if (got.length && missing.length && score < maxMarks) parts.push("You have got: " + got.map((p) => p.label).join(", ") + ".");
    if (missing.length && score < maxMarks) parts.push("Still to add: " + missing.map((p) => p.label).join(", ") + ".");
    parts.push(...flags);
    return { score, maxMarks, points, got, missing, flags, feedback: parts.join(" ") };
  }
  const api = { mark, normalise, stem, version: "1.0.0" };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.MarkPoint = api;
})(typeof window !== "undefined" ? window : globalThis);
