# Analytics maintenance

These instructions apply to Codex and Claude Code working in this repository.
Every website content update includes analytics for all new or changed links,
buttons, table controls, quotes, references, downloads, icons/images, and
dynamically generated content; the user need not request tracking separately.

- Reuse the central delegated handler. Every content page must load exactly one
  each of `/assets/js/link-tracking.js`, `/assets/js/page-visibility.js`, and the
  existing Umami Cloud loader with website ID
  `6c3573da-71d0-4f6e-9d45-f848a93e9aa7`. The two shared scripts are maintained in
  the personal website repository; do not copy their source into this repository.
  Preserve `data-domains="rodrigosanjose.github.io"` and existing exclusions,
  opt-out behavior, and duplicate guards.
- Use native buttons for actions and anchors for navigation. Give new controls
  descriptive visible text or accessible labels and use the existing rendering
  helpers to attach analytics metadata. Handle keyboard activation through the
  same semantic action as pointer activation. Do not add separate tracking
  listeners, per-control tracker calls, or `data-umami-event` attributes that
  duplicate the shared handler.
- Keep event names human-readable and at most 50 characters. Preserve the full
  descriptive `label`, destination `url`, and useful `section`. Generate names
  for references and publication links from their underlying citation data and
  destination type, rather than DOI text alone. When adding a reference, supply
  its complete `title` and an optional unambiguous `short_title` in
  `data/references.csv`; the generator preserves these fields in the website's
  reference data. Reuse that metadata rather than hardcoding an event name for
  each reference. Derive table labels from the underlying data rather than
  rendered MathJax or ambiguous numeric text.
- Additional table properties are limited to public numeric `q`, `m`, `d`, and
  `r` values, supplied through `data-analytics-q`, `data-analytics-m`,
  `data-analytics-d`, and `data-analytics-r`. Preserve this allowlist and numeric
  validation. Do not turn arbitrary URL parameters into additional properties.
  Never collect form contents, visitor identifiers, or other visitor-specific
  information; add no cookies or tracking service.
- Preserve the shared visible-time milestones of 30, 60, 120, 300, and 600 seconds,
  visible-only elapsed time, and memory-only timer state. Table changes encoded
  by `#q=...&m=...&d=...&r=...` remain within the same page visit and must not reset
  the timer. New page visits, including history restoration, start fresh.
- Verify every added or changed control or link produces its intended name,
  full label, URL, placement, and allowed table properties exactly once per
  activation, or preserves its intentional exclusion. Cover dynamic redraws,
  nested icons/math, keyboard activation, normal navigation, and missing trackers
  with mocked analytics. New pages must include the shared scripts too.

## Development analytics exclusion

Agent visits, previews, and automated checks must never enter production Umami
statistics. Prefer local or intercepted pages. Before site scripts execute in
every browser context and popup, install this initialization script:

```js
try { localStorage.setItem('umami.disabled', '1'); } catch (error) {}
```

Intercept all remote requests, including the Umami loader and collection
requests, before the first navigation. Replace analytics with a local mock;
never forward mock calls or load the live tracker to verify analytics. Keep the
opt-out and request interception as independent safeguards. If tooling cannot
apply them before navigation, inspect source or use a protected local browser.
Never clear the agent browser's opt-out or add an unconditional production
opt-out that would disable real visitors' analytics.

Run the protected tests from the repository root:

```sh
python -B -m unittest discover -s tests -v
```

Browser tracking tests require Python Playwright and Chromium; use
`CHROMIUM_PATH` when Chromium is installed elsewhere. They read the shared
tracking scripts from a local sibling `RodrigoSanJose.github.io` checkout by
default; clone/check out that repository locally or set `PERSONAL_SITE_ROOT` to
its checkout path. Serve those assets through local test routes; never retrieve
them by loading the production website. The mathematical unit tests use standard
Python. Separate computations in `sage/compute.py` require SageMath and the GHWs
package; they are not needed for analytics-only changes.

## README edits

Preserve the existing README and its content. Before any README edit, explicitly
tell the user that `README.md` will change and describe the intended changes.
Never silently add analytics, maintenance, testing, or other documentation to it.

## References

Keep the references in alphabetical order of the surnames of their authors, then by year (as in the
amsalpha style): in `data/references.csv`, whose order the website follows, and in the reference
list at the end of `README.md`. When adding a reference, insert it at its place in both (the README
rule above applies) and give it an author-year key, such as `HKY92`. `tests/test_citation.py`
checks the order.
