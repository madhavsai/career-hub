"""
Build script for Career Hub.

Reads the source documents in this workspace and emits:
  static/content.json     - every section, keyed into the theme-based nav
  static/playbook-data.js - the AI Income Playbook's data + renderers, verbatim

Nothing is rewritten by hand: section bodies are lifted out of the source HTML
as-is, so the originals stay the single source of truth. Re-run this after
editing any source doc.

Deliberately excluded (personalised strategy content, per the build decision) -
see EXCLUSIONS at the bottom of this file for the machine-readable list.
"""

import json
import re
import sys
import html as htmllib
from datetime import datetime, timezone
from pathlib import Path

from method_details import DETAILS as METHOD_DETAILS

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "static"



def find_source(*candidates):
    """Resolve a source file by trying known locations in order.

    These folders get reorganised (Freelancing/ moved under Job search/ on
    2026-09-01), so the build looks in each plausible spot rather than dying on
    a hard-coded path - and names every place it looked if it still can't find it.
    """
    for rel in candidates:
        p = ROOT / rel
        if p.exists():
            return p
    raise SystemExit("source not found - looked in:\n  "
                     + "\n  ".join(str(ROOT / c) for c in candidates))


SRC_PLAYBOOK = find_source("Job search/Freelancing/ai-income-playbook.html",
                           "Freelancing/ai-income-playbook.html")
SRC_USGUIDE = find_source("Job search/US remote jobs/us-remote-ai-jobs-guide.html",
                          "US remote jobs/us-remote-ai-jobs-guide.html")
SRC_STRATEGY = find_source("Job search/ai-target-companies-and-outreach-strategy.html")
SRC_JDS = find_source("Job search/gcc jds")
SRC_SITES = find_source("Job search/websites for remote work.txt")


def read(p):
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------- extraction

def extract_sections(doc, pattern):
    """Pull <section> bodies out of a document. Sections are never nested in
    these files, so a non-greedy match to the next </section> is exact."""
    out = {}
    for m in re.finditer(pattern, doc, re.DOTALL):
        out[m.group(1)] = m.group(2).strip()
    return out


def strip_own_h2(body):
    """Remove a section's own <h2> title - the hub renders its own header, so
    keeping it would print the title twice."""
    return re.sub(r"^\s*<h2>.*?</h2>", "", body, count=1, flags=re.DOTALL).strip()


def strip_masthead(body):
    """Playbook sections open with a .masthead holding an eyebrow, an <h2> and
    a .dek lead paragraph. Keep the dek, drop the duplicated title."""
    m = re.search(r'<div class="masthead">(.*?)</div>', body, re.DOTALL)
    if not m:
        return body
    dek = re.search(r'<p class="dek">.*?</p>', m.group(1), re.DOTALL)
    replacement = '<div class="lead">' + dek.group(0) + "</div>" if dek else ""
    return (body[: m.start()] + replacement + body[m.end():]).strip()


