#!/usr/bin/env python3
# =============================================================================
#  DKMA MONSTER  --  Web dashboard generator (stdlib only)
#  Turns data/oem_registry.json into a self-hostable, searchable static site
#  (a dontkillmyapp.com-style guide) so the docs can never drift from the tools.
#
#  Usage:   python3 web/build.py            # writes site into web/site/
#           python3 web/build.py --out DIR
# =============================================================================
import argparse
import html
import json
import os
import re
import shutil
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "..", "data", "oem_registry.json")

# ---- user-facing guidance per step id (the registry stores tech; we add UX) --
STEP_GUIDE = {
    "autostart": ("Enable Autostart",
        "Find this app in the Autostart list and turn its toggle ON. This lets it "
        "start itself in the background \u2014 the single most important setting."),
    "battery_profile": ("Set battery to \u201cNo restrictions\u201d",
        "Change this app's battery mode from \u201cBattery saver\u201d to "
        "\u201cNo restrictions\u201d so the system won't sleep it."),
    "app_details": ("App info \u2192 allow background",
        "Open the app's info page and enable options like \u201cAutostart,\u201d "
        "\u201cKeep running after screen off\u201d and battery \u201cUnrestricted.\u201d"),
    "sleeping_apps": ("Remove from Sleeping apps",
        "Make sure this app is NOT listed under \u201cSleeping apps\u201d or "
        "\u201cDeep sleeping apps.\u201d Remove it if present."),
    "protected_apps": ("Protect the app / App launch",
        "Switch the app to \u201cManage manually,\u201d then enable Auto-launch, "
        "Secondary launch and Run in background."),
    "startup_manager": ("Allow auto-launch",
        "Allow this app to launch automatically in the Startup manager."),
    "startup": ("Allow auto-launch",
        "Allow this app to launch automatically in the Startup manager."),
    "chain": ("Disable deep optimization",
        "Turn off \u201cDeep optimization\u201d / \u201cAdvanced optimization\u201d "
        "for this app."),
    "recent_lock": ("Lock in Recents + don't optimize",
        "Lock the app card in Recent apps, and set Battery optimization to "
        "\u201cDon't optimize.\u201d"),
    "chain_launch": ("Disable deep optimization",
        "Turn off deep/advanced optimization for this app."),
    "stamina": ("Exclude from STAMINA",
        "Add this app to the exceptions of STAMINA / battery-saver mode."),
    "security": ("Allow background from Security",
        "In the Security app, allow this app to keep running in the background."),
    "auto_start": ("Enable auto-start",
        "Allow this app to auto-start via the device's Mobile/Phone Manager."),
    "battery_opt": ("Battery optimization \u2192 Don't optimize",
        "In the battery-optimization list, set this app to \u201cDon't optimize.\u201d"),
}

def guide(step):
    """Prefer the JSON's own hint (single source of truth); fall back to the
    curated STEP_GUIDE copy, then to the raw title."""
    sid = step.get("id", "")
    if step.get("hint"):
        # Use the friendly STEP_GUIDE title if we have one, else the raw title.
        title = STEP_GUIDE.get(sid, (step.get("title", sid), ""))[0]
        return title, step["hint"]
    title, body = STEP_GUIDE.get(sid, (step.get("title", sid),
        "Open this settings screen and allow the app to run in the background."))
    return title, body

# ---- tiny html helpers ------------------------------------------------------
def esc(s): return html.escape(str(s), quote=True)

