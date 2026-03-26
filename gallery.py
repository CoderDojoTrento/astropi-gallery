"""
Gallery generator: creates a space-themed HTML page showcasing
Mission Zero animation videos with preview thumbnails.
"""

import html
import os
import base64
import shutil
from pathlib import Path


_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".gif": "image/gif",
}


def _inline_image_src(image_path, output_dir=None):
    """Return a data URI for a small image, or copy to output_dir and return basename."""
    size = os.path.getsize(image_path)
    ext = os.path.splitext(image_path)[1].lower()
    mime = _MIME_TYPES.get(ext, "application/octet-stream")

    if size < 200_000:  # inline if < 200KB
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"

    # Too large to inline: copy to output dir and reference by basename
    basename = os.path.basename(image_path)
    if output_dir:
        dest = os.path.join(output_dir, basename)
        if os.path.abspath(image_path) != os.path.abspath(dest):
            shutil.copy2(image_path, dest)
    return basename


def _logo_tag(path, alt, output_dir, css_class="logo-img"):
    """Build an <img> tag for a logo, inlining or copying as needed."""
    if not path:
        return ""
    if not os.path.exists(path):
        import warnings
        warnings.warn(f"Logo image not found: {path}")
        return ""
    src = _inline_image_src(path, output_dir)
    return f'<img src="{src}" alt="{html.escape(alt)}" class="{css_class}">'


def generate_gallery(entries, output_path, title=None, subtitle=None,
                     description=None, year=None,
                     instructor_name=None, instructor_logo_path=None,
                     instructor_link=None,
                     esa_logo_path=None, raspberry_logo_path=None,
                     astropi_logo_path=None, mission_zero_logo_path=None):
    """
    Generate a space-themed HTML gallery page.

    Args:
        entries: list of dicts with keys:
            - name: display name (participant + project)
            - participant: participant/team name
            - project: project name
            - video: path to .mp4 (relative to HTML)
            - preview: path to .png (relative to HTML)
            - duration: animation duration in seconds
            - criteria_pass: bool (optional)
        output_path: where to write the HTML file
        title: page title (default: "Mission Zero Gallery")
        subtitle: subtitle text (may contain HTML link tags)
        description: paragraph below the subtitle (may contain HTML link tags)
        year: challenge year/season to display (e.g. "2025/26")
        instructor_name: name of the local promoter/instructor/club
        instructor_logo_path: path to promoter logo image (must start with promoter-)
        instructor_link: URL for the promoter logo (opens in new tab)
        esa_logo_path: path to ESA logo (white on black)
        raspberry_logo_path: path to Raspberry Pi Foundation logo (white on black)
        astropi_logo_path: path to Astro Pi logo
        mission_zero_logo_path: path to Mission Zero logo
    """
    if title is None:
        title = "Mission Zero Gallery"
    if subtitle is None:
        subtitle = "Our code ran on the International Space Station!"
    if description is None:
        description = ("Each animation was coded in Python and displayed "
                       "on the Astro\u00a0Pi LED\u00a0matrix aboard the ISS.")
    if instructor_name is None:
        instructor_name = "Your School / Club"

    output_dir = os.path.dirname(os.path.abspath(output_path))

    cards_html = []
    for i, e in enumerate(entries):
        participant = html.escape(e.get("participant", ""))
        project = html.escape(e.get("project", e.get("name", "")))
        video = html.escape(e["video"])
        preview_file = e.get("preview_path", "")
        if preview_file and os.path.exists(preview_file):
            preview_src = _inline_image_src(preview_file, output_dir)
        else:
            preview_src = html.escape(e["preview"])
        duration = e.get("duration", 0)
        passed = e.get("criteria_pass", None)

        badge = ""
        if passed is True:
            badge = '<span class="badge pass" title="Meets all Mission Zero criteria">&#x2714; Flight Ready</span>'
        elif passed is False:
            badge = '<span class="badge fail" title="Does not meet all criteria">&#x26A0; Needs Fix</span>'

        dur_str = f"{duration:.0f}s" if duration else ""

        cards_html.append(f'''
      <article class="card" data-video="{video}" data-name="{html.escape(project)}" tabindex="0">
        <div class="card-img">
          <img src="{preview_src}" alt="{html.escape(project)}" loading="lazy" width="378" height="378">
          <div class="play-icon" aria-hidden="true">&#9654;</div>
          <span class="dur">{dur_str}</span>
        </div>
        <div class="card-body">
          <h3 class="card-title">{project}</h3>
          <p class="card-sub">{participant}</p>
          {badge}
        </div>
      </article>''')

    # ── Build logo tags ──
    astropi_tag = _logo_tag(astropi_logo_path, "Astro Pi", output_dir, "logo-hero")
    mzero_tag = _logo_tag(mission_zero_logo_path, "Mission Zero", output_dir, "logo-hero")
    esa_tag = _logo_tag(esa_logo_path, "European Space Agency", output_dir)
    raspberry_tag = _logo_tag(raspberry_logo_path, "Raspberry Pi Foundation", output_dir)

    if instructor_logo_path and os.path.exists(instructor_logo_path):
        promoter_inner = (
            f'<img src="{_inline_image_src(instructor_logo_path, output_dir)}" '
            f'alt="{html.escape(instructor_name)}" class="logo-img logo-promoter">'
        )
    else:
        promoter_inner = (
            f'<div class="logo-placeholder">{html.escape(instructor_name)}</div>'
        )

    if instructor_link:
        promoter_tag = (
            f'<a href="{html.escape(instructor_link)}" target="_blank" '
            f'rel="noopener" aria-label="{html.escape(instructor_name)}">'
            f'{promoter_inner}</a>'
        )
    else:
        promoter_tag = promoter_inner

    # Wrap org logos in links when present
    def _wrap_link(tag, href, label):
        if not tag:
            return ""
        return f'<a href="{href}" target="_blank" rel="noopener" aria-label="{label}">{tag}</a>'

    esa_link = _wrap_link(esa_tag, "https://www.esa.int/Education/AstroPI", "European Space Agency")
    raspberry_link = _wrap_link(raspberry_tag, "https://www.raspberrypi.org", "Raspberry Pi Foundation")

    # Year badge
    year_html = ""
    if year:
        year_html = f'<span class="year-badge">{html.escape(str(year))}</span>'

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

