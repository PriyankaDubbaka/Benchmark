"""What may reach a hosted copy of the dashboard: the leak check on the exported folder, and the
page's defences against hostile model output (a script in an output must never run)."""
import json
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

_EXPORT = None


def exported() -> Path:
    """One clean export, copied fresh for each test that plants something in it."""
    global _EXPORT
    if _EXPORT is None:
        base = Path(tempfile.mkdtemp())
        empty = base / "empty"
        with mock.patch("bambench.runner.published_dir", lambda t: empty / t), \
                mock.patch("bambench.runner.summary_dir", lambda t: empty / "none" if t == "closed" else
                           Path(__file__).resolve().parents[1] / "results" / "open" / "summaries"), \
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


class LeakCheck(unittest.TestCase):
    def setUp(self):
        self.pub = exported()
        self.addCleanup(shutil.rmtree, self.pub.parent)

    def test_a_clean_export_passes(self):
        self.assertEqual(site_check.check(self.pub), [])

    def test_a_pdf_or_page_image_fails(self):
        (self.pub / "api" / "page-1.png").write_bytes(b"\x89PNG")
        (self.pub / "report.pdf").write_bytes(b"%PDF-1.7")
        problems = site_check.check(self.pub)
        self.assertEqual(len(problems), 2, problems)

    def test_a_document_outside_the_open_track_fails(self):
        edit_json(self.pub / "api" / "documents.json", lambda d: d.append({"document_id": "internal-report-7"}))
        self.assertTrue(any("internal-report-7" in p for p in site_check.check(self.pub)))

    def test_page_text_fails(self):
        edit_json(self.pub / "api" / "leaderboard.json",
                  lambda d: d.append({"system": "x", "open": {"page_items": {"bam-b001/1": {"t": 0.9}}}}))
        self.assertTrue(any("page_items" in p for p in site_check.check(self.pub)))

    def test_a_closed_score_on_too_few_pages_fails(self):
        row = {"system": "x", "closed": {"scores": {"overall": 0.8}, "counts": {"pages": 12}, "publishable": True}}
        edit_json(self.pub / "api" / "leaderboard.json", lambda d: d.append(row))
        self.assertTrue(any("12 pages" in p for p in site_check.check(self.pub)))

    def test_a_cleared_closed_score_passes(self):
        row = {"system": "x", "closed": {"scores": {"overall": 0.8}, "counts": {"pages": 25}, "publishable": True}}
        edit_json(self.pub / "api" / "leaderboard.json", lambda d: d.append(row))
        self.assertEqual(site_check.check(self.pub), [])

    def test_closed_text_found_anywhere_fails(self):
        line = "Die Prüfung ergab eine Abweichung von 0,42 mm am Flansch der Probe 3"
        (self.pub / "api" / "about.json").write_text(json.dumps({"note": line}, ensure_ascii=False), encoding="utf-8")
        with mock.patch("bambench.site_check._closed_needles", lambda: [("closed label text", line)]):
            self.assertTrue(any("closed label text" in p for p in site_check.check(self.pub)))

    def test_the_command_fails_with_a_nonzero_exit(self):
        import contextlib
        import io
        from bambench.cli import main
        (self.pub / "leak.pdf").write_bytes(b"%PDF")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["check-site", str(self.pub)]), 1)
        self.assertIn("do not publish", out.getvalue())


class PageDefences(unittest.TestCase):
    def test_the_page_limits_where_scripts_images_and_requests_may_go(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="Content-Security-Policy"', html)
        for rule in ("script-src 'self'", "connect-src 'self'", "img-src 'self' data: blob:", "object-src 'none'"):
            self.assertIn(rule, html)


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

BROWSER_SCRIPT = r"""
const { chromium } = require("playwright");
(async () => {
  const [url, payloads] = [process.argv[2], JSON.parse(process.argv[3])];
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url);
  await page.waitForFunction(() => typeof renderMarkdown === "function");
  const out = await page.evaluate(async (payloads) => {
    const box = document.createElement("div");
    document.body.appendChild(box);
    const found = [];
    for (const p of payloads) {
      box.innerHTML = renderMarkdown(p);
      box.querySelectorAll("*").forEach((el) => {
        if (["SCRIPT", "IMG", "IFRAME", "SVG", "svg", "MATH", "math", "STYLE", "A", "DETAILS"].includes(el.tagName)) found.push(el.tagName);
        for (const a of el.attributes) if (!["colspan", "rowspan", "class"].includes(a.name)) found.push(a.name);
      });
      box.querySelectorAll("td, th, details").forEach((el) => el.dispatchEvent(new MouseEvent("mouseover")));
    }
    await new Promise((r) => setTimeout(r, 300));
    return { pwned: window.__pwned || null, found };
  }, payloads);
  console.log(JSON.stringify(out));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(2); });
"""


def _node_with_playwright() -> bool:
    try:
        return subprocess.run(["node", "-e", "require('playwright')"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@unittest.skipUnless(_node_with_playwright(), "needs node with Playwright and Chromium")
class HostileModelOutput(unittest.TestCase):
    """A model output is shown on the local dashboard next to closed pages. If a script in it ran, it
    could read those pages through the local API, so nothing in an output may become live markup."""

    def test_no_payload_runs_or_survives_as_markup(self):
        from bambench.server import Handler
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        srv.local_only = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / "probe.js"
            script.write_text(BROWSER_SCRIPT, encoding="utf-8")
            r = subprocess.run(["node", str(script), f"http://127.0.0.1:{srv.server_port}/#/about", json.dumps(HOSTILE)],
                               capture_output=True, text=True, timeout=120, cwd=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertIsNone(res["pwned"], res)
        self.assertEqual(res["found"], [], res)


if __name__ == "__main__":
    unittest.main()