CSS = """
/* ===== DKMA Monster - Linacre theme (Ink Black + Amber Core/Glow) ===== */
:root{
  --ink:#0b0b0d; --ink2:#111116; --panel:#15151c; --panel2:#1b1b24;
  --line:#26262f; --line2:#33333f;
  --text:#f4f2ee; --muted:#9a9aa6; --dim:#6c6c78;
  --amber:#f5a524; --amber2:#ff8f00; --amber-soft:rgba(245,165,36,.14);
  --glow:0 0 24px rgba(245,165,36,.28); --glow-sm:0 0 12px rgba(245,165,36,.22);
  --ok:#3ddc84; --warn:#f5a524; --err:#ff5c6c;
  --grad:linear-gradient(135deg,#f5a524,#ff8f00);
  --mono:ui-monospace,'SF Mono',SFMono-Regular,'JetBrains Mono',Menlo,Consolas,monospace;
  --sans:'Space Grotesk','Segoe UI',Roboto,system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:var(--sans);background:var(--ink);color:var(--text);line-height:1.6;
  background-image:radial-gradient(1200px 500px at 78% -8%,rgba(245,165,36,.10),transparent 60%),
    radial-gradient(900px 500px at 0% 0%,rgba(245,165,36,.05),transparent 55%);
  background-attachment:fixed;}
a{color:var(--amber);text-decoration:none}a:hover{text-decoration:underline}

/* glassmorphism sticky header */
header.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;padding:14px 26px;
  border-bottom:1px solid var(--line);background:rgba(11,11,13,.72);backdrop-filter:blur(12px) saturate(140%);
  -webkit-backdrop-filter:blur(12px) saturate(140%);}
header.top .logo{width:34px;height:34px;display:grid;place-items:center;font-size:16px;font-weight:800;color:var(--ink);
  background:var(--grad);clip-path:polygon(25% 5%,75% 5%,100% 50%,75% 95%,25% 95%,0% 50%);
  box-shadow:var(--glow-sm);animation:breathe 3.6s ease-in-out infinite}
@keyframes breathe{0%,100%{box-shadow:0 0 10px rgba(245,165,36,.20)}50%{box-shadow:0 0 22px rgba(245,165,36,.45)}}
header.top h1{font-size:16px;margin:0;font-weight:700;letter-spacing:.2px}
header.top h1 a{color:var(--text)}
header.top .tag{margin-left:auto;color:var(--dim);font-size:12px;font-family:var(--mono)}

/* amber pulse-line divider */
.pulse{height:1px;border:0;margin:0;background:linear-gradient(90deg,transparent,var(--amber),transparent);
  opacity:.5;box-shadow:0 0 8px rgba(245,165,36,.4)}

.wrap{max-width:1060px;margin:0 auto;padding:30px 26px 10px}

/* hex-grid hero */
.hero{position:relative;padding:26px 0 26px;overflow:hidden}
.hero::before{content:"";position:absolute;inset:-40px -20px auto auto;width:280px;height:220px;opacity:.5;
  background-image:
   linear-gradient(60deg,transparent 46%,rgba(245,165,36,.16) 47%,rgba(245,165,36,.16) 53%,transparent 54%),
   linear-gradient(-60deg,transparent 46%,rgba(245,165,36,.16) 47%,rgba(245,165,36,.16) 53%,transparent 54%);
  background-size:26px 46px;-webkit-mask-image:radial-gradient(circle at 70% 30%,#000,transparent 70%);
  mask-image:radial-gradient(circle at 70% 30%,#000,transparent 70%);pointer-events:none}
.kicker{font-family:var(--mono);font-size:12px;color:var(--amber);letter-spacing:.12em;text-transform:uppercase;
  display:inline-flex;align-items:center;gap:8px;margin-bottom:12px}
.kicker::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--amber);box-shadow:var(--glow-sm);
  animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.hero h2{font-size:34px;line-height:1.12;margin:0 0 12px;font-weight:700;letter-spacing:-.02em}
.hero h2 .amber{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--muted);max-width:66ch;font-size:15.5px}

/* terminal prompt line */
.term{font-family:var(--mono);font-size:13px;background:var(--ink2);border:1px solid var(--line);border-radius:12px;
  padding:12px 14px;margin:16px 0 0;color:var(--muted);box-shadow:inset 0 0 0 1px rgba(255,255,255,.02)}
.term .p{color:var(--amber)} .term .c{color:var(--dim)}

.search{width:100%;padding:14px 16px;background:var(--panel2);color:var(--text);border:1px solid var(--line);
  border-radius:12px;font-size:16px;margin:14px 0 24px;font-family:var(--mono);transition:.15s}
.search:focus{outline:none;border-color:var(--amber);box-shadow:var(--glow-sm)}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.card{display:block;position:relative;background:linear-gradient(180deg,var(--panel),var(--ink2));
  border:1px solid var(--line);border-radius:16px;padding:18px;transition:.18s;overflow:hidden}
.card::after{content:"";position:absolute;inset:0;border-radius:16px;padding:1px;background:transparent;pointer-events:none;transition:.18s}
.card:hover{transform:translateY(-3px);border-color:var(--amber);box-shadow:var(--glow);text-decoration:none}
.card .name{font-weight:700;font-size:16px;color:var(--text)}
.card .meta{color:var(--muted);font-size:12.5px;margin-top:6px}
.badge{display:inline-block;background:var(--amber-soft);border:1px solid rgba(245,165,36,.35);border-radius:999px;
  padding:3px 11px;font-size:11.5px;color:var(--amber);margin-top:12px;font-family:var(--mono)}

.crumb{color:var(--muted);font-size:13px;margin-bottom:6px;font-family:var(--mono)}
.severity{display:flex;gap:10px;align-items:center;background:var(--amber-soft);
  border:1px solid rgba(245,165,36,.4);color:#ffe0a8;border-radius:12px;padding:11px 14px;font-size:13.5px;margin:8px 0 22px}

.step{background:linear-gradient(180deg,var(--panel),var(--ink2));border:1px solid var(--line);border-radius:16px;
  padding:20px;margin-bottom:14px;transition:.15s}
.step:hover{border-color:var(--line2)}
.step .head{display:flex;gap:14px;align-items:flex-start}
.step .n{width:34px;height:34px;flex:0 0 auto;display:grid;place-items:center;font-weight:800;color:var(--ink);
  background:var(--grad);box-shadow:var(--glow-sm);
  clip-path:polygon(25% 5%,75% 5%,100% 50%,75% 95%,25% 95%,0% 50%)}
.step h3{margin:0;font-size:17px;font-weight:700}
.step p{margin:8px 0 0;color:var(--text)}
.step .why{color:var(--muted);font-size:13.5px}
details{margin-top:14px;border-top:1px dashed var(--line);padding-top:12px}
summary{cursor:pointer;color:var(--amber);font-size:13px;font-family:var(--mono)}
code,.mono{font-family:var(--mono);font-size:12.5px;background:var(--ink2);border:1px solid var(--line);
  border-radius:6px;padding:2px 7px;color:#ffd591;display:inline-block;margin:3px 0}

.callout{background:var(--ink2);border:1px solid var(--line);border-left:3px solid var(--amber);
  border-radius:0 14px 14px 0;padding:16px 18px;margin:20px 0;color:var(--muted);font-size:14px;box-shadow:var(--glow-sm)}
.callout b{color:var(--text)}
.tools{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px}
.tool{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:13px}
.tool b{color:var(--amber)}

footer{border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;padding:26px;text-align:center;line-height:1.8;margin-top:20px}
footer a{color:var(--amber)}
.top3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:18px 0 22px}
@media(max-width:680px){.top3{grid-template-columns:1fr}.hero h2{font-size:27px}}
.top3 .t{background:linear-gradient(180deg,var(--panel),var(--ink2));border:1px solid var(--line);border-radius:14px;padding:16px;transition:.15s}
.top3 .t:hover{border-color:var(--amber);box-shadow:var(--glow-sm)}
.top3 .t b{display:block;color:var(--amber);margin-bottom:4px;font-family:var(--mono);font-size:13px}
.pillrow{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.pill{background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:3px 11px;font-size:12px;color:var(--muted);font-family:var(--mono)}
"""