:root{{
  --bg:#0a0c1a;
  --surface:#111428;
  --card:#161938;
  --border:#1f2352;
  --accent:#00e5ff;
  --accent2:#ff2d78;
  --accent3:#b54cff;
  --gold:#ffd54f;
  --text:#e2e5ff;
  --text2:#8a8fc4;
  --radius:14px;
  --font-display:'Outfit',system-ui,sans-serif;
  --font-body:'DM Sans',system-ui,sans-serif;
}}

@font-face{{
  font-family:'Outfit';
  font-display:swap;
  src:url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
}}

html{{
  font-family:var(--font-body);
  background:var(--bg);
  color:var(--text);
  -webkit-font-smoothing:antialiased;
  scroll-behavior:smooth;
}}

body{{
  min-height:100vh;
  background:
    radial-gradient(ellipse 80% 50% at 20% 0%,rgba(0,229,255,.06),transparent),
    radial-gradient(ellipse 60% 40% at 80% 100%,rgba(181,76,255,.05),transparent),
    var(--bg);
}}

/* ── stars ── */
.stars{{
  position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:
    /* bright stars */
    radial-gradient(2.5px 2.5px at 4% 7%,rgba(255,255,255,.95),transparent),
    radial-gradient(2px 2px at 12% 18%,rgba(200,220,255,1),transparent),
    radial-gradient(2px 2px at 23% 4%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 36% 14%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 48% 9%,rgba(0,229,255,.9),transparent),
    radial-gradient(2px 2px at 61% 6%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 74% 11%,rgba(200,220,255,.95),transparent),
    radial-gradient(2px 2px at 87% 3%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 95% 16%,rgba(255,213,79,.8),transparent),
    radial-gradient(2px 2px at 8% 32%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 19% 41%,rgba(0,229,255,.85),transparent),
    radial-gradient(2px 2px at 33% 28%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 44% 38%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 58% 45%,rgba(200,220,255,.95),transparent),
    radial-gradient(2px 2px at 69% 33%,rgba(255,213,79,.8),transparent),
    radial-gradient(2px 2px at 82% 42%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 93% 36%,rgba(181,76,255,.8),transparent),
    radial-gradient(2px 2px at 5% 55%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 16% 63%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 28% 58%,rgba(0,229,255,.85),transparent),
    radial-gradient(2px 2px at 41% 67%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 53% 54%,rgba(200,220,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 66% 62%,rgba(255,255,255,.95),transparent),
    radial-gradient(2px 2px at 78% 57%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 91% 65%,rgba(255,213,79,.75),transparent),
    radial-gradient(2px 2px at 10% 78%,rgba(181,76,255,.7),transparent),
    radial-gradient(2.5px 2.5px at 22% 84%,rgba(255,255,255,.9),transparent),
    radial-gradient(2px 2px at 35% 76%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 47% 88%,rgba(0,229,255,.8),transparent),
    radial-gradient(2.5px 2.5px at 62% 81%,rgba(255,255,255,.9),transparent),
    radial-gradient(2px 2px at 75% 92%,rgba(200,220,255,.85),transparent),
    radial-gradient(2px 2px at 88% 85%,rgba(255,255,255,.9),transparent),
    radial-gradient(2.5px 2.5px at 97% 78%,rgba(255,255,255,.85),transparent);
  background-size:100% 100%;
}}
@keyframes twinkle{{0%,100%{{opacity:.6}}50%{{opacity:1}}}}
@keyframes twinkle2{{0%,100%{{opacity:.8}}60%{{opacity:.4}}}}
/* dim + medium star field */
.stars::before{{
  content:'';position:absolute;inset:0;
  background-image:
    radial-gradient(1.5px 1.5px at 2% 12%,rgba(255,255,255,.6),transparent),
    radial-gradient(1px 1px at 7% 26%,rgba(255,255,255,.45),transparent),
    radial-gradient(1.5px 1.5px at 14% 8%,rgba(255,255,255,.55),transparent),
    radial-gradient(1px 1px at 18% 52%,rgba(255,255,255,.4),transparent),
    radial-gradient(1.5px 1.5px at 24% 35%,rgba(255,255,255,.6),transparent),
    radial-gradient(1px 1px at 29% 68%,rgba(255,255,255,.35),transparent),
    radial-gradient(1.5px 1.5px at 34% 18%,rgba(255,255,255,.55),transparent),
    radial-gradient(1px 1px at 38% 82%,rgba(255,255,255,.4),transparent),
    radial-gradient(1.5px 1.5px at 43% 48%,rgba(255,255,255,.5),transparent),
    radial-gradient(1px 1px at 47% 5%,rgba(255,255,255,.4),transparent),
    radial-gradient(1.5px 1.5px at 52% 72%,rgba(255,255,255,.55),transparent),
    radial-gradient(1px 1px at 56% 30%,rgba(255,255,255,.45),transparent),
    radial-gradient(1.5px 1.5px at 61% 92%,rgba(255,255,255,.5),transparent),
    radial-gradient(1px 1px at 65% 15%,rgba(255,255,255,.4),transparent),
    radial-gradient(1.5px 1.5px at 70% 55%,rgba(255,255,255,.6),transparent),
    radial-gradient(1px 1px at 74% 40%,rgba(255,255,255,.35),transparent),
    radial-gradient(1.5px 1.5px at 79% 78%,rgba(255,255,255,.5),transparent),
    radial-gradient(1px 1px at 83% 22%,rgba(255,255,255,.45),transparent),
    radial-gradient(1.5px 1.5px at 88% 60%,rgba(255,255,255,.55),transparent),
    radial-gradient(1px 1px at 92% 8%,rgba(255,255,255,.4),transparent),
    radial-gradient(1.5px 1.5px at 96% 45%,rgba(255,255,255,.5),transparent),
    radial-gradient(1px 1px at 3% 95%,rgba(255,255,255,.35),transparent),
    radial-gradient(1px 1px at 15% 74%,rgba(255,255,255,.3),transparent),
    radial-gradient(1px 1px at 27% 90%,rgba(255,255,255,.35),transparent),
    radial-gradient(1px 1px at 40% 60%,rgba(255,255,255,.3),transparent),
    radial-gradient(1px 1px at 55% 20%,rgba(255,255,255,.25),transparent),
    radial-gradient(1px 1px at 68% 85%,rgba(255,255,255,.3),transparent),
    radial-gradient(1px 1px at 80% 50%,rgba(255,255,255,.25),transparent),
    radial-gradient(1px 1px at 94% 72%,rgba(255,255,255,.3),transparent);
  background-size:100% 100%;
}}
/* extra bright stars layer */
.stars::after{{
  content:'';position:absolute;inset:0;
  background-image:
    radial-gradient(2.5px 2.5px at 20% 30%,rgba(255,255,255,.9),transparent),
    radial-gradient(2px 2px at 60% 70%,rgba(0,229,255,.8),transparent),
    radial-gradient(2px 2px at 80% 15%,rgba(255,213,79,.7),transparent),
    radial-gradient(2.5px 2.5px at 45% 85%,rgba(255,255,255,.85),transparent),
    radial-gradient(2px 2px at 15% 60%,rgba(181,76,255,.7),transparent),
    radial-gradient(2.5px 2.5px at 90% 50%,rgba(255,255,255,.8),transparent),
    radial-gradient(2px 2px at 35% 10%,rgba(0,229,255,.7),transparent),
    radial-gradient(2px 2px at 70% 40%,rgba(255,255,255,.85),transparent);
  background-size:100% 100%;
}}

.page{{position:relative;z-index:1;max-width:1280px;margin:0 auto;padding:0 24px}}

/* ── logo bar ── */
.logo-bar{{
  display:flex;align-items:center;justify-content:space-between;
  padding:28px 0 20px;gap:20px;flex-wrap:wrap;
}}
.logos-left{{display:flex;align-items:center;gap:24px;flex-wrap:wrap}}
.logo-img{{height:56px;width:auto;opacity:.92;transition:opacity .2s}}
.logo-img:hover{{opacity:1}}
.logo-promoter{{height:64px}}
.logo-hero{{max-width:340px;opacity:1}}
.logo-placeholder{{
  font-family:var(--font-display);font-weight:600;font-size:1rem;
  color:var(--text2);border:2px dashed var(--border);border-radius:10px;
  padding:10px 22px;white-space:nowrap;
  transition:border-color .2s;
}}
.logo-placeholder:hover{{border-color:var(--accent)}}

/* ── header ── */
.hero{{text-align:center;padding:36px 0 12px}}
.hero-logos{{
  display:flex;align-items:center;justify-content:center;
  gap:28px;flex-wrap:wrap;margin-bottom:8px;
}}
.hero h1{{
  font-family:var(--font-display);font-weight:800;
  font-size:clamp(2rem,5.5vw,3.6rem);
  letter-spacing:-.02em;line-height:1.1;
  background:linear-gradient(135deg,var(--accent),var(--accent3),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}}
.hero .tagline{{
  font-family:var(--font-display);font-weight:600;
  font-size:clamp(1rem,2.5vw,1.35rem);
  color:var(--gold);margin-top:14px;
  text-shadow:0 0 30px rgba(255,213,79,.25);
}}
.hero .sub{{color:var(--text2);margin-top:8px;font-size:.95rem;max-width:600px;margin-inline:auto}}
.hero a{{color:var(--accent);text-decoration:none}}
.hero a:hover{{text-decoration:underline}}
.year-badge{{
  display:inline-block;margin-top:16px;
  font-family:var(--font-display);font-weight:700;font-size:1.1rem;
  color:var(--accent);border:2px solid var(--accent);
  padding:4px 18px;border-radius:20px;letter-spacing:.05em;
}}

.divider{{
  height:1px;margin:28px auto 36px;max-width:200px;
  background:linear-gradient(90deg,transparent,var(--accent),transparent);
}}

/* ── card grid ── */
.grid{{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));
  gap:28px;padding-bottom:48px;
}}
@media(min-width:1080px){{
  .grid{{grid-template-columns:repeat(3,1fr)}}
}}

