"""What may reach a hosted copy of the dashboard: the leak check on the exported folder, and the
page's defences against hostile model output and hostile names (nothing in them may run)."""
import contextlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from bambench import site_check, static_site
from bambench.paths import SITE

ROOT = Path(__file__).resolve().parents[1]
_EXPORT = None


def exported() -> Path:
    """One clean export, copied fresh for each test that plants something in it."""
    global _EXPORT
    if _EXPORT is None:
        base = Path(tempfile.mkdtemp())
        empty = base / "empty"
        with mock.patch("bambench.runner.published_dir", lambda t: empty / t), \
                mock.patch("bambench.runner.summary_dir", lambda t: empty / "none" if t == "closed" else
                           ROOT / "results" / "open" / "summaries"), \
                mock.patch("bambench.runner.closed_progress", lambda: None):
            static_site.export(base / "public")
        _EXPORT = base / "public"
    out = Path(tempfile.mkdtemp()) / "public"
    shutil.copytree(_EXPORT, out)
    return out


def edit_json(path: Path, change):
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


CLOSED_LINE = "Die Prüfung ergab eine Abweichung von 0,42 mm am Flansch der Probe 3"
SHORT_LINE = "Riss am Flansch, Probe 3"  # 24 characters


def no_closed_track():
    return mock.patch("bambench.site_check._closed_needles", lambda: ([], set()))


def closed_track(names=(), lines=()):
    norm = site_check._norm
    return mock.patch("bambench.site_check._closed_needles",
                      lambda: ([(w, norm(s)) for w, s in names], {norm(x) for x in lines}))


class LeakCheck(unittest.TestCase):
    def setUp(self):
        self.pub = exported()
        self.addCleanup(shutil.rmtree, self.pub.parent)
        self.cleared = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.cleared)
        p = mock.patch("bambench.site_check.published_dir", lambda t: self.cleared)
        p.start()
        self.addCleanup(p.stop)

    def problems(self):
        with no_closed_track():
            return site_check.check(self.pub)

    def test_a_clean_export_passes(self):
        self.assertEqual(self.problems(), [])

    def test_any_file_export_site_does_not_write_fails(self):
        (self.pub / "api" / "page-1.png").write_bytes(b"\x89PNG")
        (self.pub / "report.pdf").write_bytes(b"%PDF-1.7")
        (self.pub / "notes.txt").write_text(CLOSED_LINE)
        (self.pub / "logo.svg").write_text('<svg><image href="data:image/png;base64,AAAA"/></svg>')
        (self.pub / "api" / "extra.json").write_text("{}")
        self.assertEqual(len(self.problems()), 5, self.problems())

    def test_a_document_outside_the_open_track_fails_as_a_value_or_in_a_list(self):
        edit_json(self.pub / "api" / "documents.json", lambda d: d.append({"document_id": "internal-report-7"}))
        edit_json(self.pub / "api" / "about.json", lambda d: d.update({"document_id": ["bam-b001", "closed-123"]}))
        found = self.problems()
        self.assertTrue(any("internal-report-7" in p for p in found), found)
        self.assertTrue(any("closed-123" in p for p in found), found)
        self.assertFalse(any("bam-b001" in p for p in found), found)

    def test_page_text_fails(self):
        edit_json(self.pub / "api" / "leaderboard.json",
                  lambda d: d.append({"system": "x", "open": {"page_items": {"bam-b001/1": {"t": 0.9}}}}))
        self.assertTrue(any("page_items" in p for p in self.problems()))

    def closed_row(self, pages=25, publishable=True, run_id="r1", shape="scores"):
        res = {"track": "closed", "counts": {"pages": pages}, "publishable": publishable, "run_id": run_id}
        res.update({"scores": {"overall": 0.8}} if shape == "scores" else {"overall": 0.8})
        return res

    def clear(self, system="x", run_id="r1"):
        (self.cleared / f"{system}.json").write_text(json.dumps({"system": system, "run_id": run_id}))

    def test_a_closed_result_on_too_few_pages_fails_in_any_shape(self):
        self.clear()
        edit_json(self.pub / "api" / "leaderboard.json",
                  lambda d: d.append({"system": "x", "closed": self.closed_row(pages=12, shape="flat")}))
        edit_json(self.pub / "api" / "about.json", lambda d: d.update({"closed_score": {**self.closed_row(pages=12), "system": "x"}}))
        found = [p for p in self.problems() if "12 pages" in p]
        self.assertEqual(len(found), 2, found)

    def test_a_closed_result_export_closed_did_not_clear_fails(self):
        edit_json(self.pub / "api" / "leaderboard.json", lambda d: d.append({"system": "x", "closed": self.closed_row()}))
        self.assertTrue(any("not cleared" in p for p in self.problems()))
        self.clear(run_id="an-older-run")
        self.assertTrue(any("not cleared" in p for p in self.problems()))

    def test_a_cleared_closed_result_passes(self):
        self.clear()
        edit_json(self.pub / "api" / "leaderboard.json", lambda d: d.append({"system": "x", "closed": self.closed_row()}))
        self.assertEqual(self.problems(), [])

    def test_closed_text_is_found_through_json_escaping_and_unicode_forms(self):
        # ensure_ascii writes \\u00fc; the decomposed form writes u plus a combining mark.
        decomposed = CLOSED_LINE.replace("ü", "ü")
        edit_json(self.pub / "api" / "about.json", lambda d: d.update({"note": CLOSED_LINE, "other": "x\n" + decomposed + "\ny"}))
        self.assertIn("\\u00fc", (self.pub / "api" / "about.json").read_text())
        with closed_track(lines=[CLOSED_LINE]):
            found = site_check.check(self.pub)
        self.assertEqual(len(found), 1, found)
        self.assertIn("closed label or output text", found[0])

    def test_short_closed_lines_and_names_inside_longer_text_are_found(self):
        edit_json(self.pub / "api" / "about.json", lambda d: d.update({"a": SHORT_LINE}))
        with closed_track(lines=[SHORT_LINE]):
            self.assertTrue(site_check.check(self.pub))
        edit_json(self.pub / "api" / "about.json", lambda d: d.update({"a": "see Prüfbericht  KR-2024-17 for details"}))
        with closed_track(names=[("closed document title", "Prüfbericht KR-2024-17")]):
            self.assertTrue(any("closed document title" in p for p in site_check.check(self.pub)))

    def test_closed_model_output_lines_are_collected(self):
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base)
        out = base / "runs" / "sys" / "run1" / "doc"
        out.mkdir(parents=True)
        (out / "page-001.md").write_text("short\n" + CLOSED_LINE + "\n", encoding="utf-8")
        doc = mock.Mock(document_id="internal-1", sha256="abc", title="")
        with mock.patch("bambench.site_check.load_documents", lambda t: [doc] if t == "closed" else []), \
                mock.patch("bambench.site_check.page_statuses", lambda d: {}), \
                mock.patch("bambench.site_check.run_dir", lambda t: base / "runs"):
            names, lines = site_check._closed_needles()
        self.assertIn(site_check._norm(CLOSED_LINE), lines)
        self.assertNotIn("short", lines)
        self.assertIn(("closed document id", "internal-1"), names)

    def test_the_command_fails_with_a_nonzero_exit(self):
        from bambench.cli import main
        (self.pub / "leak.pdf").write_bytes(b"%PDF")
        with no_closed_track(), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["check-site", str(self.pub)]), 1)
        self.assertIn("do not publish", out.getvalue())


