"""Browser checks for GHW analytics; all requests are fulfilled locally.

Install Python Playwright and Chromium (at /usr/bin/chromium, or set CHROMIUM_PATH), then run:
    python -B -m unittest discover -s tests -p test_tracking.py -v
The shared website scripts are read from the sibling RodrigoSanJose.github.io
checkout, or from PERSONAL_SITE_ROOT. Nothing is sent to production analytics.
"""

from datetime import datetime, timezone
from html.parser import HTMLParser
import http.server
import json
import mimetypes
import os
from pathlib import Path
import unittest
import threading
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PERSONAL_SITE = Path(os.environ.get(
    "PERSONAL_SITE_ROOT", str(ROOT.parent / "RodrigoSanJose.github.io")))
ORIGIN = "https://ghw-tracking.test"
PAGE = ORIGIN + "/ghw-tables/"
UMAMI_ID = "6c3573da-71d0-4f6e-9d45-f848a93e9aa7"
INITIAL_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
INIT = """
try { localStorage.setItem('umami.disabled', '1'); } catch (error) {}
window.__testVisibility = 'visible';
Object.defineProperty(document, 'visibilityState', {
    configurable: true, get: () => window.__testVisibility
});
"""
MOCK = """
window.__analyticsEvents = [];
window.umami = {track(name, data) {
    const payload = typeof name === 'function'
        ? name({url: location.pathname + location.search}) : {name, data};
    const event = {name: payload.name, data: payload.data};
    if ('url' in payload) event.url = payload.url;
    window.__analyticsEvents.push(event);
    return Promise.resolve();
}};
"""
MATHJAX = """
MathJax.startup.promise = Promise.resolve();
MathJax.typesetPromise = () => Promise.resolve();
if (window.mjShow) mjShow();
"""


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.has_body = False
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.has_body = True
        if tag == "script":
            self.scripts.append(dict(attrs))


class TrackingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ("link-tracking.js", "page-visibility.js"):
            if not (PERSONAL_SITE / "assets/js" / name).is_file():
                raise RuntimeError(
                    "Check out the personal website beside ghw-tables, or set "
                    "PERSONAL_SITE_ROOT to its checkout, for shared tracking tests.")
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium"),
            args=["--no-sandbox"],
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1400, "height": 1000})
        # Opt out before every document, including popups; the isolated mock above
        # deliberately records calls locally despite that flag.
        self.context.add_init_script(INIT)
        self.requests = []
        self.context.route("**/*", self.route)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.goto(PAGE, wait_until="load")
        self.page.wait_for_selector("#entry-1-1", state="attached")

    def tearDown(self):
        self.context.close()

    def route(self, route):
        request = route.request
        self.requests.append(request.url)
        parsed = urlsplit(request.url)
        if parsed.netloc == "cloud.umami.is" and parsed.path == "/script.js":
            route.fulfill(content_type="application/javascript", body=MOCK)
            return
        if "mathjax" in request.url.lower():
            route.fulfill(content_type="application/javascript", body=MATHJAX)
            return
        path = unquote(parsed.path)
        local = None
        if parsed.netloc == urlsplit(ORIGIN).netloc:
            if path.startswith("/ghw-tables/"):
                local = DOCS / (path[len("/ghw-tables/"):] or "index.html")
            elif path.startswith(("/assets/", "/images/")):
                local = PERSONAL_SITE / path.lstrip("/")
        if local and local.resolve().is_relative_to(
                DOCS.resolve() if path.startswith("/ghw-tables/") else PERSONAL_SITE.resolve()
        ) and local.is_file():
            route.fulfill(body=local.read_bytes(), content_type=(
                mimetypes.guess_type(str(local))[0] or "application/octet-stream"))
        elif request.resource_type == "document":
            route.fulfill(content_type="text/html", body="<!doctype html><title>Local destination</title>")
        elif request.resource_type == "script":
            route.fulfill(content_type="application/javascript", body="")
        else:
            route.fulfill(content_type="text/plain", body="")

    def events(self):
        return self.page.evaluate("window.__analyticsEvents.filter(e => !e.name.startsWith('Page visible. '))")

    def reset_events(self):
        self.page.evaluate("window.__analyticsEvents.length = 0")

    def assert_event(self, name, label, url, section, **context):
        events = self.events()
        self.assertEqual(len(events), 1, events)
        event = events[0]
        self.assertEqual(event["name"], name)
        self.assertLessEqual(len(event["name"]), 50)
        self.assertEqual(event["data"], {
            "label": label, "url": url, "section": section, **context,
        })
        for key in ("q", "m", "d", "r"):
            if key in event["data"]:
                self.assertIs(type(event["data"][key]), int)

    def table_action(self, action, q=3, m=3, d=None, r=None):
        values = {"q": q, "m": m}
        if d is not None:
            values["d"] = d
        if r is not None:
            values["r"] = r
        return action + ". " + ", ".join(f"{key}={value}" for key, value in values.items())

    def stop_navigation(self):
        self.page.evaluate("""() => document.addEventListener('click', event => {
            if (event.target.closest('a[href]')) event.preventDefault();
        }, true)""")

    def test_every_content_page_keeps_single_shared_tracker_and_existing_installation(self):
        found = 0
        for file in DOCS.rglob("*.html"):
            parser = ScriptParser()
            parser.feed(file.read_text(encoding="utf-8"))
            if not parser.has_body:
                continue
            found += 1
            with self.subTest(page=str(file.relative_to(DOCS))):
                sources = [script.get("src") for script in parser.scripts]
                self.assertEqual(sources.count("/assets/js/link-tracking.js"), 1)
                self.assertEqual(sources.count("/assets/js/page-visibility.js"), 1)
                umami = [script for script in parser.scripts
                         if script.get("src") == "https://cloud.umami.is/script.js"]
                self.assertEqual(len(umami), 1)
                self.assertEqual(umami[0].get("data-website-id"), UMAMI_ID)
                self.assertEqual(umami[0].get("data-domains"), "rodrigosanjose.github.io")
        self.assertGreater(found, 0)
        self.assertEqual(self.page.evaluate("localStorage.getItem('umami.disabled')"), "1")
        self.assertFalse(self.context.cookies())

    def test_choices_redraw_tables_with_target_parameters_and_stable_names(self):
        q_choice = self.page.locator('#ghw-q-choices a[href="#q=2&m=3"]')
        q_choice.click()
        self.page.wait_for_selector('#ghw-q-choices a.ghw-current[href="#q=2&m=3"]')
        self.assert_event("GHW. Select field size", self.table_action("GHW. Select field size", 2, 3),
                          PAGE + "#q=2&m=3", "GHW tables / Controls", q=2, m=3)
        self.reset_events()
        self.page.locator('#ghw-m-choices a[href="#q=2&m=2"]').click()
        self.page.wait_for_selector('#ghw-m-choices a.ghw-current[href="#q=2&m=2"]')
        self.assert_event("GHW. Select dimension", self.table_action("GHW. Select dimension", 2, 2),
                          PAGE + "#q=2&m=2", "GHW tables / Controls", q=2, m=2)
        self.assertIn("q=2&m=2", self.page.url)
        self.assertTrue(self.page.locator("#entry-1-1").is_visible())

    def test_nested_cell_opens_explanation_and_close_preserves_native_hash(self):
        # A MathJax-like descendant must resolve to its owning control.
        self.page.locator("#entry-1-1").evaluate("e => e.innerHTML = '<span class=math><i>27</i></span>'")
        self.page.locator("#entry-1-1 i").click()
        self.page.wait_for_selector("#ghw-explanation:not([hidden])")
        self.assert_event("GHW. Open explanation", self.table_action("GHW. Open explanation", d=1, r=1),
                          PAGE + "#q=3&m=3&d=1&r=1", "GHW tables / Codes", q=3, m=3, d=1, r=1)
        self.assertIn("ghw-selected", self.page.locator("#entry-1-1").get_attribute("class"))
        self.reset_events()
        self.page.locator(".ghw-permalink a").click()
        self.assert_event("GHW. Entry permalink", self.table_action("GHW. Entry permalink", d=1, r=1),
                          PAGE + "#q=3&m=3&d=1&r=1", "GHW tables / Explanation", q=3, m=3, d=1, r=1)
        self.reset_events()
        self.page.locator(".ghw-close").click()
        self.page.wait_for_selector("#ghw-explanation[hidden]", state="attached")
        self.assert_event("GHW. Close explanation", self.table_action("GHW. Close explanation", d=1, r=1),
                          PAGE + "#q=3&m=3", "GHW tables / Explanation", q=3, m=3, d=1, r=1)
        self.assertEqual(self.page.url, PAGE + "#q=3&m=3")

    def test_toggle_mouse_enter_and_space_each_emit_once_and_redraw(self):
        for method, action, expanded in (("click", "Hide", False), ("Enter", "Show", True),
                                         ("Space", "Hide", False), ("Space", "Show", True)):
            with self.subTest(method=method, action=action):
                self.reset_events()
                control = self.page.locator("#code-1 .ghw-toggle")
                if method == "click":
                    control.click()
                else:
                    control.focus()
                    control.press(method)
                self.assert_event("GHW. " + action + " weights",
                                  self.table_action("GHW. " + action + " weights", d=1),
                                  PAGE + "#", "GHW tables / Codes", q=3, m=3, d=1)
                self.assertEqual(self.page.locator("#entry-1-1").count(), int(expanded))
                self.assertTrue(self.page.locator("#code-1 .ghw-toggle").evaluate("e => e === document.activeElement"))

    def test_references_and_icon_only_links_have_meaningful_names(self):
        self.stop_navigation()
        self.page.locator("#header a.fa-google-scholar").evaluate("e => e.innerHTML = '<span><i></i></span>'")
        self.page.locator("#header a.fa-google-scholar i").dispatch_event("click", {"button": 0})
        self.assert_event("Google Scholar", "Google Scholar",
                          "https://scholar.google.com/citations?user=F5GiN1MAAAAJ", "Header")
        self.reset_events()
        reference = self.page.locator('#ghw-references a[href="https://doi.org/10.48550/arXiv.2611.08203"]')
        reference.dispatch_event("click", {"button": 0})
        event = self.events()[0]
        self.assertEqual(len(self.events()), 1)
        self.assertIn("Common zeros", event["data"]["label"])
        self.assertTrue(event["name"].endswith(". Arxiv"))
        self.assertEqual(event["data"]["url"], "https://doi.org/10.48550/arXiv.2611.08203")
        self.assertLessEqual(len(event["name"]), 50)

    def test_generated_explanation_links_have_destination_context(self):
        # This real degree has both a code reference (duality) and recursive
        # weight references across its entries. No fabricated table fixture.
        seen = set()
        for degree, rank in ((5, 2), (4, 7), (3, 6), (4, 2)):
            self.page.evaluate("hash => { location.hash = hash; }", f"#q=3&m=3&d={degree}&r={rank}")
            self.page.wait_for_function("args => document.querySelector('.ghw-selected')?.id === args", arg=f"entry-{degree}-{rank}")
            self.stop_navigation()
            for link in self.page.locator('#ghw-explanation a[data-analytics-name="GHW. Referenced code"], '
                                          '#ghw-explanation a[data-analytics-name="GHW. Referenced weight"]').all():
                self.reset_events()
                href = link.get_attribute("href")
                link.dispatch_event("click", {"button": 0})
                event = self.events()[0]
                self.assertEqual(len(self.events()), 1)
                seen.add(event["name"])
                values = dict(item.split("=") for item in href.lstrip("#").split("&"))
                target_context = {key: int(value) for key, value in values.items()}
                self.assert_event(event["name"], self.table_action(event["name"], **target_context),
                                  PAGE + href, "GHW tables / Explanation", **target_context)
        self.assertEqual(seen, {"GHW. Referenced code", "GHW. Referenced weight"})

    def test_citation_copy_matches_the_displayed_entry_and_is_tracked(self):
        displayed = self.page.locator("#ghw-bibtex code").text_content()
        self.assertTrue(displayed.startswith("@misc{sanjoseGHWTables,"))
        self.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=ORIGIN)
        section = "GHW tables / Citation"
        for method in ("click", "Enter", "Space"):
            with self.subTest(method=method):
                self.page.evaluate("navigator.clipboard.writeText('')")
                self.reset_events()
                button = self.page.locator("#ghw-copy-bibtex")
                if method == "click":
                    button.locator("i").click()          # the icon inside the button
                else:
                    button.focus()
                    button.press(method)
                self.page.wait_for_function("document.getElementById('ghw-copy-status').textContent === 'Copied.'")
                self.assertEqual(self.page.evaluate("navigator.clipboard.readText()"), displayed)
                self.assert_event("GHW tables. Copy BibTeX", "GHW tables. Copy BibTeX", PAGE, section)
        self.assertEqual(self.page.locator('a[download], a[href$=".bib"]').count(), 0)
        self.reset_events()
        self.stop_navigation()
        self.page.locator('#ghw-citation a[href="https://doi.org/10.5281/zenodo.24020768"]').dispatch_event(
            "click", {"button": 0})
        self.assert_event("GHW tables. Zenodo archive",
                          "Tables of generalized Hamming weights of projective Reed-Muller codes. Zenodo archive",
                          "https://doi.org/10.5281/zenodo.24020768", section)
        self.assertEqual(self.errors, [])

    def test_site_navigation_links_have_one_event_and_the_current_page_is_not_a_link(self):
        self.stop_navigation()
        nav = self.page.locator("#header nav.site-nav")
        self.assertEqual(nav.locator('[aria-current="page"]').text_content(), "GHW tables")
        self.assertEqual(nav.locator('a[href="/ghw-tables/"]').count(), 0)
        for href, name in (("/", "Home"), ("/books.html", "Tier lists")):
            with self.subTest(link=name):
                self.reset_events()
                nav.locator(f'a[href="{href}"]').dispatch_event("click", {"button": 0})
                self.assert_event(name, name, ORIGIN + href, "Navigation")
        self.assertEqual(self.page.locator("#header .avatar[href], #header h1 a").count(), 0)

    def test_math_stays_hidden_until_typeset_after_changing_the_table(self):
        """When the page loads, its math is hidden until MathJax has typeset it.  The math drawn later
        (another table, an explanation) must stay hidden too, so that its TeX source never shows."""
        self.page.evaluate("""() => {     // a MathJax that finishes only when the test releases it
            window.__gate = new Promise(resolve => { window.__release = resolve; });
            MathJax.typesetPromise = () => window.__gate;
        }""")
        visibility = "elements => elements.map(element => getComputedStyle(element).visibility)"
        self.page.locator('#ghw-q-choices a[href="#q=2&m=3"]').click()
        self.page.wait_for_selector('#ghw-q-choices a.ghw-current[href="#q=2&m=3"]')
        self.page.locator("#entry-1-1").click()
        self.page.wait_for_selector("#ghw-explanation:not([hidden])")
        for selector in ("#ghw-summary .math", "#ghw-codes .math", "#ghw-explanation .math"):
            with self.subTest(selector=selector, released=False):
                values = self.page.locator(selector).evaluate_all(visibility)
                self.assertTrue(values)
                self.assertEqual(set(values), {"hidden"})
        self.page.evaluate("window.__release()")
        self.page.wait_for_function("!document.querySelector('.mj-pending')")
        for selector in ("#ghw-summary .math", "#ghw-codes .math", "#ghw-explanation .math"):
            with self.subTest(selector=selector, released=True):
                self.assertEqual(set(self.page.locator(selector).evaluate_all(visibility)), {"visible"})
        self.assertEqual(self.errors, [])

    def test_show_all_and_hide_all_redraw_every_code_and_emit_one_event_each(self):
        self.page.evaluate("location.hash = '#q=2&m=7'")
        self.page.wait_for_selector('#ghw-q-choices a.ghw-current[href="#q=2&m=7"]')
        codes = self.page.evaluate("shown.data.codes.length")
        weights = self.page.evaluate("shown.data.codes.reduce((total, code) => total + code.k, 0)")
        self.assertGreater(self.page.locator('#ghw-codes .ghw-toggle:text-is("Show")').count(), 0)
        for method, show in (("click", True), ("Enter", False), ("Space", True)):
            with self.subTest(method=method, show=show):
                self.reset_events()
                button = self.page.locator(f'#ghw-summary .ghw-all-toggle[data-show="{str(show).lower()}"]')
                if method == "click":
                    button.click()
                else:
                    button.focus()
                    button.press(method)
                action = "GHW. Show all weights" if show else "GHW. Hide all weights"
                self.assert_event(action, self.table_action(action, 2, 7), PAGE + "#q=2&m=7",
                                  "GHW tables / Controls", q=2, m=7)
                self.assertEqual(self.page.locator('#ghw-codes [id^="entry-"]').count(), weights if show else 0)
                toggle = "Hide" if show else "Show"           # every code now offers the opposite action
                self.assertEqual(self.page.locator(f'#ghw-codes .ghw-toggle:text-is("{toggle}")').count(), codes)
        self.assertEqual(self.errors, [])

    def test_all_current_links_and_new_large_table_cells_are_covered(self):
        results = self.page.evaluate(r"""() => {
            const selector = 'a[href], area[href], button, input[type="button"], ' +
                'input[type="submit"], input[type="reset"], [role="button"]';
            // Prevent native navigation/submission only in this coverage sweep.
            document.addEventListener('click', event => {
                if (event.target.closest(selector)) event.preventDefault();
            }, true);
            return [...document.querySelectorAll(selector)].filter(control =>
                !control.closest('[data-analytics-ignore], [inert], [aria-disabled="true"]') &&
                !control.matches(':disabled, [disabled]')
            ).map(control => {
                const labelledBy = (control.getAttribute('aria-labelledby') || '').split(/\s+/)
                    .map(id => document.getElementById(id)?.textContent || '').join(' ');
                // Input values can contain visitor information. An action needs
                // declared metadata or an accessible name independent of value.
                const actionLabel = [control.dataset.analyticsLabel, control.dataset.analyticsName,
                    control.getAttribute('data-umami-event'), control.getAttribute('aria-label'),
                    labelledBy, control.getAttribute('title'), control.textContent,
                    control.querySelector('img[alt]')?.getAttribute('alt')]
                    .find(value => value && value.trim());
                const href = control.matches('a[href], area[href]') ? control.href : location.href;
                const keyboardCovered = control.matches('.ghw-toggle, .ghw-all-toggle');
                const nativeUmami = Boolean(control.closest('[data-umami-event]'));
                const before = __analyticsEvents.length;
                // Show/Hide replaces its entire block, and Show all/Hide all every block;
                // exercise those separately with real mouse/Enter/Space activations.
                if (!keyboardCovered) control.dispatchEvent(new MouseEvent('click', {
                    bubbles: true, cancelable: true, button: 0
                }));
                const emitted = __analyticsEvents.slice(before).filter(e => !e.name.startsWith('Page visible. '));
                return {id: control.id, href, actionLabel, keyboardCovered, nativeUmami, emitted};
            });
        }""")
        self.assertGreater(len(results), 150)
        self.assertTrue(any(result["id"] == "dark-mode-toggle" for result in results))
        for result in results:
            with self.subTest(control=result["id"], url=result["href"]):
                self.assertTrue(result.get("actionLabel"), "Give each control meaningful analytics or accessible action text")
                if result["keyboardCovered"]:
                    continue
                if result["nativeUmami"]:
                    self.assertEqual(result["emitted"], [], "Native Umami events must not also emit shared events")
                    continue
                self.assertEqual(len(result["emitted"]), 1, result)
                event = result["emitted"][0]
                self.assertTrue(event["name"])
                self.assertLessEqual(len(event["name"]), 50)
                self.assertTrue(event["data"]["label"])
                self.assertEqual(event["data"]["url"], result["href"])
                self.assertTrue(event["data"]["section"])
        # A larger real table starts partly collapsed; newly rendered cells
        # need the same delegated tracking after an expansion/redraw.
        self.page.evaluate("location.hash = '#q=2&m=7'")
        self.page.wait_for_selector('#ghw-q-choices a.ghw-current[href="#q=2&m=7"]')
        toggle = self.page.locator('.ghw-toggle[data-analytics-name="GHW. Show weights"]').first
        degree = int(toggle.get_attribute("data-degree"))
        toggle.click()
        cell = self.page.locator(f"#entry-{degree}-1")
        self.reset_events()
        cell.dispatch_event("click", {"button": 0})
        self.assert_event("GHW. Open explanation", self.table_action("GHW. Open explanation", 2, 7, degree, 1),
                          PAGE + f"#q=2&m=7&d={degree}&r=1", "GHW tables / Codes", q=2, m=7, d=degree, r=1)

    def test_future_controls_and_links_are_automatic_and_do_not_collect_form_values(self):
        self.page.evaluate("""() => {
            const host = document.createElement('section');
            host.id = 'future-controls';
            host.dataset.analyticsSection = 'GHW tables / Future';
            host.dataset.analyticsQ = '3'; host.dataset.analyticsM = '3';
            host.dataset.analyticsD = '2'; host.dataset.analyticsR = '4';
            host.innerHTML = '<input value="PRIVATE FORM CONTENT" name="secret">' +
                '<button type=button id=future-button aria-label="GHW. Export selected table"><span>Export</span></button>' +
                '<a id=future-link href="/future-document.pdf" download><img alt="Future notes PDF"></a>';
            document.querySelector('#tables').append(host);
            document.querySelector('#future-button').addEventListener('click', () => window.__buttonActions = (window.__buttonActions || 0) + 1);
        }""")
        for method in ("click", "Enter", "Space"):
            self.reset_events()
            target = self.page.locator("#future-button")
            if method == "click":
                target.locator("span").click()
            else:
                target.press(method)
            self.assert_event("GHW. Export selected table", "GHW. Export selected table", PAGE,
                              "GHW tables / Future", q=3, m=3, d=2, r=4)
        self.assertEqual(self.page.evaluate("window.__buttonActions"), 3)
        self.reset_events()
        with self.page.expect_download() as download_info:
            self.page.locator("#future-link img").click()
        self.assertEqual(download_info.value.suggested_filename, "future-document.pdf")
        self.assertEqual(self.page.url, PAGE)
        self.assert_event("Future notes PDF", "Future notes PDF", ORIGIN + "/future-document.pdf",
                          "GHW tables / Future", q=3, m=3, d=2, r=4)
        self.assertNotIn("PRIVATE", json.dumps(self.events()))

    def test_modifier_and_middle_links_keep_browser_behavior(self):
        # Chromium can start a modifier-created tab before Playwright attaches
        # interception to it. A loopback-only destination makes that first
        # request harmless even on Chromium versions with that behavior.
        class Destination(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<!doctype html><title>Local destination</title>")

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Destination)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        destination = f"http://127.0.0.1:{server.server_port}/destination"
        try:
            self.page.evaluate("""url => {
                const link = document.createElement('a');
                link.id = 'native-link'; link.href = url;
                link.textContent = 'GHW. Verification destination';
                link.dataset.analyticsSection = 'GHW tables / Verification';
                document.querySelector('#tables').append(link);
            }""", destination)
            control = self.page.locator("#native-link")
            for method in ("Control", "middle"):
                self.reset_events()
                with self.context.expect_page() as popup_info:
                    if method == "middle":
                        control.click(button="middle")
                    else:
                        control.click(modifiers=[method])
                popup = popup_info.value
                popup.wait_for_load_state()
                self.assertEqual(popup.url, destination)
                popup.close()
                self.assert_event("GHW. Verification destination", "GHW. Verification destination",
                                  destination, "GHW tables / Verification")
                self.assertEqual(self.page.url, PAGE)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_missing_throwing_rejected_tracker_and_reinjection_are_harmless(self):
        for expression in ("delete window.umami", "window.umami = {track() {throw new Error('blocked')}}",
                           "window.umami = {track() {return Promise.reject(new Error('blocked'))}}"):
            self.page.evaluate(expression)
            self.page.locator("#entry-1-1").click()
            self.page.wait_for_selector("#ghw-explanation:not([hidden])")
            self.assertEqual(self.page.url, PAGE + "#q=3&m=3&d=1&r=1")
            self.page.locator(".ghw-close").click()
        self.page.evaluate(MOCK)
        self.page.add_script_tag(path=str(PERSONAL_SITE / "assets/js/link-tracking.js"))
        self.page.add_script_tag(path=str(PERSONAL_SITE / "assets/js/link-tracking.js"))
        self.page.locator("#entry-1-1").click()
        self.assert_event("GHW. Open explanation", self.table_action("GHW. Open explanation", d=1, r=1),
                          PAGE + "#q=3&m=3&d=1&r=1", "GHW tables / Codes", q=3, m=3, d=1, r=1)
        self.assertEqual(self.errors, [])

    def test_missing_entries_close_the_explanation_and_values_stay_accessible_names(self):
        """An address with an entry that does not exist (r=x, r=1.5, r=99) closes the explanation without
        errors.  The analytics label does not replace the accessible name of a cell (its value) or of a
        permalink; only the controls whose text needs context (×, Show/Hide, the choices) use it."""
        for address in ("#q=3&m=3&d=4&r=x", "#q=3&m=3&d=4&r=1.5", "#q=3&m=3&d=4&r=99"):
            with self.subTest(address=address):
                self.page.evaluate("location.hash = '#q=3&m=3&d=4&r=7'")
                self.page.wait_for_selector("#ghw-explanation:not([hidden])")
                self.page.evaluate("address => { location.hash = address; }", address)
                self.page.wait_for_selector("#ghw-explanation[hidden]", state="attached")
        self.assertEqual(self.errors, [])
        self.page.evaluate("location.hash = '#q=3&m=3&d=4&r=7'")
        self.page.wait_for_selector("#ghw-explanation:not([hidden])")
        self.assertEqual(self.page.locator("#entry-4-7").aria_snapshot().splitlines()[0], '- link "16":')
        self.assertEqual(self.page.locator(".ghw-cell[aria-label], .ghw-permalink a[aria-label]").count(), 0)
        self.assertEqual(self.page.locator(".ghw-close").get_attribute("aria-label"),
                         self.table_action("GHW. Close explanation", d=4, r=7))
        self.assertEqual(self.page.locator("#code-4 .ghw-toggle").get_attribute("aria-label"),
                         self.table_action("GHW. Hide weights", d=4))

    def test_tables_that_cannot_be_downloaded_give_a_message(self):
        """A table that cannot be downloaded gives a message, without errors: in the notice when another
        table is shown (the choice is still tracked once), and instead of "Loading the tables…" when it is
        the first table of the visit (there are no choices yet)."""
        self.page.route("**/ghw-tables/data/q4_m3.json", lambda route: route.abort())
        self.page.locator('#ghw-q-choices a[href="#q=4&m=3"]').click()
        self.page.wait_for_selector("#ghw-notice:not([hidden])")
        notice = self.page.locator("#ghw-notice").text_content()
        self.assertIn("q = 4 and m = 3 could not be loaded", notice)
        self.assertIn("q = 3 and m = 3 is still shown", notice)
        self.assertEqual(self.page.evaluate("[shown.q, shown.m]"), [3, 3])
        self.assert_event("GHW. Select field size", self.table_action("GHW. Select field size", 4, 3),
                          PAGE + "#q=4&m=3", "GHW tables / Controls", q=4, m=3)
        page = self.context.new_page()
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        page.route("**/ghw-tables/data/q3_m3.json", lambda route: route.abort())
        page.goto(PAGE, wait_until="load")
        page.wait_for_function("document.getElementById('ghw-loading').textContent.includes('could not be loaded')")
        self.assertIn("Please reload the page", page.locator("#ghw-loading").text_content())
        # A missing table, whose replacement cannot be loaded either: only the failure is reported.
        page.goto(PAGE + "#q=99&m=1", wait_until="load")
        page.wait_for_function("document.getElementById('ghw-loading').textContent.includes('could not be loaded')")
        self.assertTrue(page.locator("#ghw-notice").is_hidden())
        page.close()
        self.assertEqual(self.errors, [])

    def test_scrolls_of_an_older_address_are_dropped(self):
        """A scroll to a code waits until MathJax has typeset the table. If the visitor has moved on by then,
        it must neither fail (the new table has no such code) nor scroll the new table (it has one)."""
        for newer in ("#q=2&m=1", "#q=3&m=3"):                    # without, and with, a code d = 7
            with self.subTest(newer=newer):
                self.page.evaluate("""() => {     // a MathJax that finishes only when the test releases it
                    window.__gate = new Promise(resolve => { window.__release = resolve; });
                    MathJax.typesetPromise = () => window.__gate;
                }""")
                self.page.evaluate("location.hash = '#q=4&m=3&d=7'")
                self.page.wait_for_selector('#ghw-q-choices a.ghw-current[href="#q=4&m=3"]')
                self.page.evaluate("address => { location.hash = address; }", newer)
                self.page.wait_for_selector(f'#ghw-m-choices a.ghw-current[href="{newer}"]')
                self.page.evaluate("window.__release()")
                self.page.wait_for_function("!document.querySelector('.mj-pending')")
                self.page.wait_for_timeout(800)                   # a smooth scroll would have moved by now
                self.assertEqual(self.page.evaluate("scrollY"), 0)
        self.assertEqual(self.errors, [])

    def test_blocked_site_data_keeps_the_dark_mode_toggle_working(self):
        """When the visitor blocks site data, localStorage throws: the page still starts in dark mode, and
        the toggle still switches the theme, its icon and its pressed state (only for this page)."""
        context = self.browser.new_context(viewport={"width": 1400, "height": 1000})
        # The opt-out comes first, in the same script: separate init scripts have no guaranteed order.
        context.add_init_script(INIT + """
Object.defineProperty(window, 'localStorage', {configurable: true, get() {
    throw new DOMException('Access is denied for this document.', 'SecurityError');
}});
""")
        context.route("**/*", self.route)
        try:
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(PAGE, wait_until="load")
            page.wait_for_selector("#entry-1-1", state="attached")
            toggle = page.locator("#dark-mode-toggle")
            self.assertTrue(page.evaluate("document.documentElement.classList.contains('dark-mode')"))
            self.assertEqual(toggle.get_attribute("aria-pressed"), "true")
            toggle.click()
            self.assertFalse(page.evaluate("document.documentElement.classList.contains('dark-mode')"))
            self.assertEqual(toggle.get_attribute("aria-pressed"), "false")
            self.assertEqual(toggle.locator("i").get_attribute("class"), "fas fa-moon")
            events = page.evaluate("window.__analyticsEvents.filter(e => !e.name.startsWith('Page visible. '))")
            self.assertEqual([event["name"] for event in events], ["Toggle dark mode"])
            self.assertEqual(errors, [])
        finally:
            context.close()

    def test_language_states_and_live_regions_for_assistive_technology(self):
        """The page declares its language and exposes the current choices, the state of the Show/Hide and
        dark-mode toggles, and live regions for its messages. An address naming an entry of a table that
        does not exist selects nothing, also after a redraw."""
        self.assertEqual(self.page.evaluate("document.documentElement.lang"), "en")
        for group in ("#ghw-q-choices", "#ghw-m-choices"):
            current = self.page.locator(group + ' a[aria-current="true"]')
            self.assertEqual(current.count(), 1)
            self.assertIn("ghw-current", current.get_attribute("class"))
        self.assertEqual(self.page.locator(".ghw-choice[aria-current]:not(.ghw-current)").count(), 0)
        toggle = self.page.locator("#code-1 .ghw-toggle")
        self.assertEqual((toggle.get_attribute("aria-expanded"), toggle.get_attribute("aria-controls")),
                         ("true", "weights-1"))
        self.assertEqual(self.page.locator("#weights-1 #entry-1-1").count(), 1)
        toggle.click()
        self.assertEqual(self.page.locator("#code-1 .ghw-toggle").get_attribute("aria-expanded"), "false")
        self.assertEqual(self.page.locator("#weights-1").count(), 1)
        self.assertEqual(self.page.locator("#dark-mode-toggle").get_attribute("aria-pressed"), "true")
        self.assertEqual(self.page.locator("#ghw-notice").evaluate("e => e.parentElement.getAttribute('role')"),
                         "status")
        self.assertEqual(self.page.locator("#ghw-loading").count(), 0)    # replaced by the table
        self.assertIn('<p id="ghw-loading" role="status">', (DOCS / "index.html").read_text(encoding="utf-8"))
        self.page.evaluate("location.hash = '#q=99&m=1&d=4&r=7'")
        self.page.wait_for_selector("#ghw-notice:not([hidden])")
        self.page.locator('.ghw-all-toggle[data-show="true"]').click()
        self.assertEqual(self.page.locator(".ghw-selected").count(), 0)
        self.assertEqual(self.errors, [])

    def test_shared_visible_timer_pauses_resumes_keeps_hash_visit_and_handles_back_forward(self):
        self.page.clock.install(time=INITIAL_TIME)
        self.page.clock.pause_at(INITIAL_TIME)
        # Reload starts a genuine fresh visit with the controlled performance clock.
        self.page.reload(wait_until="load")
        self.page.wait_for_selector("#entry-1-1", state="attached")
        self.page.clock.run_for(20_000)
        self.page.evaluate("""() => {
            __testVisibility = 'hidden'; document.dispatchEvent(new Event('visibilitychange'));
        }""")
        self.page.clock.run_for(900_000)
        self.assertEqual(self.page.evaluate("__analyticsEvents"), [])
        self.page.evaluate("""() => {
            __testVisibility = 'visible'; document.dispatchEvent(new Event('visibilitychange'));
            location.hash = '#q=3&m=3&d=1&r=1';
        }""")
        self.page.add_script_tag(path=str(PERSONAL_SITE / "assets/js/page-visibility.js"))
        self.page.clock.run_for(10_000)
        events = self.page.evaluate("__analyticsEvents")
        self.assertEqual(events, [{"name": "Page visible. 30s", "data": {
            "visible_seconds": 30, "page": PAGE}, "url": "/ghw-tables/"}])
        self.page.clock.fast_forward(95_000)
        self.assertEqual([event["name"] for event in self.page.evaluate("__analyticsEvents")],
                         ["Page visible. 30s", "Page visible. 60s", "Page visible. 120s"])
        self.page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide', {persisted: true}))")
        self.page.clock.run_for(1_000_000)
        self.assertEqual(len(self.page.evaluate("__analyticsEvents")), 3)
        self.page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
        self.page.clock.run_for(29_000)
        self.assertEqual(len(self.page.evaluate("__analyticsEvents")), 3)
        self.page.clock.run_for(1_000)
        self.assertEqual(self.page.evaluate("__analyticsEvents.at(-1)"), {
            "name": "Page visible. 30s", "data": {"visible_seconds": 30, "page": PAGE}, "url": "/ghw-tables/"})
        self.assertEqual(self.errors, [])


if __name__ == "__main__":
    unittest.main()
