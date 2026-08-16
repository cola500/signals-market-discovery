# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "flask",
#     "supabase==2.31.0",
#     "python-dotenv",
# ]
# ///
"""Signals - market discovery for job search.

Kör lokalt: uv run app.py
Kräver en .env-fil med SUPABASE_URL, SUPABASE_ANON_KEY, FLASK_SECRET_KEY
(se .env.example). Data lagras i Supabase Postgres (schema "signals"),
inte lokalt - appen fungerar likadant lokalt och i produktion.
"""
import os
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    g,
    get_flashed_messages,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    session,
    url_for,
)
from supabase import Client, ClientOptions, create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
_CLIENT_OPTIONS = ClientOptions(schema="signals")

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)


def get_supabase() -> Client:
    """Per-request Supabase client, scoped to the logged-in user's session.

    RLS policies (user_id = auth.uid()) are the real access boundary - this
    client always carries the current user's access token, never a
    privileged key, so a query can only ever see that user's own rows.
    """
    if "db" not in g:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=_CLIENT_OPTIONS)
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        if access_token and refresh_token:
            auth_response = client.auth.set_session(access_token, refresh_token)
            session["access_token"] = auth_response.session.access_token
            session["refresh_token"] = auth_response.session.refresh_token
            g.user = auth_response.user
        g.db = client
    return g.db


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("access_token"):
            return redirect(url_for("login", next=request.path))
        try:
            get_supabase()
        except Exception:
            session.clear()
            return redirect(url_for("login", next=request.path))
        if not getattr(g, "user", None):
            session.clear()
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{
  --ink-950:#1C1712;--ink-600:#5C5346;--ink-400:#8A8072;--ink-200:#C9C0B2;--ink-100:#E8E1D4;--ink-50:#F5F0E6;
  --cream-50:#FFF9F0;--white:#fff;
  --coral-500:#FF6A47;--coral-600:#F04F28;--coral-700:#C93B18;
  --teal-100:#D9F1EC;--teal-700:#1E6A5F;
  --rose-100:#FBE3E8;--rose-text:#9C2B45;
  --success-500:#2E9E5B;--danger-500:#D8365A;
  --radius-md:10px;--radius-lg:16px;--radius-full:999px;
  --shadow-sm:0 1px 2px rgba(28,23,18,.06);
  --shadow-md:0 4px 12px rgba(28,23,18,.08);
  --ease:cubic-bezier(.2,.8,.2,1);
}
*{box-sizing:border-box}
body{font-family:'Manrope',system-ui,sans-serif;max-width:640px;margin:0 auto;padding:1rem 1rem 5rem;color:var(--ink-950);background:var(--cream-50);line-height:1.55}
h1{font-weight:700;font-size:1.75rem;margin:1rem 0 1rem}
h2{font-weight:700;font-size:1.15rem;margin:1.75rem 0 .75rem;color:var(--ink-950)}
a{color:var(--coral-600);font-weight:600;text-decoration:none;transition:color .12s var(--ease)}
a:visited{color:var(--coral-600)}
a:hover{color:var(--coral-700);text-decoration:underline}
nav{position:fixed;left:0;right:0;bottom:0;display:flex;align-items:stretch;gap:2px;background:var(--white);border-top:1px solid var(--ink-100);box-shadow:var(--shadow-md);padding:.4rem .5rem calc(.4rem + env(safe-area-inset-bottom));z-index:10}
nav a,nav a:visited{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.2rem;padding:.3rem .2rem;color:var(--ink-600);font-weight:600;font-size:.7rem;text-decoration:none;border-radius:var(--radius-md);transition:color .12s var(--ease)}
nav a:hover{color:var(--coral-600)}
nav a svg{width:20px;height:20px;flex-shrink:0}
nav form{display:flex;flex:1}
nav button{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.2rem;padding:.3rem .2rem;min-height:auto;font-size:.7rem;background:none;border:none;color:var(--ink-400);font-weight:600}
nav button:hover{color:var(--ink-950)}
nav button svg{width:20px;height:20px;flex-shrink:0}
form label{display:block;margin-bottom:1rem;font-weight:600;font-size:.875rem;color:var(--ink-950)}
input,select,textarea{width:100%;padding:.7rem .85rem;box-sizing:border-box;font-size:1rem;font-family:inherit;border:1px solid var(--ink-200);border-radius:var(--radius-md);background:var(--white);margin-top:.4rem;transition:border-color .12s var(--ease),box-shadow .12s var(--ease)}
input[type="date"]{-webkit-appearance:none;appearance:none}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--coral-500);box-shadow:0 0 0 3px rgba(255,106,71,.25)}
textarea{min-height:6rem;resize:vertical}
button{padding:.75rem 1.25rem;font-size:1rem;font-family:inherit;font-weight:700;border-radius:var(--radius-md);min-height:44px;border:1px solid var(--ink-200);background:var(--ink-50);color:var(--ink-950);cursor:pointer;transition:background .12s var(--ease),transform .12s var(--ease)}
button:hover{background:var(--ink-100)}
button:active{transform:scale(.97)}
.btn-primary{width:100%;margin-top:.5rem;background:var(--coral-500);border:none;color:#fff}
.btn-primary:hover{background:var(--coral-600)}
.btn-primary:active{background:var(--coral-700);transform:scale(.97)}
.btn-danger{background:var(--danger-500);border:none;color:#fff}
.btn-danger:hover{background:#B5294A}
.actions-row{display:flex;gap:.6rem;margin-bottom:1rem}
.actions-row form{margin:0;flex:1;display:flex}
.actions-row button{flex:1;text-align:center;justify-content:center}
.actions-row a{flex:1;display:flex;align-items:center;justify-content:center;text-align:center;padding:.75rem 1rem;font-size:1rem;font-weight:700;border-radius:var(--radius-md);min-height:44px;border:1px solid var(--ink-200);background:var(--ink-50);color:var(--ink-950);text-decoration:none;transition:background .12s var(--ease),transform .12s var(--ease)}
.actions-row a:visited{color:var(--ink-950)}
.actions-row a:hover{background:var(--ink-100);text-decoration:none}
.actions-row a:active{transform:scale(.97)}
.actions-row .btn-accent{background:var(--coral-500);border:none;color:#fff}
.actions-row .btn-accent:hover{background:var(--coral-600)}
.status-row{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem}
.status-row .btn-accent{background:var(--coral-500);border:none;color:#fff}
.status-row .btn-accent:hover{background:var(--coral-600)}
fieldset{margin-bottom:1rem;border:1px solid var(--ink-100);border-radius:var(--radius-md);background:var(--ink-50);padding:1rem}
details{margin-bottom:1rem;border:1px solid var(--ink-100);border-radius:var(--radius-md);background:var(--ink-50);padding:1rem}
details summary{font-weight:700;font-size:.875rem;cursor:pointer;list-style:none;display:flex;align-items:center;gap:.4rem}
details summary::-webkit-details-marker{display:none}
details summary::before{content:'▸';display:inline-block;transition:transform .12s var(--ease)}
details[open] summary::before{transform:rotate(90deg)}
details[open] summary{margin-bottom:.5rem}
details label:last-child{margin-bottom:0}
.suggestions{list-style:none;margin:.3rem 0 0;padding:0;background:var(--white);border:1px solid var(--ink-200);border-radius:var(--radius-md);box-shadow:var(--shadow-md);max-height:12rem;overflow-y:auto}
.suggestions:empty{display:none;margin:0;border:none;box-shadow:none}
.suggestions li{padding:.75rem .85rem;font-size:1rem;font-weight:500;cursor:pointer}
.suggestions li:active{background:var(--ink-50)}
.suggestions li[aria-selected="true"]{background:var(--ink-100)}
.suggestions li+li{border-top:1px solid var(--ink-100)}
legend{font-weight:700;font-size:.875rem;padding:0 .3rem}
.feed{list-style:none;padding:0;display:flex;flex-direction:column;gap:1rem}
.feed-controls{margin-bottom:1rem}
#feed-search{margin-bottom:.6rem}
.chip-row{display:flex;flex-wrap:wrap;gap:.4rem}
.chip{padding:.35rem .8rem;font-size:.8rem;font-weight:600;border-radius:var(--radius-full);border:1px solid var(--ink-200);background:var(--white);color:var(--ink-600);min-height:auto}
.chip.active{background:var(--coral-500);border-color:var(--coral-500);color:#fff}
.feed-empty{color:var(--ink-400);font-size:.9rem;margin-top:.6rem}
.note-preview{margin:.75rem 0}
.card-details{margin-bottom:.5rem}
.card-toggle{background:none;border:none;color:var(--coral-600);font-weight:700;padding:.4rem 0;min-height:auto}
.card-toggle:hover{color:var(--coral-700);background:none}
.feed li{border:1px solid var(--ink-100);border-radius:var(--radius-lg);background:var(--white);box-shadow:var(--shadow-sm);padding:1.25rem}
.badge{display:inline-block;background:var(--ink-100);color:var(--ink-600);border-radius:var(--radius-full);padding:.15rem .65rem;font-size:.8rem;font-weight:700;margin-right:.3rem}
.vote-row{display:flex;align-items:center;gap:.5rem;margin-top:.75rem}
.vote-row form{margin:0}
.vote-row button{padding:.4rem .9rem;min-height:auto}
.vote-row .badge{margin:0;font-family:'JetBrains Mono',monospace}
.tag{display:inline-block;border-radius:var(--radius-full);padding:.2rem .7rem;font-size:.8rem;font-weight:600;margin-right:.35rem}
.tag.problem{background:var(--rose-100);color:var(--rose-text)}
.tag.role{background:var(--teal-100);color:var(--teal-700)}
.hyp{display:block;font-size:.85rem;font-weight:600;margin-top:.4rem}
.hyp.supports{color:var(--success-500)}
.hyp.contradicts{color:var(--danger-500)}
.next-action.done{text-decoration:line-through;color:var(--ink-400)}
.error{color:var(--rose-text);background:var(--rose-100);padding:.75rem 1rem;border-radius:var(--radius-md);border-left:3px solid var(--danger-500);display:block;margin-bottom:1rem}
.toast{background:var(--success-500);color:#fff;font-weight:700;padding:.75rem 1rem;border-radius:var(--radius-md);margin-bottom:1rem;overflow:hidden;animation:toast-fade 3s ease-out forwards}
.insight-note{background:var(--teal-100);color:var(--teal-700);border-radius:var(--radius-md);padding:.75rem 1rem;margin-bottom:1rem;font-weight:500}
.insight-note p{margin:0}
.insight-note p+p{margin-top:.35rem}
@keyframes toast-fade{0%,70%{opacity:1;max-height:4rem;margin-bottom:1rem;padding:.75rem 1rem}100%{opacity:0;max-height:0;margin-bottom:0;padding:0 1rem}}
#splash{position:fixed;inset:0;background:var(--coral-500);display:flex;align-items:center;justify-content:center;z-index:100;transition:opacity .4s ease-out}
#splash img{width:88px;height:88px;border-radius:20px}
#ptr{position:fixed;top:0;left:50%;width:36px;height:36px;margin-left:-18px;border-radius:50%;background:var(--white);box-shadow:var(--shadow-md);display:flex;align-items:center;justify-content:center;z-index:20;opacity:0;transform:translateY(calc(-100% + var(--pull, 0px)));pointer-events:none}
#ptr.show{transition:none}
#ptr:not(.show){transition:transform .2s var(--ease),opacity .2s var(--ease)}
#ptr.show,#ptr.loading{opacity:1}
#ptr.loading{transform:translateY(14px)}
#ptr svg{width:18px;height:18px;color:var(--ink-400);transition:transform .15s var(--ease),color .15s var(--ease)}
#ptr.ready svg.ptr-arrow{color:var(--coral-500);transform:rotate(180deg)}
#ptr .ptr-spinner{display:none;color:var(--coral-500)}
#ptr.loading svg.ptr-arrow{display:none}
#ptr.loading svg.ptr-spinner{display:block;animation:ptr-spin .7s linear infinite}
@keyframes ptr-spin{to{transform:rotate(360deg)}}
</style>
"""

NAV = """
<nav>
  {% if session.get('access_token') %}
    <a href="{{ url_for('feed') }}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg><span>Flöde</span></a>
    <a href="/signals/new"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg><span>+ Ny signal</span></a>
    <a href="/hypotheses"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M12 2a7 7 0 0 0-4 12.7 3 3 0 0 1 1 2.3h6a3 3 0 0 1 1-2.3A7 7 0 0 0 12 2z"></path></svg><span>Hypoteser</span></a>
    <a href="/review"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg><span>Översikt</span></a>
    <form method="post" action="{{ url_for('logout') }}"><button type="submit"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg><span>Logga ut</span></button></form>
  {% else %}
    <a href="{{ url_for('login') }}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg><span>Logga in</span></a>
  {% endif %}
</nav>
"""


HEAD_EXTRAS = """
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Signals">
<meta name="theme-color" content="#FF6A47">
<link rel="apple-touch-icon" href="/app-icon.svg">
<link rel="icon" href="/app-icon.svg">
"""

SPLASH = """
<div id="splash"><img src="/app-icon.svg"></div>
<script>
if (sessionStorage.getItem('signals_splash_shown')) {
  document.getElementById('splash').remove();
} else {
  sessionStorage.setItem('signals_splash_shown', '1');
  window.addEventListener('load', () => {
    setTimeout(() => {
      const s = document.getElementById('splash');
      if (s) { s.style.opacity = '0'; setTimeout(() => s.remove(), 400); }
    }, 400);
  });
}
</script>
"""


PULL_TO_REFRESH = """
<div id="ptr" aria-hidden="true">
  <svg class="ptr-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
  <svg class="ptr-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-9-9"></path></svg>
</div>
<script>
(function () {
  var ptr = document.getElementById('ptr');
  var threshold = 70;
  var startY = null;
  var pulling = false;
  var loading = false;

  function setPull(px) {
    ptr.style.setProperty('--pull', px + 'px');
  }

  document.addEventListener('touchstart', function (e) {
    if (loading) return;
    var target = e.target.closest('input, textarea, select');
    if (target || window.scrollY > 0) {
      startY = null;
      pulling = false;
      return;
    }
    startY = e.touches[0].clientY;
    pulling = true;
  }, { passive: true });

  var deadZone = 12;

  document.addEventListener('touchmove', function (e) {
    if (!pulling || startY === null || loading) return;
    var dy = e.touches[0].clientY - startY;
    if (dy <= 0 || window.scrollY > 0) {
      ptr.classList.remove('show', 'ready');
      setPull(0);
      return;
    }
    if (dy < deadZone) return;
    e.preventDefault();
    var dist = Math.min((dy - deadZone) * 0.5, 100);
    setPull(dist);
    ptr.classList.add('show');
    ptr.classList.toggle('ready', dist >= threshold);
  }, { passive: false });

  document.addEventListener('touchend', function () {
    if (!pulling) return;
    pulling = false;
    var ready = ptr.classList.contains('ready');
    if (ready) {
      loading = true;
      ptr.classList.remove('show', 'ready');
      ptr.classList.add('loading');
      location.reload();
    } else {
      ptr.classList.remove('show', 'ready');
      setPull(0);
    }
    startY = null;
  }, { passive: true });
})();
</script>
"""


def page(title, body_template):
    return (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"{HEAD_EXTRAS}"
        f"<title>{title}</title>{STYLE}</head><body>{SPLASH}{PULL_TO_REFRESH}{NAV}{body_template}</body></html>"
    )


PUBLIC_DIR = Path(__file__).parent / "public"


@app.route("/app-icon.svg")
def app_icon():
    # On Vercel, files under public/** are served directly by the platform
    # and this route is never hit. Locally (uv run app.py) there is no such
    # layer, so Flask serves the same file itself - same pattern Vercel's
    # own docs use for /favicon.ico.
    return send_from_directory(PUBLIC_DIR, "app-icon.svg", mimetype="image/svg+xml")


LOGIN_TEMPLATE = """
<h1>Logga in</h1>
<p style="margin:-0.5rem 0 1.5rem;color:var(--ink-600);font-size:0.9rem">Logga signaler från din jobbsökning — kaffemöten, rekryterarkontakt, intervjuer — och se vilka hypoteser de stödjer eller motsäger.</p>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post">
  <label>E-post<input type="email" name="email" required autofocus></label>
  <label>Lösenord<input type="password" name="password" required></label>
  <button type="submit" class="btn-primary">Logga in</button>
</form>
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=_CLIENT_OPTIONS)
        try:
            auth_response = client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception:
            return render_template_string(
                page("Logga in", LOGIN_TEMPLATE), error="Fel e-post eller lösenord."
            )
        session.permanent = True
        session["access_token"] = auth_response.session.access_token
        session["refresh_token"] = auth_response.session.refresh_token
        next_url = request.args.get("next") or url_for("feed")
        return redirect(next_url)

    return render_template_string(page("Logga in", LOGIN_TEMPLATE), error=None)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


SIGNAL_TYPE_SEED = [
    "kaffe", "lunch", "rekryterarkontakt", "linkedin-meddelande", "jobbannons",
    "intervju", "introduktion", "samtal", "avslag", "konsultuppdrag", "rollförslag",
]
CHANNEL_SEED = [
    "befintlig relation", "introduktion", "rekryterare", "linkedin", "ansökan", "tidigare kollega",
]


def parse_tag_list(raw):
    return [t.strip() for t in raw.split(",") if t.strip()]


def get_or_create_tag(db, user_id, text, category):
    text = text.strip().lower()
    existing = (
        db.table("tags")
        .select("id")
        .eq("user_id", user_id)
        .eq("text", text)
        .eq("category", category)
        .execute()
        .data
    )
    if existing:
        return existing[0]["id"]
    created = (
        db.table("tags")
        .insert({"user_id": user_id, "text": text, "category": category})
        .select()
        .execute()
        .data
    )
    return created[0]["id"]


def distinct_values(db, user_id, column, seed):
    rows = db.table("signals").select(column).eq("user_id", user_id).execute().data
    values = {r[column] for r in rows if r.get(column)}
    values.update(seed)
    return sorted(values)


def distinct_tag_values(db, user_id, category):
    rows = (
        db.table("tags")
        .select("text")
        .eq("user_id", user_id)
        .eq("category", category)
        .execute()
        .data
    )
    return sorted({r["text"] for r in rows})


def recent_distinct_values(db, user_id, column):
    rows = (
        db.table("signals")
        .select(f"{column}, date")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .execute()
        .data
    )
    seen = set()
    values = []
    for r in rows:
        value = r.get(column)
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def set_signal_tags(db, user_id, signal_id, category, raw_text):
    tag_ids_in_category = [
        t["id"]
        for t in db.table("tags").select("id").eq("user_id", user_id).eq("category", category).execute().data
    ]
    if tag_ids_in_category:
        db.table("signal_tags").delete().eq("signal_id", signal_id).in_("tag_id", tag_ids_in_category).execute()
    for text in parse_tag_list(raw_text):
        tag_id = get_or_create_tag(db, user_id, text, category)
        db.table("signal_tags").upsert(
            {"signal_id": signal_id, "tag_id": tag_id, "user_id": user_id},
            on_conflict="signal_id,tag_id",
        ).execute()


def set_signal_hypothesis(db, user_id, signal_id, form):
    db.table("signal_hypotheses").delete().eq("signal_id", signal_id).execute()
    relation = form.get("relation")
    new_hyp_statement = form.get("new_hypothesis", "").strip()
    hypothesis_id = None
    if new_hyp_statement:
        existing_hyp = (
            db.table("hypotheses")
            .select("id")
            .eq("user_id", user_id)
            .eq("statement", new_hyp_statement)
            .execute()
            .data
        )
        if existing_hyp:
            hypothesis_id = existing_hyp[0]["id"]
        else:
            created = (
                db.table("hypotheses")
                .insert({"user_id": user_id, "statement": new_hyp_statement, "status": "exploring"})
                .select()
                .execute()
                .data
            )
            hypothesis_id = created[0]["id"]

    if hypothesis_id and relation:
        db.table("signal_hypotheses").insert(
            {"signal_id": signal_id, "hypothesis_id": hypothesis_id, "user_id": user_id, "relation": relation}
        ).execute()
        return hypothesis_id, relation
    return None, None


def build_learning_feedback(db, user_id, hypothesis_id, relation, problem_tags_raw):
    """Short, evidence-based feedback lines about what this save changed.

    Pure counts over the user's own data - no inference beyond what's
    directly observable, per the "no invented insights" requirement.
    """
    lines = []

    if hypothesis_id and relation:
        hyp_rows = db.table("hypotheses").select("statement").eq("id", hypothesis_id).execute().data
        statement = hyp_rows[0]["statement"] if hyp_rows else ""
        evidence_count = len(
            db.table("signal_hypotheses")
            .select("signal_id")
            .eq("hypothesis_id", hypothesis_id)
            .eq("relation", relation)
            .execute()
            .data
        )
        verb = "stödjande" if relation == "supports" else "motsägande"
        if evidence_count <= 1:
            lines.append(f"Hypotesen “{statement}” fick sin första {verb} signal.")
        else:
            lines.append(f"Hypotesen “{statement}” fick ytterligare en {verb} signal ({evidence_count} totalt).")
    else:
        lines.append("Ingen hypotes kopplad till den här signalen än.")

    problem_texts = {t.strip().lower() for t in parse_tag_list(problem_tags_raw)}
    tag_counts = {}
    for text in problem_texts:
        tag_rows = (
            db.table("tags").select("id").eq("user_id", user_id).eq("text", text).eq("category", "problem").execute().data
        )
        if not tag_rows:
            continue
        n = len(db.table("signal_tags").select("signal_id").eq("tag_id", tag_rows[0]["id"]).execute().data)
        tag_counts[text] = n
    if tag_counts:
        top_text, top_count = max(tag_counts.items(), key=lambda kv: kv[1])
        if top_count >= 2:
            lines.append(f"Problemet “{top_text}” har nu dykt upp {top_count} gånger.")

    return lines


SIGNAL_FORM_TEMPLATE = """
<h1>{{ heading }}</h1>
<form method="post" action="{{ form_action }}">
  <fieldset>
    <legend>Vem &amp; när</legend>
    <label>Datum *<input type="date" name="date" value="{{ date_value }}" required></label>
    <label>Person *
      <div class="autocomplete-field">
        <input type="text" name="person" id="person" value="{{ person_value }}" autocomplete="off" required>
        <ul class="suggestions" id="person-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label>Organisation
      <div class="autocomplete-field">
        <input type="text" name="organization" id="organization" value="{{ organization_value }}" autocomplete="off">
        <ul class="suggestions" id="organization-suggestions" role="listbox"></ul>
      </div>
    </label>
  </fieldset>

  <fieldset>
    <legend>Vad hände</legend>
    <label>Signal-typ *
      <div class="autocomplete-field">
        <input type="text" name="signal_type" id="signal_type" value="{{ signal_type_value }}" autocomplete="off" required>
        <ul class="suggestions" id="signal_type-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label>Roll/möjlighet (valfritt)
      <div class="autocomplete-field">
        <input type="text" name="role_opportunity" id="role_opportunity" value="{{ role_opportunity_value }}" autocomplete="off">
        <ul class="suggestions" id="role_opportunity-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label>Kanal (valfritt)
      <div class="autocomplete-field">
        <input type="text" name="channel" id="channel" value="{{ channel_value }}" autocomplete="off">
        <ul class="suggestions" id="channel-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label>Vad hände? *<textarea name="note" required>{{ note_value }}</textarea></label>
  </fieldset>

  <details {% if learning_value or problem_heard_value or interest_signal_value %}open{% endif %}>
    <summary>Reflektion (valfritt)</summary>
    <label>Vad lärde jag mig?<textarea name="learning">{{ learning_value }}</textarea></label>
    <label>Vilket problem/behov hörde jag?<textarea name="problem_heard">{{ problem_heard_value }}</textarea></label>
    <label>Vad skapade intresse för min bakgrund?<textarea name="interest_signal">{{ interest_signal_value }}</textarea></label>
  </details>

  <fieldset>
    <legend>Taggar &amp; hypotes</legend>
    <label>Problem-taggar (kommaseparerat)
      <div class="autocomplete-field">
        <input type="text" name="problem_tags" id="problem_tags" value="{{ problem_tags_value }}" autocomplete="off">
        <ul class="suggestions" id="problem_tags-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label>Roll-taggar (kommaseparerat)
      <div class="autocomplete-field">
        <input type="text" name="role_tags" id="role_tags" value="{{ role_tags_value }}" autocomplete="off">
        <ul class="suggestions" id="role_tags-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label>Hypotes (valfritt)
      <div class="autocomplete-field">
        <input type="text" name="new_hypothesis" id="new_hypothesis" value="{{ hypothesis_value }}" autocomplete="off">
        <ul class="suggestions" id="hypothesis-suggestions" role="listbox"></ul>
      </div>
    </label>
    <label id="relation-label">Relation
      <select name="relation">
        <option value="supports" {% if relation_value == 'supports' %}selected{% endif %}>Stödjer</option>
        <option value="contradicts" {% if relation_value == 'contradicts' %}selected{% endif %}>Motsäger</option>
      </select>
    </label>
  </fieldset>

  <label>Nästa steg (valfritt)<input type="text" name="next_action" value="{{ next_action_value }}"></label>

  <button type="submit" class="btn-primary">{{ submit_label }}</button>
</form>
<script>
function updateRelationVisibility() {
  var newHyp = document.getElementById('new_hypothesis');
  var relationLabel = document.getElementById('relation-label');
  relationLabel.style.display = newHyp.value.trim() ? '' : 'none';
}
document.getElementById('new_hypothesis').addEventListener('input', updateRelationVisibility);
updateRelationVisibility();

function setupComboboxAria(input, list, suggestionsId) {
  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-autocomplete', 'list');
  input.setAttribute('aria-haspopup', 'listbox');
  input.setAttribute('aria-controls', suggestionsId);
  input.setAttribute('aria-expanded', 'false');

  var activeIndex = -1;

  function options() {
    return Array.prototype.slice.call(list.children);
  }

  function setActive(index) {
    var opts = options();
    if (!opts.length) return;
    if (index < 0) index = opts.length - 1;
    if (index >= opts.length) index = 0;
    opts.forEach(function(li, i) {
      li.setAttribute('aria-selected', i === index ? 'true' : 'false');
    });
    activeIndex = index;
    input.setAttribute('aria-activedescendant', opts[index].id);
    opts[index].scrollIntoView({ block: 'nearest' });
  }

  input.addEventListener('keydown', function(e) {
    var opts = options();
    if (!opts.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive(activeIndex + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive(activeIndex - 1);
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0) {
        e.preventDefault();
        opts[activeIndex].dispatchEvent(new MouseEvent('mousedown'));
      }
    } else if (e.key === 'Escape') {
      list.innerHTML = '';
      reset();
    }
  });

  function reset() {
    activeIndex = -1;
    input.removeAttribute('aria-activedescendant');
    input.setAttribute('aria-expanded', list.children.length > 0 ? 'true' : 'false');
  }

  return { reset: reset };
}

function setupAutocomplete(inputId, suggestionsId, values) {
  var input = document.getElementById(inputId);
  var list = document.getElementById(suggestionsId);
  var combobox = setupComboboxAria(input, list, suggestionsId);

  function render(query) {
    list.innerHTML = '';
    var matches;
    if (query) {
      var lower = query.toLowerCase();
      var prefixMatches = [];
      var otherMatches = [];
      values.forEach(function(value) {
        var idx = value.toLowerCase().indexOf(lower);
        if (idx === 0) prefixMatches.push(value);
        else if (idx > 0) otherMatches.push(value);
      });
      matches = prefixMatches.concat(otherMatches).slice(0, 6);
    } else {
      matches = values;
    }
    matches.forEach(function(value, index) {
      var li = document.createElement('li');
      li.id = suggestionsId + '-opt-' + index;
      li.textContent = value;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');
      li.addEventListener('mousedown', function(e) {
        e.preventDefault();
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        list.innerHTML = '';
        combobox.reset();
      });
      list.appendChild(li);
    });
    combobox.reset();
  }

  input.addEventListener('input', function() {
    render(input.value.trim());
  });
  input.addEventListener('focus', function() {
    render(input.value.trim());
  });
  input.addEventListener('blur', function() {
    setTimeout(function() { list.innerHTML = ''; combobox.reset(); }, 200);
  });
}

function setupTagAutocomplete(inputId, suggestionsId, values) {
  var input = document.getElementById(inputId);
  var list = document.getElementById(suggestionsId);
  var combobox = setupComboboxAria(input, list, suggestionsId);

  function tagsInField() {
    return input.value.split(',').map(function(s) { return s.trim().toLowerCase(); }).filter(Boolean);
  }

  function currentToken() {
    var parts = input.value.split(',');
    return parts[parts.length - 1].trim();
  }

  function selectTag(value) {
    var parts = input.value.split(',');
    parts.pop();
    var newTags = parts.map(function(p) { return p.trim(); }).filter(Boolean);
    newTags.push(value);
    input.value = newTags.join(', ') + ', ';
    list.innerHTML = '';
    combobox.reset();
    input.focus();
  }

  function render() {
    list.innerHTML = '';
    var query = currentToken();
    var alreadyUsed = tagsInField();
    var matches;
    if (query) {
      var lower = query.toLowerCase();
      var prefixMatches = [];
      var otherMatches = [];
      values.forEach(function(value) {
        if (alreadyUsed.indexOf(value.toLowerCase()) !== -1) return;
        var idx = value.toLowerCase().indexOf(lower);
        if (idx === 0) prefixMatches.push(value);
        else if (idx > 0) otherMatches.push(value);
      });
      matches = prefixMatches.concat(otherMatches).slice(0, 6);
    } else {
      matches = values.filter(function(value) {
        return alreadyUsed.indexOf(value.toLowerCase()) === -1;
      });
    }
    matches.forEach(function(value, index) {
      var li = document.createElement('li');
      li.id = suggestionsId + '-opt-' + index;
      li.textContent = value;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');
      li.addEventListener('mousedown', function(e) {
        e.preventDefault();
        selectTag(value);
      });
      list.appendChild(li);
    });
    combobox.reset();
  }

  input.addEventListener('input', render);
  input.addEventListener('focus', render);
  input.addEventListener('blur', function() {
    setTimeout(function() { list.innerHTML = ''; combobox.reset(); }, 200);
  });
}

setupAutocomplete('person', 'person-suggestions', {{ people|tojson }});
setupAutocomplete('organization', 'organization-suggestions', {{ organizations|tojson }});
setupAutocomplete('signal_type', 'signal_type-suggestions', {{ signal_types|tojson }});
setupAutocomplete('channel', 'channel-suggestions', {{ channels|tojson }});
setupAutocomplete('role_opportunity', 'role_opportunity-suggestions', {{ roles|tojson }});
setupAutocomplete('new_hypothesis', 'hypothesis-suggestions', {{ hypothesis_statements|tojson }});
setupTagAutocomplete('problem_tags', 'problem_tags-suggestions', {{ problem_tag_values|tojson }});
setupTagAutocomplete('role_tags', 'role_tags-suggestions', {{ role_tag_values|tojson }});
</script>
"""


@app.route("/signals/new", methods=["GET", "POST"])
@login_required
def new_signal():
    db = get_supabase()
    user_id = g.user.id
    if request.method == "POST":
        form = request.form
        signal_type = form["signal_type"].strip()
        channel = form.get("channel", "").strip() or None
        created = (
            db.table("signals")
            .insert(
                {
                    "user_id": user_id,
                    "date": form["date"],
                    "person": form["person"],
                    "organization": form.get("organization") or None,
                    "signal_type": signal_type,
                    "role_opportunity": form.get("role_opportunity") or None,
                    "channel": channel,
                    "note": form["note"],
                    "learning": form.get("learning") or None,
                    "problem_heard": form.get("problem_heard") or None,
                    "interest_signal": form.get("interest_signal") or None,
                    "next_action": form.get("next_action") or None,
                }
            )
            .select()
            .execute()
            .data
        )
        signal_id = created[0]["id"]

        set_signal_tags(db, user_id, signal_id, "problem", form.get("problem_tags", ""))
        set_signal_tags(db, user_id, signal_id, "role", form.get("role_tags", ""))
        linked_hypothesis_id, linked_relation = set_signal_hypothesis(db, user_id, signal_id, form)

        for line in build_learning_feedback(
            db, user_id, linked_hypothesis_id, linked_relation, form.get("problem_tags", "")
        ):
            flash(line)

        return redirect(url_for("feed", saved=1))

    signal_types = distinct_values(db, user_id, "signal_type", SIGNAL_TYPE_SEED)
    channels = distinct_values(db, user_id, "channel", CHANNEL_SEED)
    people = recent_distinct_values(db, user_id, "person")
    organizations = recent_distinct_values(db, user_id, "organization")
    roles = recent_distinct_values(db, user_id, "role_opportunity")
    problem_tag_values = distinct_tag_values(db, user_id, "problem")
    role_tag_values = distinct_tag_values(db, user_id, "role")
    hypotheses = (
        db.table("hypotheses")
        .select("id, statement")
        .eq("user_id", user_id)
        .neq("status", "retired")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return render_template_string(
        page("Ny signal", SIGNAL_FORM_TEMPLATE),
        heading="Ny signal",
        form_action=url_for("new_signal"),
        submit_label="Spara signal",
        date_value=date.today().isoformat(),
        person_value="",
        organization_value="",
        people=people,
        organizations=organizations,
        roles=roles,
        problem_tag_values=problem_tag_values,
        role_tag_values=role_tag_values,
        signal_types=signal_types,
        signal_type_value="",
        role_opportunity_value="",
        channels=channels,
        channel_value="",
        note_value="",
        learning_value="",
        problem_heard_value="",
        interest_signal_value="",
        problem_tags_value="",
        role_tags_value="",
        hypothesis_statements=[h["statement"] for h in hypotheses],
        hypothesis_value="",
        relation_value="supports",
        next_action_value="",
    )


@app.route("/signals/<uuid:signal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_signal(signal_id):
    db = get_supabase()
    user_id = g.user.id
    signal_id = str(signal_id)
    signal_rows = db.table("signals").select("*").eq("id", signal_id).eq("user_id", user_id).execute().data
    if not signal_rows:
        return redirect(url_for("feed"))
    signal = signal_rows[0]

    if request.method == "POST":
        form = request.form
        signal_type = form["signal_type"].strip()
        channel = form.get("channel", "").strip() or None
        db.table("signals").update(
            {
                "date": form["date"],
                "person": form["person"],
                "organization": form.get("organization") or None,
                "signal_type": signal_type,
                "role_opportunity": form.get("role_opportunity") or None,
                "channel": channel,
                "note": form["note"],
                "learning": form.get("learning") or None,
                "problem_heard": form.get("problem_heard") or None,
                "interest_signal": form.get("interest_signal") or None,
                "next_action": form.get("next_action") or None,
            }
        ).eq("id", signal_id).eq("user_id", user_id).execute()

        set_signal_tags(db, user_id, signal_id, "problem", form.get("problem_tags", ""))
        set_signal_tags(db, user_id, signal_id, "role", form.get("role_tags", ""))
        linked_hypothesis_id, linked_relation = set_signal_hypothesis(db, user_id, signal_id, form)

        for line in build_learning_feedback(
            db, user_id, linked_hypothesis_id, linked_relation, form.get("problem_tags", "")
        ):
            flash(line)

        return redirect(url_for("feed"))

    signal_types = distinct_values(db, user_id, "signal_type", SIGNAL_TYPE_SEED)
    channels = distinct_values(db, user_id, "channel", CHANNEL_SEED)
    people = recent_distinct_values(db, user_id, "person")
    organizations = recent_distinct_values(db, user_id, "organization")
    roles = recent_distinct_values(db, user_id, "role_opportunity")
    problem_tag_values = distinct_tag_values(db, user_id, "problem")
    role_tag_values = distinct_tag_values(db, user_id, "role")
    hypotheses = (
        db.table("hypotheses")
        .select("id, statement")
        .eq("user_id", user_id)
        .neq("status", "retired")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    tag_rows = (
        db.table("signal_tags")
        .select("tags(text, category)")
        .eq("signal_id", signal_id)
        .execute()
        .data
    )
    problem_tags_value = ", ".join(r["tags"]["text"] for r in tag_rows if r["tags"]["category"] == "problem")
    role_tags_value = ", ".join(r["tags"]["text"] for r in tag_rows if r["tags"]["category"] == "role")

    hyp_link_rows = (
        db.table("signal_hypotheses")
        .select("relation, hypotheses(statement)")
        .eq("signal_id", signal_id)
        .limit(1)
        .execute()
        .data
    )
    hyp_link = hyp_link_rows[0] if hyp_link_rows else None

    return render_template_string(
        page("Redigera signal", SIGNAL_FORM_TEMPLATE),
        heading="Redigera signal",
        form_action=url_for("edit_signal", signal_id=signal_id),
        submit_label="Spara ändringar",
        date_value=signal["date"],
        person_value=signal["person"],
        organization_value=signal["organization"] or "",
        people=people,
        organizations=organizations,
        roles=roles,
        problem_tag_values=problem_tag_values,
        role_tag_values=role_tag_values,
        signal_types=signal_types,
        signal_type_value=signal["signal_type"],
        role_opportunity_value=signal["role_opportunity"] or "",
        channels=channels,
        channel_value=signal["channel"] or "",
        note_value=signal["note"],
        learning_value=signal["learning"] or "",
        problem_heard_value=signal["problem_heard"] or "",
        interest_signal_value=signal["interest_signal"] or "",
        problem_tags_value=problem_tags_value,
        role_tags_value=role_tags_value,
        hypothesis_statements=[h["statement"] for h in hypotheses],
        hypothesis_value=hyp_link["hypotheses"]["statement"] if hyp_link else "",
        relation_value=hyp_link["relation"] if hyp_link else "supports",
        next_action_value=signal["next_action"] or "",
    )


FEED_TEMPLATE = """
<h1>Signals flöde</h1>
{% if show_saved %}
<p class="toast">Bra jobbat! Signalen är sparad.</p>
{% endif %}
{% if learning_feedback %}
<div class="insight-note">
  {% for line in learning_feedback %}<p>{{ line }}</p>{% endfor %}
</div>
{% endif %}
{% if not signals %}
<p>Inga signaler ännu.</p>
{% else %}
<div class="feed-controls">
  <input type="search" id="feed-search" placeholder="Sök person, organisation, anteckning…" aria-label="Sök i flödet">
  {% if all_tags or any_hyp_linked %}
    <div class="chip-row" id="feed-chips">
      {% for t in all_tags %}<button type="button" class="chip" data-filter-tag="{{ t }}">{{ t }}</button>{% endfor %}
      {% if any_hyp_linked %}<button type="button" class="chip" data-filter-hyp="1">Kopplad till hypotes</button>{% endif %}
    </div>
  {% endif %}
  <p id="feed-empty-state" class="feed-empty" hidden>Inga signaler matchar filtret.</p>
</div>
{% endif %}
<ul class="feed">
{% for s in signals %}
  <li class="feed-card"
      data-search="{{ (s['person'] ~ ' ' ~ (s['organization'] or '') ~ ' ' ~ s['note'])|lower }}"
      data-tags="{{ s['tag_texts'] }}"
      data-has-hyp="{{ '1' if hyps_by_signal.get(s['id']) else '' }}">
    <strong>{{ s['date'] }}</strong> — {{ s['person'] }}{% if s['organization'] %} ({{ s['organization'] }}){% endif %}
    <span class="badge">{{ s['signal_type'] }}</span>
    {% if tags_by_signal.get(s['id']) %}
      <p class="tags">
        {% for t in tags_by_signal[s['id']] %}<span class="tag {{ t['category'] }}">{{ t['text'] }}</span>{% endfor %}
      </p>
    {% endif %}
    <p class="note-preview">{{ s['note_preview'] }}</p>
    {% if s['has_extra'] %}
      <div class="card-details" {% if not s['always_expanded'] %}hidden{% endif %}>
        {% if s['channel'] %}<span class="badge">{{ s['channel'] }}</span>{% endif %}
        {% if s['note_truncated'] %}<p>{{ s['note'] }}</p>{% endif %}
        {% if s['learning'] %}<p><em>Lärde mig:</em> {{ s['learning'] }}</p>{% endif %}
        {% if s['role_opportunity'] %}<p><em>Roll/möjlighet:</em> {{ s['role_opportunity'] }}</p>{% endif %}
        {% if s['problem_heard'] %}<p><em>Problem/behov:</em> {{ s['problem_heard'] }}</p>{% endif %}
        {% if s['interest_signal'] %}<p><em>Skapade intresse:</em> {{ s['interest_signal'] }}</p>{% endif %}
        {% if hyps_by_signal.get(s['id']) %}
          <p class="hyps">
            {% for h in hyps_by_signal[s['id']] %}
              <span class="hyp {{ h['relation'] }}">{{ 'Stödjer' if h['relation'] == 'supports' else 'Motsäger' }}: {{ h['statement'] }}</span>
            {% endfor %}
          </p>
        {% endif %}
        {% if s['next_action'] %}
          <p class="next-action {{ 'done' if s['next_action_done'] else '' }}">
            Nästa steg: {{ s['next_action'] }}{% if s['next_action_done'] %} (klar){% endif %}
          </p>
        {% endif %}
      </div>
      <button type="button" class="card-toggle" aria-expanded="{{ 'true' if s['always_expanded'] else 'false' }}">{{ 'Visa mindre' if s['always_expanded'] else 'Visa mer' }}</button>
    {% endif %}
    <div class="actions-row">
      {% if s['next_action'] and not s['next_action_done'] %}
        <form method="post" action="{{ url_for('mark_next_action_done', signal_id=s['id']) }}">
          <button type="submit" class="btn-accent">Klarmarkera</button>
        </form>
      {% elif s['next_action'] %}
        <form method="post" action="{{ url_for('unmark_next_action_done', signal_id=s['id']) }}">
          <button type="submit">Ångra</button>
        </form>
      {% endif %}
      <a href="{{ url_for('edit_signal', signal_id=s['id']) }}">Redigera</a>
      <form method="post" action="{{ url_for('delete_signal', signal_id=s['id']) }}"
            onsubmit="return confirm('Ta bort den här signalen? Det går inte att ångra.');">
        <button type="submit" class="btn-danger">Ta bort</button>
      </form>
    </div>
  </li>
{% endfor %}
</ul>
<script>
(function() {
  var search = document.getElementById('feed-search');
  var chipRow = document.getElementById('feed-chips');
  var items = Array.prototype.slice.call(document.querySelectorAll('.feed-card'));
  var emptyState = document.getElementById('feed-empty-state');
  var activeTags = [];
  var hypOnly = false;

  function applyFilters() {
    var query = search ? search.value.trim().toLowerCase() : '';
    var visibleCount = 0;
    items.forEach(function(li) {
      var tags = li.dataset.tags ? li.dataset.tags.split(',') : [];
      var matchesSearch = !query || li.dataset.search.indexOf(query) !== -1;
      var matchesTags = activeTags.every(function(t) { return tags.indexOf(t) !== -1; });
      var matchesHyp = !hypOnly || li.dataset.hasHyp === '1';
      var visible = matchesSearch && matchesTags && matchesHyp;
      li.hidden = !visible;
      if (visible) visibleCount++;
    });
    if (emptyState) emptyState.hidden = visibleCount !== 0;
  }

  if (search) search.addEventListener('input', applyFilters);
  if (chipRow) {
    chipRow.addEventListener('click', function(e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      if (chip.dataset.filterTag) {
        var t = chip.dataset.filterTag;
        var idx = activeTags.indexOf(t);
        if (idx === -1) { activeTags.push(t); chip.classList.add('active'); }
        else { activeTags.splice(idx, 1); chip.classList.remove('active'); }
      } else if (chip.dataset.filterHyp) {
        hypOnly = !hypOnly;
        chip.classList.toggle('active', hypOnly);
      }
      applyFilters();
    });
  }

  document.querySelectorAll('.card-toggle').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var card = btn.closest('.feed-card');
      var details = card.querySelector('.card-details');
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      details.hidden = expanded;
      btn.setAttribute('aria-expanded', String(!expanded));
      btn.textContent = expanded ? 'Visa mer' : 'Visa mindre';
    });
  });
})();
</script>
"""


@app.route("/")
@login_required
def feed():
    db = get_supabase()
    user_id = g.user.id
    show_saved = request.args.get("saved") == "1"
    learning_feedback = get_flashed_messages()
    signals = (
        db.table("signals")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    signal_ids = [s["id"] for s in signals]

    tags_by_signal = {}
    hyps_by_signal = {}
    if signal_ids:
        tag_rows = (
            db.table("signal_tags")
            .select("signal_id, tags(text, category)")
            .in_("signal_id", signal_ids)
            .execute()
            .data
        )
        for r in tag_rows:
            tags_by_signal.setdefault(r["signal_id"], []).append(r["tags"])

        hyp_rows = (
            db.table("signal_hypotheses")
            .select("signal_id, relation, hypotheses(statement)")
            .in_("signal_id", signal_ids)
            .execute()
            .data
        )
        for r in hyp_rows:
            hyps_by_signal.setdefault(r["signal_id"], []).append(
                {"relation": r["relation"], "statement": r["hypotheses"]["statement"]}
            )

    note_preview_max = 140
    for s in signals:
        first_line, _, rest = s["note"].partition("\n")
        line_truncated = len(first_line) > note_preview_max
        s["note_preview"] = (
            first_line[:note_preview_max].rstrip() + "…" if line_truncated else first_line
        )
        s["note_truncated"] = line_truncated or bool(rest)
        s["always_expanded"] = bool(s["next_action"] and not s["next_action_done"])
        s["tag_texts"] = ",".join(t["text"] for t in tags_by_signal.get(s["id"], []))
        s["has_extra"] = bool(
            s["channel"]
            or s["note_truncated"]
            or s["learning"]
            or s["role_opportunity"]
            or s["problem_heard"]
            or s["interest_signal"]
            or hyps_by_signal.get(s["id"])
            or s["next_action"]
        )

    all_tags = sorted({t["text"] for tags in tags_by_signal.values() for t in tags})
    any_hyp_linked = bool(hyps_by_signal)

    return render_template_string(
        page("Signal Feed", FEED_TEMPLATE),
        signals=signals,
        tags_by_signal=tags_by_signal,
        hyps_by_signal=hyps_by_signal,
        all_tags=all_tags,
        any_hyp_linked=any_hyp_linked,
        show_saved=show_saved,
        learning_feedback=learning_feedback,
    )


@app.route("/signals/<uuid:signal_id>/delete", methods=["POST"])
@login_required
def delete_signal(signal_id):
    db = get_supabase()
    user_id = g.user.id
    signal_id = str(signal_id)
    db.table("signal_tags").delete().eq("signal_id", signal_id).eq("user_id", user_id).execute()
    db.table("signal_hypotheses").delete().eq("signal_id", signal_id).eq("user_id", user_id).execute()
    db.table("signals").delete().eq("id", signal_id).eq("user_id", user_id).execute()
    return redirect(url_for("feed"))


@app.route("/signals/<uuid:signal_id>/done", methods=["POST"])
@login_required
def mark_next_action_done(signal_id):
    db = get_supabase()
    db.table("signals").update({"next_action_done": True}).eq("id", str(signal_id)).eq(
        "user_id", g.user.id
    ).execute()
    return redirect(request.referrer or url_for("feed"))


@app.route("/signals/<uuid:signal_id>/undone", methods=["POST"])
@login_required
def unmark_next_action_done(signal_id):
    db = get_supabase()
    db.table("signals").update({"next_action_done": False}).eq("id", str(signal_id)).eq(
        "user_id", g.user.id
    ).execute()
    return redirect(request.referrer or url_for("feed"))


HYPOTHESES_LIST_TEMPLATE = """
<h1>Hypoteser</h1>
{% if not hypotheses %}<p>Inga hypoteser ännu.</p>{% endif %}
<ul>
{% for h in hypotheses %}
  <li>
    <a href="{{ url_for('hypothesis_detail', hypothesis_id=h['id']) }}">{{ h['statement'] }}</a>
    <span class="badge">{{ h['status'] }}</span>
    {% if h['supports_count'] + h['contradicts_count'] == 0 %}
      <span class="badge">Ingen evidens än</span>
    {% else %}
      <span class="tag role">{{ h['supports_count'] }} stödjer</span>
      <span class="tag problem">{{ h['contradicts_count'] }} motsäger</span>
    {% endif %}
  </li>
{% endfor %}
</ul>
"""

HYPOTHESIS_DETAIL_TEMPLATE = """
<p><a href="{{ url_for('hypotheses_list') }}">&larr; Alla hypoteser</a></p>
<h1>{{ hyp['statement'] }}</h1>
<div class="actions-row">
  <a href="{{ url_for('edit_hypothesis', hypothesis_id=hyp['id']) }}">Redigera</a>
  <form method="post" action="{{ url_for('delete_hypothesis', hypothesis_id=hyp['id']) }}"
        onsubmit="return confirm('Ta bort den här hypotesen? Kopplingar till signaler tas också bort. Det går inte att ångra.');">
    <button type="submit" class="btn-danger">Ta bort</button>
  </form>
</div>
<p style="font-weight:600;font-size:.875rem;margin-bottom:.4rem">Status</p>
<form method="post" action="{{ url_for('update_hypothesis_status', hypothesis_id=hyp['id']) }}" class="status-row">
  {% for s in ['exploring', 'strengthening', 'weakening', 'retired'] %}
    <button type="submit" name="status" value="{{ s }}" class="{{ 'btn-accent' if hyp['status'] == s else '' }}">{{ s }}</button>
  {% endfor %}
</form>

<h2>Stödjande signaler ({{ supporting|length }})</h2>
<ul>
{% for s in supporting %}<li><a href="{{ url_for('edit_signal', signal_id=s['id']) }}">{{ s['date'] }} — {{ s['person'] }}: {{ s['note'] }}</a></li>{% endfor %}
</ul>

<h2>Motsägande signaler ({{ contradicting|length }})</h2>
<ul>
{% for s in contradicting %}<li><a href="{{ url_for('edit_signal', signal_id=s['id']) }}">{{ s['date'] }} — {{ s['person'] }}: {{ s['note'] }}</a></li>{% endfor %}
</ul>
"""

HYPOTHESIS_EDIT_TEMPLATE = """
<p><a href="{{ url_for('hypothesis_detail', hypothesis_id=hypothesis_id) }}">&larr; Tillbaka</a></p>
<h1>Redigera hypotes</h1>
{% if error %}<span class="error">{{ error }}</span>{% endif %}
<form method="post" action="{{ url_for('edit_hypothesis', hypothesis_id=hypothesis_id) }}">
  <label>Hypotes<textarea name="statement" required>{{ statement_value }}</textarea></label>
  <button type="submit" class="btn-primary">Spara ändringar</button>
</form>
"""


@app.route("/hypotheses")
@login_required
def hypotheses_list():
    db = get_supabase()
    rows = (
        db.table("hypotheses")
        .select("*, signal_hypotheses(relation)")
        .eq("user_id", g.user.id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    for h in rows:
        relations = [sh["relation"] for sh in h.get("signal_hypotheses", [])]
        h["supports_count"] = relations.count("supports")
        h["contradicts_count"] = relations.count("contradicts")
    rows.sort(key=lambda h: (h["supports_count"] + h["contradicts_count"]) > 0)
    return render_template_string(page("Hypoteser", HYPOTHESES_LIST_TEMPLATE), hypotheses=rows)


@app.route("/hypotheses/<uuid:hypothesis_id>")
@login_required
def hypothesis_detail(hypothesis_id):
    db = get_supabase()
    user_id = g.user.id
    hypothesis_id = str(hypothesis_id)
    hyp_rows = (
        db.table("hypotheses").select("*").eq("id", hypothesis_id).eq("user_id", user_id).execute().data
    )
    if not hyp_rows:
        return redirect(url_for("hypotheses_list"))
    hyp = hyp_rows[0]

    evidence = (
        db.table("signal_hypotheses")
        .select("relation, signals(id, date, person, note)")
        .eq("hypothesis_id", hypothesis_id)
        .execute()
        .data
    )
    supporting = sorted(
        (e["signals"] for e in evidence if e["relation"] == "supports"), key=lambda s: s["date"], reverse=True
    )
    contradicting = sorted(
        (e["signals"] for e in evidence if e["relation"] == "contradicts"), key=lambda s: s["date"], reverse=True
    )
    return render_template_string(
        page("Hypotes", HYPOTHESIS_DETAIL_TEMPLATE),
        hyp=hyp,
        supporting=supporting,
        contradicting=contradicting,
    )


@app.route("/hypotheses/<uuid:hypothesis_id>/status", methods=["POST"])
@login_required
def update_hypothesis_status(hypothesis_id):
    db = get_supabase()
    status = request.form["status"]
    db.table("hypotheses").update({"status": status}).eq("id", str(hypothesis_id)).eq(
        "user_id", g.user.id
    ).execute()
    return redirect(url_for("hypothesis_detail", hypothesis_id=hypothesis_id))


@app.route("/hypotheses/<uuid:hypothesis_id>/edit", methods=["GET", "POST"])
@login_required
def edit_hypothesis(hypothesis_id):
    db = get_supabase()
    user_id = g.user.id
    hypothesis_id = str(hypothesis_id)
    hyp_rows = (
        db.table("hypotheses").select("*").eq("id", hypothesis_id).eq("user_id", user_id).execute().data
    )
    if not hyp_rows:
        return redirect(url_for("hypotheses_list"))
    hyp = hyp_rows[0]

    if request.method == "POST":
        statement = request.form.get("statement", "").strip()
        if not statement:
            return render_template_string(
                page("Redigera hypotes", HYPOTHESIS_EDIT_TEMPLATE),
                hypothesis_id=hypothesis_id,
                statement_value=statement,
                error="Hypotesen kan inte vara tom.",
            )
        db.table("hypotheses").update({"statement": statement}).eq("id", hypothesis_id).eq(
            "user_id", user_id
        ).execute()
        return redirect(url_for("hypothesis_detail", hypothesis_id=hypothesis_id))

    return render_template_string(
        page("Redigera hypotes", HYPOTHESIS_EDIT_TEMPLATE),
        hypothesis_id=hypothesis_id,
        statement_value=hyp["statement"],
        error=None,
    )


@app.route("/hypotheses/<uuid:hypothesis_id>/delete", methods=["POST"])
@login_required
def delete_hypothesis(hypothesis_id):
    db = get_supabase()
    user_id = g.user.id
    hypothesis_id = str(hypothesis_id)
    db.table("signal_hypotheses").delete().eq("hypothesis_id", hypothesis_id).eq("user_id", user_id).execute()
    db.table("hypotheses").delete().eq("id", hypothesis_id).eq("user_id", user_id).execute()
    return redirect(url_for("hypotheses_list"))


REVIEW_TEMPLATE = """
<h1>Översikt</h1>
<div class="actions-row">
{% for key, opt in range_options.items() %}
  <a href="{{ url_for('review', range=key) }}" class="{{ 'btn-accent' if key == selected_range else '' }}">{{ opt['label'] }}</a>
{% endfor %}
</div>
<p style="margin:-0.5rem 0 1rem"><a href="{{ url_for('ideas') }}">Idé till appen &rarr;</a></p>
<p>{{ range_count }} signaler {{ range_text }}.</p>

<h2>Mest frekventa problem-taggar</h2>
<ul>{% for t in top_problem_tags %}<li>{{ t['text'] }} ({{ t['n'] }})</li>{% endfor %}</ul>

<h2>Mest frekventa roll-taggar</h2>
<ul>{% for t in top_role_tags %}<li>{{ t['text'] }} ({{ t['n'] }})</li>{% endfor %}</ul>

<h2>Hypoteser med ny evidens {{ range_text }}</h2>
<ul>
{% for h in hyps_with_new_evidence %}
  <li><a href="{{ url_for('hypothesis_detail', hypothesis_id=h['id']) }}">{{ h['statement'] }}</a> — +{{ h['new_supports'] }} stödjer, +{{ h['new_contradicts'] }} motsäger</li>
{% endfor %}
</ul>

<h2>Obehandlade nästa steg</h2>
<ul>
{% for s in outstanding_actions %}
  <li>
    {{ s['date'] }} — {{ s['person'] }}: {{ s['next_action'] }}
    <form method="post" action="{{ url_for('mark_next_action_done', signal_id=s['id']) }}">
      <button type="submit" class="btn-accent">Klarmarkera</button>
    </form>
  </li>
{% endfor %}
</ul>
"""


REVIEW_RANGE_OPTIONS = {
    "week": {"label": "Vecka", "days": 7, "text": "senaste 7 dagarna"},
    "month": {"label": "Månad", "days": 30, "text": "senaste 30 dagarna"},
    "quarter": {"label": "3 månader", "days": 90, "text": "senaste 90 dagarna"},
    "all": {"label": "Alla", "days": None, "text": "hela tiden"},
}


@app.route("/review")
@login_required
def review():
    db = get_supabase()
    user_id = g.user.id

    selected_range = request.args.get("range", "week")
    if selected_range not in REVIEW_RANGE_OPTIONS:
        selected_range = "week"
    range_days = REVIEW_RANGE_OPTIONS[selected_range]["days"]

    range_query = db.table("signals").select("*").eq("user_id", user_id)
    if range_days is not None:
        range_start = (datetime.now(timezone.utc) - timedelta(days=range_days)).date().isoformat()
        range_query = range_query.gte("date", range_start)
    range_signals = range_query.order("date", desc=True).execute().data
    range_ids = [s["id"] for s in range_signals]

    top_problem_tags = []
    top_role_tags = []
    hyps_with_new_evidence = []
    if range_ids:
        tag_rows = (
            db.table("signal_tags")
            .select("signal_id, tags(text, category)")
            .in_("signal_id", range_ids)
            .execute()
            .data
        )
        problem_counts, role_counts = {}, {}
        for r in tag_rows:
            t = r["tags"]
            bucket = problem_counts if t["category"] == "problem" else role_counts
            bucket[t["text"]] = bucket.get(t["text"], 0) + 1
        top_problem_tags = [
            {"text": k, "n": v} for k, v in sorted(problem_counts.items(), key=lambda kv: -kv[1])
        ][:10]
        top_role_tags = [
            {"text": k, "n": v} for k, v in sorted(role_counts.items(), key=lambda kv: -kv[1])
        ][:10]

        hyp_rows = (
            db.table("signal_hypotheses")
            .select("hypothesis_id, relation, hypotheses(id, statement)")
            .in_("signal_id", range_ids)
            .execute()
            .data
        )
        hyp_agg = {}
        for r in hyp_rows:
            hid = r["hypothesis_id"]
            entry = hyp_agg.setdefault(
                hid, {"id": hid, "statement": r["hypotheses"]["statement"], "new_supports": 0, "new_contradicts": 0}
            )
            if r["relation"] == "supports":
                entry["new_supports"] += 1
            else:
                entry["new_contradicts"] += 1
        hyps_with_new_evidence = list(hyp_agg.values())

    outstanding_actions = (
        db.table("signals")
        .select("*")
        .eq("user_id", user_id)
        .eq("next_action_done", False)
        .order("date", desc=True)
        .execute()
        .data
    )
    outstanding_actions = [s for s in outstanding_actions if s.get("next_action")]

    return render_template_string(
        page("Översikt", REVIEW_TEMPLATE),
        range_options=REVIEW_RANGE_OPTIONS,
        selected_range=selected_range,
        range_text=REVIEW_RANGE_OPTIONS[selected_range]["text"],
        range_count=len(range_signals),
        top_problem_tags=top_problem_tags,
        top_role_tags=top_role_tags,
        hyps_with_new_evidence=hyps_with_new_evidence,
        outstanding_actions=outstanding_actions,
    )


IDEA_TEMPLATE = """
<h1>Idéer</h1>
<form method="post">
  <label>Idé<textarea name="idea" required autofocus></textarea></label>
  <button type="submit" class="btn-primary">Spara</button>
</form>

{% if not ideas %}
<p>Inga idéer ännu.</p>
{% endif %}
<ul class="feed">
{% for i in ideas %}
  <li>
    <strong>{{ i['created_at'][:10] }}</strong><p>{{ i['idea'] }}</p>
    <div class="vote-row">
      <form method="post" action="{{ url_for('vote_idea', idea_id=i['id']) }}">
        <input type="hidden" name="direction" value="up">
        <button type="submit">+1</button>
      </form>
      <span class="badge">{{ i['score'] }}</span>
      <form method="post" action="{{ url_for('vote_idea', idea_id=i['id']) }}">
        <input type="hidden" name="direction" value="down">
        <button type="submit">−1</button>
      </form>
    </div>
    <div class="actions-row">
      <a href="{{ url_for('edit_idea', idea_id=i['id']) }}">Redigera</a>
      <form method="post" action="{{ url_for('delete_idea', idea_id=i['id']) }}"
            onsubmit="return confirm('Ta bort den här idén? Det går inte att ångra.');">
        <button type="submit" class="btn-danger">Ta bort</button>
      </form>
    </div>
  </li>
{% endfor %}
</ul>
"""

IDEA_EDIT_TEMPLATE = """
<p><a href="{{ url_for('ideas') }}">&larr; Tillbaka</a></p>
<h1>Redigera idé</h1>
{% if error %}<span class="error">{{ error }}</span>{% endif %}
<form method="post" action="{{ url_for('edit_idea', idea_id=idea_id) }}">
  <label>Idé<textarea name="idea" required autofocus>{{ idea_value }}</textarea></label>
  <button type="submit" class="btn-primary">Spara ändringar</button>
</form>
"""


@app.route("/ideas", methods=["GET", "POST"])
@login_required
def ideas():
    db = get_supabase()
    user_id = g.user.id
    if request.method == "POST":
        idea = request.form.get("idea", "").strip()
        if idea:
            db.table("ideas").insert({"user_id": user_id, "idea": idea}).execute()
        return redirect(url_for("ideas"))

    rows = (
        db.table("ideas")
        .select("*")
        .eq("user_id", user_id)
        .order("score", desc=True)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return render_template_string(page("Idéer", IDEA_TEMPLATE), ideas=rows)


@app.route("/ideas/<uuid:idea_id>/vote", methods=["POST"])
@login_required
def vote_idea(idea_id):
    db = get_supabase()
    user_id = g.user.id
    idea_id = str(idea_id)
    delta = 1 if request.form.get("direction") == "up" else -1

    row = db.table("ideas").select("score").eq("id", idea_id).eq("user_id", user_id).execute().data
    if row:
        db.table("ideas").update({"score": row[0]["score"] + delta}).eq("id", idea_id).eq(
            "user_id", user_id
        ).execute()

    return redirect(url_for("ideas"))


@app.route("/ideas/<uuid:idea_id>/edit", methods=["GET", "POST"])
@login_required
def edit_idea(idea_id):
    db = get_supabase()
    user_id = g.user.id
    idea_id = str(idea_id)
    rows = db.table("ideas").select("*").eq("id", idea_id).eq("user_id", user_id).execute().data
    if not rows:
        return redirect(url_for("ideas"))
    idea_row = rows[0]

    if request.method == "POST":
        idea = request.form.get("idea", "").strip()
        if not idea:
            return render_template_string(
                page("Redigera idé", IDEA_EDIT_TEMPLATE),
                idea_id=idea_id,
                idea_value=idea,
                error="Idén kan inte vara tom.",
            )
        db.table("ideas").update({"idea": idea}).eq("id", idea_id).eq("user_id", user_id).execute()
        return redirect(url_for("ideas"))

    return render_template_string(
        page("Redigera idé", IDEA_EDIT_TEMPLATE),
        idea_id=idea_id,
        idea_value=idea_row["idea"],
        error=None,
    )


@app.route("/ideas/<uuid:idea_id>/delete", methods=["POST"])
@login_required
def delete_idea(idea_id):
    db = get_supabase()
    user_id = g.user.id
    idea_id = str(idea_id)
    db.table("ideas").delete().eq("id", idea_id).eq("user_id", user_id).execute()
    return redirect(url_for("ideas"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