.card{{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--radius);overflow:hidden;cursor:pointer;
  transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;
  outline:none;
}}
.card:hover,.card:focus-visible{{
  transform:translateY(-4px);
  box-shadow:0 12px 40px rgba(0,229,255,.12),0 0 0 1px var(--accent);
  border-color:var(--accent);
}}

.card-img{{
  position:relative;aspect-ratio:1;overflow:hidden;
  background:var(--surface);
}}
.card-img img{{
  width:100%;height:100%;object-fit:cover;
  transition:transform .3s ease;
}}
.card:hover .card-img img{{transform:scale(1.04)}}

.play-icon{{
  position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-size:3rem;color:rgba(255,255,255,.85);
  background:rgba(0,0,0,.15);
  opacity:0;transition:opacity .22s ease;
  text-shadow:0 2px 20px rgba(0,0,0,.6);
}}
.card:hover .play-icon{{opacity:1}}

.dur{{
  position:absolute;bottom:8px;right:10px;
  font-size:.75rem;font-weight:600;color:#fff;
  background:rgba(0,0,0,.55);backdrop-filter:blur(4px);
  padding:2px 8px;border-radius:6px;
}}

.card-body{{padding:16px 18px 18px}}
.card-title{{
  font-family:var(--font-display);font-weight:700;
  font-size:1.1rem;line-height:1.3;color:var(--text);
}}
.card-sub{{color:var(--text2);font-size:.85rem;margin-top:3px}}