def split_at_h3sub(body):
    """Split a section body on <h3 class="sub"> boundaries. Returns
    [(heading_text_or_None, html), ...]; the first entry is whatever preceded
    the first heading."""
    parts = re.split(r'(<h3 class="sub">.*?</h3>)', body, flags=re.DOTALL)
    out = [(None, parts[0])]
    for i in range(1, len(parts), 2):
        heading = re.sub(r"<[^>]+>", "", parts[i])
        heading = htmllib.unescape(heading).replace("\xa0", " ").strip()
        out.append((heading, parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")))
    return out


def split_at_h4(body, wanted):
    """Split a section body into (matched_blocks, remainder), where a block is
    an <h4> heading plus everything up to the next <h4>. `wanted` holds
    substrings matched against the heading text."""
    parts = re.split(r"(<h4>.*?</h4>)", body, flags=re.DOTALL)
    taken, kept = [], [parts[0]]
    for i in range(1, len(parts), 2):
        block = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
        text = htmllib.unescape(re.sub(r"<[^>]+>", "", parts[i]))
        if any(w.lower() in text.lower() for w in wanted):
            taken.append(block)
        else:
            kept.append(block)
    return "".join(taken).strip(), "".join(kept).strip()


# Personalised framing baked into headings of the source docs. The hub is a
# compilation, so these are neutralised - content underneath is untouched.
HEADING_REWRITES = [
    ("Vector DB / Retrieval Infra (directly RAG-relevant to you)",
     "Vector DB / Retrieval Infra"),
    ("Voice AI &amp; Conversational AI — your strongest fit category",
     "Voice AI &amp; Conversational AI"),
    ("India-founded / India-R&amp;D companies serving the US market — your highest hit-rate tier",
     "India-founded / India-R&amp;D companies serving the US market"),
    ("India-founded / India-R&D companies serving the US market — your highest hit-rate tier",
     "India-founded / India-R&D companies serving the US market"),
    ("Full-time, physically-in-US (context, not your realistic target)",
     "Full-time, physically in the US"),
    ("Full-time, remote-from-India (your realistic target)",
     "Full-time, remote from India"),
]


def neutralise(body):
    for old, new in HEADING_REWRITES:
        body = body.replace(old, new)
    return body


# Cross-document hrefs in the sources point at sibling files that no longer sit
# beside this page, and in-page anchors point at the old section ids. Both are
# remapped onto the hub's own ids so nothing dead-ends.
FILE_LINKS = {
    "US remote jobs/us-remote-ai-jobs-guide.html": "#jobs-companies-global",
    "gcc jds/": "#jobs-gcc-jds",
    "../interview prep/study-v3/curriculum.html": "#jobs-gcc-jds",
}

ANCHORS = {
    "#using": "#strategy-data-quality",
    "#india": "#jobs-companies-india",
    "#global": "#jobs-companies-global",
    "#methods": "#strategy-methods",
    "#freelance": "#free-platforms",
    "#sources": "#strategy-sources",
    "#tldr": "#jobs-companies-global",
    "#boards": "#jobs-boards",
    "#companies": "#jobs-companies-global",
    "#comp": "#strategy-comp",
    "#interview": "#strategy-interview",
    "#resume": "#strategy-resume",
    "#hidden": "#jobs-boards",
    "#strategy": "#jobs-companies-global",
    "#plan": "#jobs-companies-global",
    "#playbook": "#strategy-search-playbook",
}


def rewrite_links(body):
    for old, new in FILE_LINKS.items():
        body = body.replace('href="' + old + '"', 'href="' + new + '"')
    return re.sub(
        r'href="(#[a-z-]+)"',
        lambda m: 'href="' + ANCHORS.get(m.group(1), m.group(1)) + '"',
        body,
    )


def clean(body):
    return rewrite_links(neutralise(body)).strip()


# ------------------------------------------------------------------ markdown

def md_to_html(md):
    """Minimal converter for the GCC job-description files: headings, nested
    bullets, bold, links, paragraphs. That is the whole vocabulary they use."""

    def inline(t):
        t = htmllib.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
        return t

    out, depth, para = [], 0, []

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def close_lists(target=0):
        nonlocal depth
        while depth > target:
            out.append("</li></ul>")
            depth -= 1

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            close_lists()
            level = min(len(m.group(1)) + 2, 6)      # '#' -> h3, '##' -> h4
            out.append("<h%d>%s</h%d>" % (level, inline(m.group(2)), level))
            continue
        m = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m:
            flush_para()
            want = len(m.group(1)) // 2 + 1
            if want > depth:
                while depth < want:
                    out.append('<ul class="tight">')
                    depth += 1
                out.append("<li>")
            else:
                close_lists(want)
                out.append("</li><li>")
            out.append(inline(m.group(2)))
            continue
        para.append(line.strip())

    flush_para()
    close_lists()
    return "\n".join(out)



# ------------------------------------------------------- GPU-rental removal
#
# User decision (2026-09-01): renting the RTX 4090 out or hosting it in a cloud
# marketplace is not a channel they will pursue. Using the card to *train and
# publish models* stays. So the rental platforms are stripped everywhere they
# appear, and the three training/publishing entries that shared that section
# are kept and re-homed.
#
# The source document is untouched - re-running this build reproduces the cut.

RENTAL_ENTITIES = [
    "Vast.ai", "Salad.com (SaladCloud)", "Salad.com",
    "RunPod (Community Cloud)", "RunPod Community Cloud", "RunPod",
    "io.net", "Akash Homenode", "Golem Network",
    "Render Network (RNDR)", "Render Network",
    "TensorDock", "ThunderCompute", "Modal Labs",
]

# Kept from the old Part 02: earning from models you train and publish.
MODEL_WORK_KEEP = ["Civitai Creator Program", "Hugging Face", "Replicate"]

MODEL_WORK_HTML = (
    '<div class="lead"><p class="dek">Earning from models you train and publish, '
    'using the 4090 for the work itself. The GPU-rental and cloud-hosting '
    'channels that used to sit here have been removed.</p></div>'
    '<div class="card-grid" id="grid-modelwork"></div>'
)


def _split_entries(block):
    """Split a dossier array body into whole {name:...} entries."""
    return [c for c in re.split(r'(?m)^(?=\{name:")', block) if c.strip()]


def _array_body(js, name):
    m = re.search(r"const %s = \[\n(.*?)\n\];" % name, js, re.DOTALL)
    if not m:
        raise SystemExit("playbook JS: array %s not found" % name)
    return m


def strip_gpu_rental(js):
    """Remove every GPU-rental/hosting channel from the lifted playbook JS."""

    # 1. Fold the three GPU arrays into one array of the kept training plays.
    kept, spans = [], []
    for arr in ("GPU_YES", "GPU_MAYBE", "GPU_NO"):
        m = _array_body(js, arr)
        spans.append(m.span())
        for entry in _split_entries(m.group(1)):
            name = re.match(r'\{name:"([^"]+)"', entry).group(1)
            if name in MODEL_WORK_KEEP:
                kept.append(entry.rstrip())
    if len(kept) != len(MODEL_WORK_KEEP):
        raise SystemExit("expected %d kept GPU entries, found %d"
                         % (len(MODEL_WORK_KEEP), len(kept)))

    replacement = "const MODEL_WORK = [\n" + "\n\n".join(kept) + "\n];"
    for start, end in sorted(spans, reverse=True):        # last first, keeps offsets valid
        js = js[:start] + ("" if (start, end) != spans[0] else replacement) + js[end:]

    # 2. Repoint the three grid mounts at the single new grid.
    js = re.sub(r"document\.getElementById\('grid-gpu-(?:maybe|no)'\)"
                r"\.innerHTML = GPU_\w+\.map\(card\)\.join\(''\);\n", "", js)
    js = js.replace(
        "document.getElementById('grid-gpu-yes').innerHTML = GPU_YES.map(card).join('');",
        "document.getElementById('grid-modelwork').innerHTML = MODEL_WORK.map(card).join('');")

    # 3. Drop the rental-only categories from the matrix, and rental names from
    #    the categories that mix them with other work.
    for key in ("GPU Rental", "GPU Compute", "Cloud GPU"):
        js = re.sub(r'(?m)^"%s":\[[^\]]*\],\n' % re.escape(key), "", js)

    # 4. Purge rental names from every remaining list - category pills and
    #    ranking rows alike.
    for name in RENTAL_ENTITIES:
        n = re.escape(name)
        js = re.sub(r'\["%s","[^"]*",\d+\],?' % n, "", js)      # ranking row
        js = re.sub(r'"%s",' % n, "", js)                        # pill, mid-list
        js = re.sub(r',"%s"(?=\])' % n, "", js)                  # pill, list end

    # 5. The GPU-owners league table is now a training/publishing list.
    js = js.replace('{title:"Top 10 best for GPU owners (RTX 4090)", sub:"", items:[',
                    '{title:"RTX 4090 — training & publishing plays", sub:"", items:[')

    # 6. Roadmap: the rental steps go, the rest of each milestone stays.
    js = js.replace(
        ", or list the RTX 4090 on Vast.ai (near-zero marginal effort — "
        "it's already-owned, already-idle hardware)", "")
    js = js.replace(
        '"List the 4090 on Vast.ai in parallel — pure upside, no time cost '
        'against the day job",', "")
    js = js.replace(" plus accumulating GPU rental income", "")

    # 7. The GPU-rental field note.
    js = re.sub(r'(?m)^\{cat:"GPU rental income".*?\n(?=\{cat:")', "", js,
                flags=re.DOTALL)

    # --- assertions: nothing rental survived, nothing kept was lost ---
    for name in RENTAL_ENTITIES:
        if name in js:
            raise SystemExit("GPU purge missed a reference to %r" % name)
    for name in MODEL_WORK_KEEP:
        if name not in js:
            raise SystemExit("GPU purge dropped a kept entry: %r" % name)
    for stray in ("grid-gpu", "GPU_YES", "GPU_MAYBE", "GPU_NO", "GPU rental"):
        if stray in js:
            raise SystemExit("GPU purge left %r behind" % stray)
    return js



# ------------------------------------------------------ the 50 methods as cards
#
# The source renders each method as a two-cell table row: a number, then a bold
# title plus one summary line. That is too cramped once each method carries a
# paragraph, so the rows are reshaped into cards here. The source's own title and
# summary are preserved word for word; the elaboration underneath comes from
# method_details.py and is rendered in its own labelled block so the two are
# never mistaken for each other.

METHOD_ROW = re.compile(
    r"<tr><td>(\d+)</td><td><strong>(.*?)</strong>\s*(.*?)</td></tr>", re.DOTALL)


def render_methods(section_html):
    groups = split_at_h3sub(section_html)
    intro = groups[0][1].strip()
    out, seen = [intro], set()

    for heading, block in groups[1:]:
        cards = []
        for num, title, summary in METHOD_ROW.findall(block):
            n = int(num)
            seen.add(n)
            detail = METHOD_DETAILS.get(n)
            cards.append(
                '<article class="method" id="method-%d">'
                '<div class="m-head"><span class="m-num">%02d</span>'
                '<h4>%s</h4></div>'
                '<p class="m-sum">%s</p>%s</article>'
                % (n, n, title.rstrip(".").strip(), summary.strip(),
                   ('<div class="m-detail"><span class="m-label">How it works</span>'
                    '<p>%s</p></div>' % detail) if detail else ""))
        if not cards:
            raise SystemExit("methods: no rows parsed under %r" % heading)
        out.append('<h3 class="section-h">%s</h3><div class="method-grid">%s</div>'
                   % (htmllib.escape(heading), "".join(cards)))

    if seen != set(range(1, 51)):
        raise SystemExit("methods: expected 1-50, parsed %d (missing %s)"
                         % (len(seen), sorted(set(range(1, 51)) - seen)))
    undocumented = sorted(seen - set(METHOD_DETAILS))
    if undocumented:
        print("  note: %d methods have no elaboration yet: %s"
              % (len(undocumented), undocumented))
    return "".join(out)


# ----------------------------------------------------------------- assembling

def build():
    try:                                  # Windows consoles default to cp1252
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    playbook_doc = read(SRC_PLAYBOOK)
    usguide_doc = read(SRC_USGUIDE)
    strategy_doc = read(SRC_STRATEGY)

    pb = extract_sections(
        playbook_doc, r'<section class="part[^"]*" id="([^"]+)">(.*?)</section>')
    ug = extract_sections(usguide_doc, r'<section id="([^"]+)">(.*?)</section>')
    st = extract_sections(strategy_doc, r'<section id="([^"]+)">(.*?)</section>')

    for name, got, want in (("playbook", pb, 10), ("us guide", ug, 11), ("strategy", st, 6)):
        if len(got) != want:
            raise SystemExit(
                "%s: expected %d sections, found %d (%s) - source layout changed"
                % (name, want, len(got), ", ".join(sorted(got))))

    pb = {k: clean(strip_masthead(v)) for k, v in pb.items()}
    ug = {k: clean(strip_own_h2(v)) for k, v in ug.items()}
    st = {k: clean(strip_own_h2(v)) for k, v in st.items()}

    # Playbook Part 00: keep the verification note, drop the profile briefing.
    ver = re.search(r"<h3 class=\"section-h\">What's verified vs\. estimated</h3>(.*)$",
                    pb["part-overview"], re.DOTALL)
    playbook_caveat = ver.group(1).strip() if ver else ""

    # Strategy section 4 splits into freelance platforms and USD payment routes.
    freelance_parts = split_at_h3sub(st["freelance"])
    st_intro = freelance_parts[0][1].strip()
    st_platforms = next((h for t, h in freelance_parts if t and t.startswith("4.1")), "")
    st_usd = next((h for t, h in freelance_parts if t and t.startswith("4.2")), "")
    if not (st_platforms and st_usd):
        raise SystemExit("strategy section 4: could not find the 4.1 / 4.2 subheadings")

    # US guide parts 3-4: lift the India-R&D block out of the global list.
    india_block, global_blocks = split_at_h4(ug["companies"], ["India-founded / India-R"])
    if not india_block:
        raise SystemExit("us guide: India-R&D company block not found")

    # The user's own nine-platform shortlist, kept verbatim.
    site_lines = [re.sub(r"^\d+\.\s*", "", l).strip()
                  for l in read(SRC_SITES).splitlines() if l.strip()]
    items = []
    for s in site_lines:
        m = re.match(r"^(https?://\S+?)/?\s*(\(.*\))?$", s)
        if m:
            url = m.group(1)
            name = url.split("//")[1].split("/")[0].replace("www.", "")
            note = (m.group(2) or "").strip("() ")
        else:
            name, url, note = s, "", ""
        label = htmllib.escape(name)
        link = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, label)
                if url else label)
        items.append("<li>" + link
                     + (" &mdash; " + htmllib.escape(note) if note else "") + "</li>")
    sites_html = (
        '<h3 class="section-h">Your own shortlist &mdash; '
        '<code>websites for remote work.txt</code></h3>'
        '<p class="section-note">The nine platforms kept in that file, verbatim and '
        'unmerged. Each also appears in the platform dossier or the reference table '
        'above.</p><ul class="tight">' + "".join(items) + "</ul>"
    )

    # GCC job descriptions.
    jd_blocks = []
    for f in sorted(SRC_JDS.glob("*.md")):
        jd_blocks.append(
            '<details class="jd"><summary>' + htmllib.escape(f.stem) + "</summary>"
            '<div class="jd-body">' + md_to_html(read(f)) + "</div></details>")
    if not jd_blocks:
        raise SystemExit("no job descriptions found in " + str(SRC_JDS))
    jds_section = (
        '<div class="lead"><p class="dek">The '
        + str(len(jd_blocks)) +
        ' job descriptions saved in <code>Job search/gcc jds/</code>, rendered in '
        'full. Click a role to expand it.</p></div>' + "".join(jd_blocks))

    sources = (
        '<h3 class="section-h">AI Income Playbook &mdash; sourcing &amp; caveats</h3>'
        + pb["part-methodology"]
        + '<h3 class="section-h">US Remote AI Jobs Guide &mdash; sources &amp; methodology</h3>'
        + ug["sources"]
        + '<h3 class="section-h">AI Job Search Reference &mdash; sources</h3>'
        + st["sources"])

    joiner = '<hr class="joiner">'

    groups = [
        {
            "id": "freelancing",
            "title": "Freelancing",
            "sections": [
                {"id": "free-platforms",
                 "title": "Platforms &amp; marketplaces",
                 "source": "AI Income Playbook Part 01 + AI Job Search Reference §4.1 + websites for remote work.txt",
                 "track": "card",
                 "html": pb["part-platforms"] + joiner
                         + '<h3 class="section-h">Cross-reference &mdash; platforms named in '
                           'the job-search reference</h3>'
                         + st_intro + st_platforms + joiner + sites_html},
                {"id": "free-modelwork", "title": "Model training &amp; publishing",
                 "source": "AI Income Playbook Part 02 (GPU-rental channels removed)",
                 "track": "card", "html": MODEL_WORK_HTML},
                {"id": "free-consulting", "title": "Consulting by industry",
                 "source": "AI Income Playbook Part 04", "track": "row",
                 "html": pb["part-consulting"]},
                {"id": "free-matrix", "title": "Categorization matrix",
                 "source": "AI Income Playbook Part 03", "track": None,
                 "html": pb["part-categories"]},
                {"id": "free-hidden", "title": "Hidden opportunities",
                 "source": "AI Income Playbook Part 05", "track": None,
                 "html": pb["part-hidden"]},
                {"id": "free-rankings", "title": "Rankings",
                 "source": "AI Income Playbook Part 06", "track": None,
                 "html": pb["part-rankings"]},
                {"id": "free-roadmap", "title": "$100 → $10k/mo roadmap",
                 "source": "AI Income Playbook Part 07", "track": None,
                 "html": pb["part-roadmap"]},
                {"id": "free-fieldnotes", "title": "Field notes (Reddit / HN / GitHub)",
                 "source": "AI Income Playbook Part 08", "track": None,
                 "html": pb["part-fieldnotes"]},
            ],
        },
        {
            "id": "jobs",
            "title": "Jobs",
            "sections": [
                {"id": "jobs-companies-global", "title": "US / global companies",
                 "source": "US Remote AI Jobs Guide Parts 3–4 + AI Job Search Reference §2",
                 "track": "row",
                 "html": global_blocks + joiner
                         + '<h3 class="section-h">AI Job Search Reference &mdash; US / global '
                           'remote, USD pay</h3>' + st["global"]},
                {"id": "jobs-companies-india", "title": "Indian companies",
                 "source": "AI Job Search Reference §1 + US Remote AI Jobs Guide Part 4",
                 "track": "row",
                 "html": st["india"] + joiner
                         + '<h3 class="section-h">US Remote AI Jobs Guide &mdash; India-founded '
                           '/ India-R&amp;D companies</h3>' + india_block},
                {"id": "jobs-gcc-jds", "title": "GCC job descriptions",
                 "source": "Job search/gcc jds/", "track": None,
                 "html": jds_section},
                {"id": "jobs-boards", "title": "Job boards &amp; channels",
                 "source": "US Remote AI Jobs Guide Parts 1–2 and 8", "track": "row",
                 "html": ug["boards"] + joiner
                         + '<h3 class="section-h">Hidden hiring channels</h3>' + ug["hidden"]},
            ],
        },
        {
            "id": "strategy",
            "title": "Strategy &amp; reference",
            "sections": [
                {"id": "strategy-methods", "title": "The 50 outreach methods",
                 "source": "AI Job Search Reference §3 (+ added elaborations)",
                 "track": None,
                 "html": render_methods(st["methods"])},
                {"id": "strategy-comp", "title": "Compensation data",
                 "source": "US Remote AI Jobs Guide Part 5", "track": None,
                 "html": ug["comp"]},
                {"id": "strategy-interview", "title": "Interview prep",
                 "source": "US Remote AI Jobs Guide Part 6", "track": None,
                 "html": ug["interview"]},
                {"id": "strategy-resume", "title": "Resume &amp; portfolio",
                 "source": "US Remote AI Jobs Guide Part 7", "track": None,
                 "html": ug["resume"]},
                {"id": "strategy-usd", "title": "Getting paid in USD",
                 "source": "AI Job Search Reference §4.2", "track": None,
                 "html": st_usd},
                {"id": "strategy-search-playbook", "title": "Platform search playbook",
                 "source": "US Remote AI Jobs Guide Part 11", "track": None,
                 "html": ug["playbook"]},
                {"id": "strategy-data-quality", "title": "Data-quality warnings",
                 "source": "AI Job Search Reference §0 + AI Income Playbook Part 00",
                 "track": None,
                 "html": st["using"] + joiner
                         + '<h3 class="section-h">AI Income Playbook &mdash; what&rsquo;s '
                           'verified vs. estimated</h3>' + playbook_caveat},
                {"id": "strategy-sources", "title": "Sources &amp; methodology",
                 "source": "All three source documents", "track": None,
                 "html": sources},
            ],
        },
    ]

    content = {
        "generated": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M"),
        "groups": groups,
        "sources": [
            {"label": "AI Income Playbook",
             "path": "Freelancing/ai-income-playbook.html"},
            {"label": "US Remote AI Jobs Guide",
             "path": "Job search/US remote jobs/us-remote-ai-jobs-guide.html"},
            {"label": "AI Job Search Reference",
             "path": "Job search/ai-target-companies-and-outreach-strategy.html"},
            {"label": "Saved GCC JDs", "path": "Job search/gcc jds/"},
            {"label": "Remote-work shortlist",
             "path": "Job search/websites for remote work.txt"},
        ],
        "exclusions": EXCLUSIONS,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "content.json").write_text(
        json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8")

    # The playbook renders its card grids, matrix, rankings, roadmap and field
    # notes from JS data. Lift that block verbatim rather than re-typing it; the
    # hub calls renderPlaybook() once its sections are in the DOM.
    lines = playbook_doc.splitlines()
    js = "\n".join(lines[376:882])           # 1-indexed lines 377..882
    if "const GENERAL" not in js or "FIELDNOTES.map" not in js:
        raise SystemExit("playbook JS block boundaries moved - check line numbers")
    js = strip_gpu_rental(js)
    (OUT / "playbook-data.js").write_text(
        "/* Generated by build_content.py - lifted from\n"
        "   Freelancing/ai-income-playbook.html lines 377-882, with the GPU-rental\n"
        "   channels stripped (see strip_gpu_rental). Do not edit here. */\n"
        "function renderPlaybook(){\n" + js + "\n}\n", encoding="utf-8")

    total = sum(len(s["html"]) for g in groups for s in g["sections"])
    print("content.json      %d sections, %s chars"
          % (sum(len(g["sections"]) for g in groups), format(total, ",")))
    print("playbook-data.js  %d lines lifted verbatim" % len(js.splitlines()))
    for g in groups:
        print("  " + re.sub(r"&amp;", "&", g["title"]))
        for s in g["sections"]:
            print("    %-42s %9s chars"
                  % (re.sub(r"&amp;", "&", s["title"]), format(len(s["html"]), ",")))


EXCLUSIONS = [
    {"doc": "ai-income-playbook.html",
     "section": "Part 02 - GPU rental / cloud hosting (Vast.ai, Salad, RunPod, "
                "io.net, Akash, Golem, Render, TensorDock, ThunderCompute, Modal)",
     "why": "user decided renting the 4090 out is not a channel they will pursue; "
            "the training/publishing plays from that section are kept under "
            "'Model training & publishing'"},
    {"doc": "us-remote-ai-jobs-guide.html",
     "section": "#tldr - TL;DR Strategy",
     "why": "personalised: three viable paths, best-fit title, biggest risk to manage"},
    {"doc": "us-remote-ai-jobs-guide.html",
     "section": "#strategy - Part 9, Your Personal Strategy",
     "why": "personalised: strengths and gaps, ranked target roles, fit-tiering"},
    {"doc": "us-remote-ai-jobs-guide.html",
     "section": "#plan - Part 10, 90-Day Action Plan",
     "why": "personalised: a dated execution plan"},
    {"doc": "ai-target-companies-and-outreach-strategy - Copy.html",
     "section": "entire file",
     "why": "superseded personalised version - voice-AI wedge, fit-tiering, 90-day plan"},
    {"doc": "ai-income-playbook.html",
     "section": "Part 00 - 'The profile this was built for'",
     "why": "personalised briefing block; Part 00's verification note is kept"},
]


if __name__ == "__main__":
    build()