def page(title, body, rel=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="DKMA Monster - stop aggressive OEM battery managers from killing your Android apps. Per-brand keep-alive guides plus automation tools.">
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head><body>
<header class="top">
  <span class="logo">DK</span>
  <h1><a href="{rel}index.html">DKMA Monster</a></h1>
  <span class="tag">amber \u00b7 hexagon \u00b7 pulse</span>
</header>
<hr class="pulse">
{body}
<hr class="pulse">
<footer>
  Generated from <code>data/oem_registry.json</code> \u2014 the single source the
  ADB installer, desktop GUI, root script, Magisk module and in-app library share,
  so it can never drift.<br>
  Knowledge distilled from the community at dontkillmyapp.com \u00b7 Built {date.today().isoformat()}.<br>
  <strong>Built by David Linacre</strong> \u00b7 <a href="https://www.linacre.site/">linacre.site</a>
</footer>
</body></html>"""

# ---- index page -------------------------------------------------------------
def build_index(reg):
    cards = []
    for o in reg["oems"]:
        nsteps = len(o["steps"])
        brands = ", ".join(sorted(set(o["match"].get("brand", []) or
                                      o["match"].get("manufacturer", []))))
        cards.append(f"""
        <a class="card" href="oem/{esc(o['id'])}.html" data-name="{esc(o['label'].lower())} {esc(brands.lower())}">
          <div class="name">{esc(o['label'])}</div>
          <div class="meta">{esc(brands.title())}</div>
          <span class="badge">{nsteps} step{'s' if nsteps!=1 else ''}</span>
        </a>""")
    body = f"""
    <div class="wrap">
      <div class="hero">
        <div class="kicker">Don't kill my app</div>
        <h2>Stop your phone from <span class="amber">killing your apps</span></h2>
        <p>Aggressive, undocumented OEM battery managers silently kill background
        apps on many Android phones. Pick your brand for exact, tested steps \u2014 or
        automate it all with the DKMA Monster CLI, desktop GUI, or root/Magisk tools.</p>
        <div class="term"><span class="p">$</span> dkma <span class="c"># detect \u00b7 grant \u00b7 guide \u00b7 verify</span></div>
      </div>
      <div class="top3">
        <div class="t"><b>01 / Autostart ON</b>Let the app start in the background.</div>
        <div class="t"><b>02 / Battery Unrestricted</b>No battery-saver limits.</div>
        <div class="t"><b>03 / Keep running</b>Don't stop after screen off.</div>
      </div>
      <input class="search" id="q" placeholder="/ search your brand (Xiaomi, Samsung, OPPO\u2026)"
             oninput="filter()" autofocus>
      <div class="grid" id="grid">{''.join(cards)}</div>
      <div class="callout">
        <b>Prefer to automate?</b> Run <code>python3 adb/dkma.py com.your.app</code>
        (or the desktop GUI <code>python3 gui/server.py</code>) to grant everything
        possible over ADB and open each screen for you. Root users get full
        automation via <code>root/dkma-root.sh</code> and the Magisk module.
      </div>
    </div>
    <script>
    function filter(){{
      var v=document.getElementById('q').value.toLowerCase();
      document.querySelectorAll('#grid .card').forEach(function(c){{
        c.style.display = c.getAttribute('data-name').indexOf(v)>-1 ? '' : 'none';
      }});
    }}
    document.addEventListener('keydown',function(e){{
      if(e.key==='/' && document.activeElement.id!=='q'){{
        e.preventDefault(); document.getElementById('q').focus();
      }}
    }});
    </script>"""
    return page("DKMA Monster \u2014 Keep your Android apps alive", body)

# ---- per-OEM page -----------------------------------------------------------
def component_pretty(comp):
    # "pkg/activity" -> readable
    if "/" in comp:
        pkg, act = comp.split("/", 1)
        return pkg, act
    return comp, ""

def build_oem(reg, o):
    steps_html = []
    for i, s in enumerate(o["steps"], 1):
        title, why = guide(s)
        comps = s.get("components", [])
        used = s.get("use")
        adv = ""
        if comps:
            rows = "".join(
                f"<div><code>{esc(c)}</code></div>" for c in comps)
            adv = f"""<details><summary>Developer: settings screen(s) opened</summary>
                     <div style="margin-top:8px">{rows}
                     <div class="why" style="margin-top:6px">The tools try these in
                     order and fall back to the app's info page.</div></div></details>"""
        elif used:
            adv = f"""<details><summary>Developer: intent used</summary>
                     <div style="margin-top:8px"><code>{esc(used)}</code></div></details>"""
        steps_html.append(f"""
        <div class="step">
          <div class="head"><div class="n">{i}</div>
            <div><h3>{esc(title)}</h3>
            <p class="why">{esc(why)}</p></div>
          </div>
          {adv}
        </div>""")

    brands = ", ".join(sorted(set(
        (o["match"].get("brand", []) + o["match"].get("manufacturer", [])))))
    pills = "".join(f'<span class="pill">{esc(b)}</span>' for b in
                    sorted(set(o["match"].get("brand", []) +
                               o["match"].get("manufacturer", []))))
    body = f"""
    <div class="wrap">
      <div class="crumb"><a href="../index.html">\u2190 All brands</a></div>
      <div class="hero">
        <div class="kicker">Keep-alive guide</div>
        <h2>{esc(o['label'])}</h2>
        <div class="pillrow">{pills}</div>
      </div>
      <div class="severity">\u26a0\ufe0f These settings have no public API \u2014 you set
        them once by hand (or fully automate with root). It takes about a minute.</div>

      {''.join(steps_html)}

      <div class="callout">
        <b>Automate this brand:</b><br>
        <div class="tools">
          <div class="tool"><b>CLI:</b> <code>python3 adb/dkma.py com.your.app</code></div>
          <div class="tool"><b>GUI:</b> <code>python3 gui/server.py</code></div>
          <div class="tool"><b>Root:</b> <code>sh root/dkma-root.sh com.your.app</code></div>
        </div>
        The CLI/GUI grant Doze whitelist, standby bucket and background appops
        automatically, then open each screen above for you to confirm.
      </div>
    </div>"""
    return page(f"{o['label']} \u2014 keep apps alive | DKMA Monster", body, rel="../")

# ---- driver -----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "site"))
    args = ap.parse_args()

    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)

    out = args.out
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "oem"), exist_ok=True)

    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(reg))

    for o in reg["oems"]:
        with open(os.path.join(out, "oem", f"{o['id']}.html"), "w",
                  encoding="utf-8") as f:
            f.write(build_oem(reg, o))

    n = len(reg["oems"])
    print(f"Built site into {out}/  ({n} brand pages + index)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