class PageDefences(unittest.TestCase):
    def test_the_page_has_one_policy_that_keeps_scripts_requests_and_images_on_the_site(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        metas = re.findall(r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]*)"', html, re.I)
        self.assertEqual(len(metas), 1, "exactly one policy, so a second one cannot loosen it")
        rules = {}
        for part in metas[0].split(";"):
            name, *values = part.split()
            self.assertNotIn(name, rules, f"{name} given twice")
            rules[name] = set(values)
        self.assertEqual(rules["default-src"], {"'self'"})
        self.assertEqual(rules["script-src"], {"'self'"})
        self.assertEqual(rules["connect-src"], {"'self'"})
        self.assertEqual(rules["img-src"], {"'self'", "data:", "blob:"})
        self.assertEqual(rules["object-src"], {"'none'"})
        self.assertEqual(rules["base-uri"], {"'none'"})


HOSTILE = [
    "<script>window.__pwned = 1</script>",
    "<img src=x onerror=\"window.__pwned = 2\">",
    "<table><tr><td onmouseover=\"window.__pwned = 3\"><svg onload=\"window.__pwned = 4\"></svg></td></tr></table>",
    "<a href=\"javascript:window.__pwned = 5\">click</a>",
    "| a | <iframe src=\"javascript:parent.__pwned = 6\"></iframe> |\n|---|---|\n| 1 | 2 |",
    "$$<img src=x onerror=\"window.__pwned = 7\">$$",
    "<math><mtext><table><mglyph><style><img src=x onerror=\"window.__pwned = 8\"></style></mglyph></table></mtext></math>",
    "<details open ontoggle=\"window.__pwned = 9\">x</details>",
]
EVIL = '<img src=x onerror="window.__pwned = 99">'