.badge{{
  display:inline-block;margin-top:8px;font-size:.75rem;font-weight:700;
  padding:3px 10px;border-radius:20px;letter-spacing:.03em;
}}
.badge.pass{{background:rgba(0,229,120,.15);color:#00e578;border:1px solid rgba(0,229,120,.25)}}
.badge.fail{{background:rgba(255,45,120,.12);color:var(--accent2);border:1px solid rgba(255,45,120,.2)}}

/* ── lightbox ── */
.lightbox{{
  position:fixed;inset:0;z-index:100;
  display:flex;align-items:center;justify-content:center;
  background:rgba(4,5,15,.92);backdrop-filter:blur(12px);
  opacity:0;visibility:hidden;
  transition:opacity .25s ease,visibility .25s ease;
}}
.lightbox.open{{opacity:1;visibility:visible}}

.lightbox-inner{{
  position:relative;width:min(92vw,680px);
  background:var(--surface);border:1px solid var(--border);
  border-radius:18px;overflow:hidden;
  box-shadow:0 32px 80px rgba(0,0,0,.6),0 0 0 1px rgba(0,229,255,.08);
  transform:scale(.95);transition:transform .25s ease;
}}
.lightbox.open .lightbox-inner{{transform:scale(1)}}

.lightbox-close{{
  position:absolute;top:14px;right:14px;z-index:2;
  width:36px;height:36px;border-radius:50%;border:none;
  background:rgba(255,255,255,.1);color:#fff;font-size:1.2rem;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:background .15s;
}}
.lightbox-close:hover{{background:rgba(255,45,120,.35)}}

.lightbox video{{
  display:block;width:100%;aspect-ratio:1;
  background:#000;object-fit:contain;
}}
.lightbox-title{{
  font-family:var(--font-display);font-weight:700;
  font-size:1.15rem;padding:16px 20px;color:var(--text);
}}

/* ── footer ── */
.footer{{
  text-align:center;padding:32px 0 40px;color:var(--text2);
  font-size:.82rem;line-height:1.7;
}}
.footer a{{color:var(--accent);text-decoration:none}}
.footer a:hover{{text-decoration:underline}}

/* ── misc ── */
.sr-only{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
</head>
<body>

<div class="stars" aria-hidden="true"></div>

<div class="page">

  <!-- Logo bar -->
  <nav class="logo-bar" aria-label="Partner logos">
    <div class="logos-left">
      {esa_link}
      {raspberry_link}
    </div>
    <div class="logos-right">
      {promoter_tag}
    </div>
  </nav>

  <!-- Hero -->
  <header class="hero">
    <div class="hero-logos">
      {astropi_tag}
      {mzero_tag}
    </div>
    <h1 class="sr-only">{html.escape(title)}</h1>
    <p class="tagline">{subtitle}</p>
    <p class="sub">{description}</p>
    {year_html}
  </header>

  <div class="divider"></div>

  <!-- Gallery grid -->
  <section class="grid" aria-label="Project gallery">
    {"".join(cards_html)}
  </section>

  <!-- Footer -->
  <footer class="footer">
    <p>European Astro Pi Challenge &mdash; an
      <a href="https://www.esa.int/Education/AstroPI" target="_blank" rel="noopener">ESA Education</a>
      project run with the
      <a href="https://www.raspberrypi.org" target="_blank" rel="noopener">Raspberry Pi Foundation</a>
    </p>
    <p>Videos recorded with <a href="https://github.com/CoderDojoTrento/astropi-gallery" target="_blank" rel="noopener"><strong>astropi-gallery</strong></a></p>
  </footer>
</div>

<!-- Lightbox -->
<div class="lightbox" id="lb" role="dialog" aria-modal="true" aria-label="Video player">
  <div class="lightbox-inner">
    <button class="lightbox-close" id="lb-close" aria-label="Close">&times;</button>
    <video id="lb-video" controls playsinline preload="none"></video>
    <div class="lightbox-title" id="lb-title"></div>
  </div>
</div>

<script>
(function(){{
  var lb=document.getElementById("lb"),
      vid=document.getElementById("lb-video"),
      lbTitle=document.getElementById("lb-title"),
      closeBtn=document.getElementById("lb-close");

  // Open lightbox on card click/enter
  document.querySelector(".grid").addEventListener("click",function(e){{
    var card=e.target.closest(".card");
    if(!card)return;
    openLB(card.dataset.video,card.dataset.name);
  }});
  document.querySelector(".grid").addEventListener("keydown",function(e){{
    if(e.key==="Enter"){{
      var card=e.target.closest(".card");
      if(card)openLB(card.dataset.video,card.dataset.name);
    }}
  }});

  function openLB(src,name){{
    vid.src=src;
    lbTitle.textContent=name;
    lb.classList.add("open");
    document.body.style.overflow="hidden";
    vid.play().catch(function(){{}});
    closeBtn.focus();
  }}

  function closeLB(){{
    lb.classList.remove("open");
    vid.pause();
    vid.removeAttribute("src");
    vid.load();
    document.body.style.overflow="";
  }}

  closeBtn.addEventListener("click",closeLB);
  lb.addEventListener("click",function(e){{
    if(e.target===lb)closeLB();
  }});
  document.addEventListener("keydown",function(e){{
    if(e.key==="Escape"&&lb.classList.contains("open"))closeLB();
  }});
}})();
</script>
</body>
</html>'''

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
