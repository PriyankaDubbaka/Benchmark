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
SHORT_LINE = "Riss am Flansch, Probe 3"  # 5 words, 24 characters


def no_closed_track():
    return mock.patch("bambench.site_check._closed_needles", site_check.Needles)


def closed_track(tokens=(), text=()):
    def needles():
        n = site_check.Needles()
        for what, tok in tokens:
            n.tokens[tok.casefold()] = what
        for t in text:
            n.add_text(t)
        return n
    return mock.patch("bambench.site_check._closed_needles", needles)


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

    def about(self, **kw):
        edit_json(self.pub / "api" / "about.json", lambda d: d.update(kw))

    def test_a_clean_export_passes(self):
        self.assertEqual(self.problems(), [])

    def test_any_file_export_site_does_not_write_fails(self):
        (self.pub / "api" / "page-1.png").write_bytes(b"\x89PNG")
        (self.pub / "report.pdf").write_bytes(b"%PDF-1.7")
        (self.pub / "notes.txt").write_text(CLOSED_LINE)
        (self.pub / "logo.svg").write_text('<svg><image href="data:image/png;base64,AAAA"/></svg>')
        (self.pub / "api" / "extra.json").write_text("{}")
        self.assertEqual(len(self.problems()), 5, self.problems())

    def test_a_pair_file_must_name_two_open_systems(self):
        pair = self.pub / "api" / "versus" / "open" / "closed-123"
        pair.mkdir(parents=True)
        (pair / "pdftotext-rules.json").write_text("{}")
        self.assertTrue(any("pair file" in p for p in self.problems()))

    def test_an_incomplete_export_fails(self):
        (self.pub / "api" / "leaderboard.json").unlink()
        self.assertTrue(any("leaderboard.json is missing" in p for p in self.problems()))

    def test_site_files_other_than_html_js_css_are_not_exported(self):
        stray = SITE / "zz-stray-note.txt"
        stray.write_text(CLOSED_LINE)
        self.addCleanup(stray.unlink)
        out = Path(tempfile.mkdtemp()) / "public"
        self.addCleanup(shutil.rmtree, out.parent)
        with mock.patch("bambench.runner.closed_progress", lambda: None):
            static_site.export(out)
        self.assertFalse((out / stray.name).exists())

    def test_a_document_outside_the_open_track_fails_as_a_value_or_in_a_list(self):
        edit_json(self.pub / "api" / "documents.json", lambda d: d.append({"document_id": "internal-report-7"}))
        self.about(document_id=["bam-b001", "closed-123"])
        found = self.problems()
        self.assertTrue(any("internal-report-7" in p for p in found), found)
        self.assertTrue(any("closed-123" in p for p in found), found)
        self.assertFalse(any("bam-b001" in p for p in found), found)

    def test_page_text_fails(self):
        edit_json(self.pub / "api" / "leaderboard.json",
                  lambda d: d.append({"system": "x", "open": {"page_items": {"bam-b001/1": {"t": 0.9}}}}))
        self.assertTrue(any("page_items" in p for p in self.problems()))

    # Closed results must be exactly what export-closed published.
    PUBLISHED = {"system": "x", "run_id": "r1", "scores": {"overall": 0.8}, "counts": {"pages": 25}, "publishable": True}

    def publish(self, **kw):
        (self.cleared / "x.json").write_text(json.dumps({**self.PUBLISHED, **kw}))

    def row(self, **kw):
        res = {k: v for k, v in {**self.PUBLISHED, "track": "closed", **kw}.items() if v is not None and k != "system"}
        edit_json(self.pub / "api" / "leaderboard.json", lambda d: d.append({"system": "x", "closed": res}))

    def closed_problems(self):
        return [p for p in self.problems() if "closed" in p]

    def test_the_published_closed_result_passes(self):
        self.publish()
        self.row()
        self.assertEqual(self.problems(), [])

    def test_a_closed_result_not_published_fails(self):
        self.row()
        self.assertTrue(self.closed_problems())

    def test_a_closed_result_without_run_or_with_another_run_fails(self):
        self.publish()
        self.row(run_id=None)
        self.assertTrue(self.closed_problems())

    def test_a_closed_result_with_changed_scores_or_pages_fails(self):
        self.publish()
        self.row(scores={"overall": 0.99})
        self.assertTrue(self.closed_problems())
        self.setUp()
        self.publish()
        self.row(counts={"pages": 40})
        self.assertTrue(self.closed_problems())

    def test_a_published_result_on_too_few_pages_still_fails(self):
        self.publish(counts={"pages": 12})
        self.row(counts={"pages": 12})
        self.assertTrue(self.closed_problems())

    def test_closed_results_at_the_root_in_lists_or_under_closed_keys_are_checked(self):
        bad = {"track": "closed", "system": "x", "scores": {"overall": 0.8}, "counts": {"pages": 12}, "publishable": True}
        (self.pub / "api" / "about.json").write_text(json.dumps(bad))
        (self.pub / "api" / "composition.json").write_text(json.dumps([bad]))
        edit_json(self.pub / "api" / "models.json", lambda d: d.update({"closed_score": {"overall": 0.8}}))
        self.assertEqual(len(self.closed_problems()), 3, self.problems())

    def test_closed_agreement_needs_twenty_cleared_pages(self):
        edit_json(self.pub / "api" / "overview.json",
                  lambda d: d.update({"agreement": {"open": None, "closed": {"pages": 8, "overall": 0.9, "publishable": False}}}))
        self.assertTrue(self.closed_problems())
        edit_json(self.pub / "api" / "overview.json",
                  lambda d: d.update({"agreement": {"open": None, "closed": {"pages": 25, "overall": 0.9, "publishable": True}}}))
        self.assertEqual(self.problems(), [])

    def test_odd_json_gives_findings_not_crashes(self):
        (self.cleared / "odd.json").write_text("[]")
        self.row(counts="unknown")
        self.row(counts={"pages": "25"})
        self.assertTrue(self.closed_problems())

    # Closed text, where the closed corpus is on the machine.
    def test_closed_text_is_found_through_json_escaping(self):
        self.about(note=CLOSED_LINE)
        self.assertIn("\\u00fc", (self.pub / "api" / "about.json").read_text())
        with closed_track(text=[CLOSED_LINE]):
            self.assertEqual(len(site_check.check(self.pub)), 1)

    def test_closed_text_is_found_in_another_unicode_form(self):
        self.about(note=CLOSED_LINE.replace("ü", "ü"))
        with closed_track(text=[CLOSED_LINE]):
            self.assertEqual(len(site_check.check(self.pub)), 1)

    def test_closed_text_is_found_inside_longer_text(self):
        self.about(note="Result: " + CLOSED_LINE + " and more words after it.")
        with closed_track(text=[CLOSED_LINE]):
            self.assertTrue(site_check.check(self.pub))
        self.about(note="Befund: " + SHORT_LINE + ", siehe Anlage")
        with closed_track(text=[SHORT_LINE]):
            self.assertTrue(site_check.check(self.pub))

    def test_closed_ids_match_whole_tokens_in_text_and_paths(self):
        self.about(note="Start state, smart parts")
        with closed_track(tokens=[("closed document id", "art")]):
            self.assertEqual(site_check.check(self.pub), [])
        self.about(note="see report KR-2024-17.")
        with closed_track(tokens=[("closed document id", "KR-2024-17")]):
            self.assertTrue(any("closed document id" in p for p in site_check.check(self.pub)))

    def test_text_shared_with_the_open_track_is_not_a_leak(self):
        line = "No text was found on this page of the scanned document at all"
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base)
        for track in ("closed", "open"):
            out = base / track / "sys" / "run1" / "doc"
            out.mkdir(parents=True)
            (out / "page-001.md").write_text(line + "\n" + (CLOSED_LINE if track == "closed" else "") + "\n", encoding="utf-8")
        doc = mock.Mock(document_id="internal-1", sha256="abc", title="")
        with mock.patch("bambench.site_check.load_documents", lambda t: [doc]), \
                mock.patch("bambench.site_check.page_statuses", lambda d: {}), \
                mock.patch("bambench.site_check.run_dir", lambda t: base / t):
            n = site_check._closed_needles()
        self.assertIsNone(n.find([line]))
        self.assertIsNotNone(n.find([CLOSED_LINE]))
        self.assertEqual(n.tokens["internal-1"], "closed document id")

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
      // Edge cases: two systems tie overall, a class without page counts, a class only one system has, an empty key.
      const r2 = (o, k) => ({ scores: { overall: o }, counts: { pages: 9 }, by_kind: { prose: { pages: 9, overall: k }, "": { pages: 9, overall: k }, nopages: { overall: k } }, by_lang: {} });
      const lb2 = [{ system: "a", card: { name: "A" }, open: r2(0.9, 0.8) }, { system: "b", card: { name: "B" }, open: r2(0.9, 0.5) },
                   { system: "c", card: { name: "C" }, open: { ...r2(0.4, 0.8), by_lang: { de: { pages: 9, overall: 0.7 } } } }];
      box.innerHTML = classResults(lb2, "open");
      const edge = {
        heads: [...box.querySelectorAll("table tr:first-child th")].map((th) => th.textContent),
        rows: Object.fromEntries([...box.querySelectorAll("table tr")].slice(1).map((tr) => [tr.querySelector("th").textContent,
          { grey: tr.classList.contains("few"), cells: [...tr.querySelectorAll("td")].map((td) => td.textContent.trim()) }])),
        obs: [...box.querySelectorAll("li")].map((li) => li.textContent),
      };
      // 3. Under the policy, an inline handler injected directly must not run.
      if (underPolicy) box.innerHTML = evil;
      await new Promise((r) => setTimeout(r, 400));
      return { pwned: window.__pwned || null, found, tied, edge };
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

    def test_class_panels_handle_tied_leaders_missing_counts_and_odd_keys(self):
        edge = self.res["sanitizer"]["edge"]
        # Two systems tie overall: no single leader column, and no claim about "the" leader.
        self.assertEqual(edge["heads"], ["Class", "Pages", "Best system", "Best", "Median"], edge)
        self.assertFalse(any("leads overall" in o for o in edge["obs"]), edge)
        # Prose: A and C tie on 0.8, so both are named and the row says tie.
        self.assertIn("A and C", edge["rows"]["Prose"]["cells"][1])
        self.assertIn("tie", edge["rows"]["Prose"]["cells"][1])
        # No page count: shown as unknown and greyed, never as "fewer than 5 pages".
        self.assertEqual(edge["rows"]["Nopages"]["cells"][0], "—")
        self.assertTrue(edge["rows"]["Nopages"]["grey"])
        self.assertTrue(edge["rows"]["German"]["grey"], "only one system has a German score")
        self.assertIn("(no label)", edge["rows"])
        self.assertFalse(any("fewer than 5 pages, so" in o for o in edge["obs"]), edge)


if __name__ == "__main__":
    unittest.main()