# Runs inside the page. Returns what survived as markup, and whether anything ran.
PROBE = r"""
const { chromium } = require("playwright");
(async () => {
  const [url, payloads, evil] = [process.argv[1], JSON.parse(process.argv[2]), process.argv[3]];
  const browser = await chromium.launch();
  const out = {};
  // 1. Sanitizer alone: the policy is bypassed, so only renderMarkdown stands between payload and page.
  for (const [name, bypassCSP] of [["sanitizer", true], ["policy", false]]) {
    const page = await (await browser.newContext({ bypassCSP })).newPage();
    await page.goto(url);
    await page.waitForFunction(() => typeof renderMarkdown === "function" && typeof classResults === "function");
    out[name] = await page.evaluate(async ([payloads, evil, underPolicy]) => {
      const box = document.createElement("div");
      document.body.appendChild(box);
      const found = [];
      const inspect = (allowedTags, allowedAttrs) => box.querySelectorAll("*").forEach((el) => {
        if (!allowedTags.includes(el.tagName)) found.push(el.tagName);
        for (const a of el.attributes) {
          if (!allowedAttrs.includes(a.name)) found.push(a.name);
          if (a.name === "href" && !a.value.startsWith("#/")) found.push("href=" + a.value);
        }
      });
      const md = ["TABLE", "THEAD", "TBODY", "TR", "TD", "TH", "SUP", "SUB", "B", "I", "EM", "STRONG", "BR", "P", "H1", "H2", "H3", "H4", "H5", "UL", "OL", "LI", "SPAN", "CODE", "PRE"];
      for (const p of payloads) {
        box.innerHTML = renderMarkdown(p);
        inspect(md, ["colspan", "rowspan", "class"]);
        box.querySelectorAll("td, th, details").forEach((el) => el.dispatchEvent(new MouseEvent("mouseover")));
      }
      // 2. The class panels with hostile names, document types, kinds and track.
      const res = (o) => ({ scores: { overall: o }, counts: { pages: 9, tables: 1 }, by_kind: { [evil]: { pages: 9, overall: o } }, by_lang: { de: { pages: 9, overall: o } } });
      const lb = [{ system: evil, card: { name: evil }, open: res(0.9) }, { system: "b", card: { name: evil }, open: res(0.9) }, { system: "c", card: {}, open: res(0.5) }];
      const comp = { open: { labelled: 9, documents: 1, by_status: { checked: 1 }, by_doc_type: { [evil]: { documents: 1 } }, by_kind: { [evil]: 9 }, by_lang: { [evil]: 9 } } };
      const panel = ["H2", "P", "DIV", "TABLE", "TBODY", "TR", "TH", "TD", "A", "SPAN", "UL", "LI"];
      box.innerHTML = classBasis(comp, lb, "open") + classResults(lb, "open");
      const tied = box.textContent.includes("tie");
      inspect(panel, ["class", "id", "href", "title", "scope"]);
      box.innerHTML = classBasis({ [evil]: comp.open }, [], evil);
      inspect(panel, ["class", "id", "href", "title", "scope"]);
      // 3. Under the policy, an inline handler injected directly must not run.
      if (underPolicy) box.innerHTML = evil;
      await new Promise((r) => setTimeout(r, 400));
      return { pwned: window.__pwned || null, found, tied };
    }, [payloads, evil, !bypassCSP]);
  }
  console.log(JSON.stringify(out));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(2); });
"""

CHECK = "const pw = require('playwright'); process.exit(require('fs').existsSync(pw.chromium.executablePath()) ? 0 : 1)"


def _node(args, **kw):
    # Run from the repository, so require() finds Playwright the same way for the check and the probe.
    return subprocess.run(["node", *args], capture_output=True, text=True, cwd=ROOT, **kw)


def _browser_available() -> bool:
    try:
        return _node(["-e", CHECK], timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@unittest.skipUnless(_browser_available(), "needs node with Playwright and its Chromium")
class HostileModelOutput(unittest.TestCase):
    """A model output is shown on the local dashboard next to closed pages. If a script in it ran, it
    could read those pages through the local API, so nothing in an output or a name may become live
    markup, with or without the page's policy."""

    @classmethod
    def setUpClass(cls):
        from bambench.server import Handler
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        srv.local_only = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        r = _node(["-e", PROBE, f"http://127.0.0.1:{srv.server_port}/#/about", json.dumps(HOSTILE), EVIL], timeout=120)
        srv.shutdown()
        srv.server_close()
        if r.returncode != 0:
            raise AssertionError(r.stderr)
        cls.res = json.loads(r.stdout.strip().splitlines()[-1])

    def test_the_sanitizer_alone_stops_every_payload(self):
        self.assertIsNone(self.res["sanitizer"]["pwned"], self.res["sanitizer"])
        self.assertEqual(self.res["sanitizer"]["found"], [], self.res["sanitizer"])

    def test_the_policy_blocks_an_inline_handler_that_got_through(self):
        self.assertIsNone(self.res["policy"]["pwned"], self.res["policy"])

    def test_class_panels_escape_names_and_mark_ties(self):
        self.assertTrue(self.res["sanitizer"]["tied"])


if __name__ == "__main__":
    unittest.main()
