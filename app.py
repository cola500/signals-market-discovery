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
from flask import Flask, g, redirect, render_template_string, request, send_from_directory, session, url_for
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
nav{position:fixed;left:0;right:0;bottom:0;display:flex;align-items:center;gap:2px;background:var(--white);border-top:1px solid var(--ink-100);box-shadow:var(--shadow-md);padding:.5rem .5rem calc(.5rem + env(safe-area-inset-bottom));z-index:10}
nav a,nav a:visited{flex:1;text-align:center;padding:.4rem .3rem;display:block;color:var(--ink-600);font-weight:600;font-size:.8rem;text-decoration:none;border-radius:var(--radius-md);transition:color .12s var(--ease)}
nav a:hover{color:var(--coral-600)}
nav form{display:inline-block;flex:0}
nav button{padding:.4rem .6rem;min-height:auto;font-size:.75rem;background:none;border:none;color:var(--ink-400);font-weight:600}
nav button:hover{color:var(--ink-950)}
form label{display:block;margin-bottom:1rem;font-weight:600;font-size:.875rem;color:var(--ink-950)}
input,select,textarea{width:100%;padding:.7rem .85rem;box-sizing:border-box;font-size:1rem;font-family:inherit;border:1px solid var(--ink-200);border-radius:var(--radius-md);background:var(--white);margin-top:.4rem;transition:border-color .12s var(--ease),box-shadow .12s var(--ease)}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--coral-500);box-shadow:0 0 0 3px rgba(255,106,71,.25)}
textarea{min-height:6rem;resize:vertical}
button{padding:.75rem 1.25rem;font-size:1rem;font-family:inherit;font-weight:700;border-radius:var(--radius-md);min-height:44px;border:1px solid var(--ink-200);background:var(--ink-50);color:var(--ink-950);cursor:pointer;transition:background .12s var(--ease),transform .12s var(--ease)}
button:hover{background:var(--ink-100)}
button:active{transform:scale(.97)}
.btn-primary{width:100%;margin-top:.5rem;background:var(--coral-500);border:none;color:#fff}
.btn-primary:hover{background:var(--coral-600)}
.btn-primary:active{background:var(--coral-700);transform:scale(.97)}
fieldset{margin-bottom:1rem;border:1px solid var(--ink-100);border-radius:var(--radius-md);background:var(--ink-50);padding:1rem}
legend{font-weight:700;font-size:.875rem;padding:0 .3rem}
.feed{list-style:none;padding:0;display:flex;flex-direction:column;gap:1rem}
.feed li{border:1px solid var(--ink-100);border-radius:var(--radius-lg);background:var(--white);box-shadow:var(--shadow-sm);padding:1.25rem}
.badge{display:inline-block;background:var(--ink-100);color:var(--ink-600);border-radius:var(--radius-full);padding:.15rem .65rem;font-size:.8rem;font-weight:700;margin-right:.3rem}
.tag{display:inline-block;border-radius:var(--radius-full);padding:.2rem .7rem;font-size:.8rem;font-weight:600;margin-right:.35rem}
.tag.problem{background:var(--rose-100);color:var(--rose-text)}
.tag.role{background:var(--teal-100);color:var(--teal-700)}
.hyp{display:block;font-size:.85rem;font-weight:600;margin-top:.4rem}
.hyp.supports{color:var(--success-500)}
.hyp.contradicts{color:var(--danger-500)}
.next-action.done{text-decoration:line-through;color:var(--ink-400)}
.error{color:var(--rose-text);background:var(--rose-100);padding:.75rem 1rem;border-radius:var(--radius-md);border-left:3px solid var(--danger-500);display:block;margin-bottom:1rem}
#splash{position:fixed;inset:0;background:var(--coral-500);display:flex;align-items:center;justify-content:center;z-index:100;transition:opacity .4s ease-out}
#splash img{width:88px;height:88px;border-radius:20px}
</style>
"""

NAV = """
<nav>
  {% if session.get('access_token') %}
    <a href="{{ url_for('feed') }}">Feed</a>
    <a href="/signals/new">+ Ny signal</a>
    <a href="/hypotheses">Hypoteser</a>
    <a href="/review">Veckoöversikt</a>
    <form method="post" action="{{ url_for('logout') }}"><button type="submit">Logga ut</button></form>
  {% else %}
    <a href="{{ url_for('login') }}">Logga in</a>
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


def page(title, body_template):
    return (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"{HEAD_EXTRAS}"
        f"<title>{title}</title>{STYLE}</head><body>{SPLASH}{NAV}{body_template}</body></html>"
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


def resolve_select_or_other(form, select_name, other_name):
    other = (form.get(other_name) or "").strip()
    if other:
        return other
    return (form.get(select_name) or "").strip()


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
    existing_hyp_id = form.get("hypothesis_id")
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
    elif existing_hyp_id:
        hypothesis_id = existing_hyp_id

    if hypothesis_id and relation:
        db.table("signal_hypotheses").insert(
            {"signal_id": signal_id, "hypothesis_id": hypothesis_id, "user_id": user_id, "relation": relation}
        ).execute()


SIGNAL_FORM_TEMPLATE = """
<h1>{{ heading }}</h1>
<form method="post" action="{{ form_action }}" onsubmit="return validateSignalType()">
  <label>Datum *<input type="date" name="date" value="{{ date_value }}" required></label>
  <label>Person *<input type="text" name="person" value="{{ person_value }}" required></label>
  <label>Organisation<input type="text" name="organization" value="{{ organization_value }}"></label>
  <label>Signal-typ *
    <select name="signal_type_select">
      <option value="">-- välj --</option>
      {% for t in signal_types %}<option value="{{ t }}" {% if t == signal_type_select_value %}selected{% endif %}>{{ t }}</option>{% endfor %}
    </select>
  </label>
  <label>...eller skriv egen signal-typ (åsidosätter valet ovan)<input type="text" name="signal_type_other" value="{{ signal_type_other_value }}"></label>
  <label>Roll/möjlighet (valfritt)<input type="text" name="role_opportunity" value="{{ role_opportunity_value }}"></label>
  <label>Kanal
    <select name="channel_select">
      <option value="">-- ingen --</option>
      {% for c in channels %}<option value="{{ c }}" {% if c == channel_select_value %}selected{% endif %}>{{ c }}</option>{% endfor %}
    </select>
  </label>
  <label>...eller skriv egen kanal<input type="text" name="channel_other" value="{{ channel_other_value }}"></label>
  <label>Vad hände? *<textarea name="note" required>{{ note_value }}</textarea></label>
  <label>Vad lärde jag mig?<textarea name="learning">{{ learning_value }}</textarea></label>
  <label>Vilket problem/behov hörde jag?<textarea name="problem_heard">{{ problem_heard_value }}</textarea></label>
  <label>Vad skapade intresse för min bakgrund?<textarea name="interest_signal">{{ interest_signal_value }}</textarea></label>
  <label>Problem-taggar (kommaseparerat)<input type="text" name="problem_tags" value="{{ problem_tags_value }}"></label>
  <label>Roll-taggar (kommaseparerat)<input type="text" name="role_tags" value="{{ role_tags_value }}"></label>

  <fieldset>
    <legend>Hypotes (valfritt)</legend>
    <label>Befintlig hypotes
      <select name="hypothesis_id">
        <option value="">-- ingen --</option>
        {% for h in hypotheses %}<option value="{{ h['id'] }}" {% if hypothesis_id_value and h['id']|string == hypothesis_id_value|string %}selected{% endif %}>{{ h['statement'] }}</option>{% endfor %}
      </select>
    </label>
    <label>Eller skriv en ny hypotes<input type="text" name="new_hypothesis"></label>
    <label>Relation
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
function validateSignalType() {
  var sel = document.querySelector('select[name="signal_type_select"]');
  var other = document.querySelector('input[name="signal_type_other"]');
  if (!sel.value && !other.value.trim()) {
    alert('Fyll i Signal-typ (välj i listan eller skriv eget).');
    sel.focus();
    return false;
  }
  return true;
}
</script>
"""


@app.route("/signals/new", methods=["GET", "POST"])
@login_required
def new_signal():
    db = get_supabase()
    user_id = g.user.id
    if request.method == "POST":
        form = request.form
        signal_type = resolve_select_or_other(form, "signal_type_select", "signal_type_other")
        channel = resolve_select_or_other(form, "channel_select", "channel_other") or None
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
        set_signal_hypothesis(db, user_id, signal_id, form)

        return redirect(url_for("feed"))

    signal_types = distinct_values(db, user_id, "signal_type", SIGNAL_TYPE_SEED)
    channels = distinct_values(db, user_id, "channel", CHANNEL_SEED)
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
        signal_types=signal_types,
        signal_type_select_value="",
        signal_type_other_value="",
        role_opportunity_value="",
        channels=channels,
        channel_select_value="",
        channel_other_value="",
        note_value="",
        learning_value="",
        problem_heard_value="",
        interest_signal_value="",
        problem_tags_value="",
        role_tags_value="",
        hypotheses=hypotheses,
        hypothesis_id_value="",
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
        signal_type = resolve_select_or_other(form, "signal_type_select", "signal_type_other")
        channel = resolve_select_or_other(form, "channel_select", "channel_other") or None
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
        set_signal_hypothesis(db, user_id, signal_id, form)

        return redirect(url_for("feed"))

    signal_types = distinct_values(db, user_id, "signal_type", SIGNAL_TYPE_SEED)
    channels = distinct_values(db, user_id, "channel", CHANNEL_SEED)
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
        .select("hypothesis_id, relation")
        .eq("signal_id", signal_id)
        .limit(1)
        .execute()
        .data
    )
    hyp_link = hyp_link_rows[0] if hyp_link_rows else None

    signal_type_known = signal["signal_type"] in signal_types
    channel_known = not signal["channel"] or signal["channel"] in channels

    return render_template_string(
        page("Redigera signal", SIGNAL_FORM_TEMPLATE),
        heading="Redigera signal",
        form_action=url_for("edit_signal", signal_id=signal_id),
        submit_label="Spara ändringar",
        date_value=signal["date"],
        person_value=signal["person"],
        organization_value=signal["organization"] or "",
        signal_types=signal_types,
        signal_type_select_value=signal["signal_type"] if signal_type_known else "",
        signal_type_other_value="" if signal_type_known else signal["signal_type"],
        role_opportunity_value=signal["role_opportunity"] or "",
        channels=channels,
        channel_select_value=signal["channel"] if channel_known else "",
        channel_other_value="" if channel_known else signal["channel"],
        note_value=signal["note"],
        learning_value=signal["learning"] or "",
        problem_heard_value=signal["problem_heard"] or "",
        interest_signal_value=signal["interest_signal"] or "",
        problem_tags_value=problem_tags_value,
        role_tags_value=role_tags_value,
        hypotheses=hypotheses,
        hypothesis_id_value=str(hyp_link["hypothesis_id"]) if hyp_link else "",
        relation_value=hyp_link["relation"] if hyp_link else "supports",
        next_action_value=signal["next_action"] or "",
    )


FEED_TEMPLATE = """
<h1>Signal Feed</h1>
<p><a href="{{ url_for('new_signal') }}">+ Ny signal</a></p>
{% if not signals %}
<p>Inga signaler ännu.</p>
{% endif %}
<ul class="feed">
{% for s in signals %}
  <li>
    <strong>{{ s['date'] }}</strong> — {{ s['person'] }}{% if s['organization'] %} ({{ s['organization'] }}){% endif %}
    <span class="badge">{{ s['signal_type'] }}</span>
    {% if s['channel'] %}<span class="badge">{{ s['channel'] }}</span>{% endif %}
    <p>{{ s['note'] }}</p>
    {% if s['learning'] %}<p><em>Lärde mig:</em> {{ s['learning'] }}</p>{% endif %}
    {% if s['role_opportunity'] %}<p><em>Roll/möjlighet:</em> {{ s['role_opportunity'] }}</p>{% endif %}
    {% if s['problem_heard'] %}<p><em>Problem/behov:</em> {{ s['problem_heard'] }}</p>{% endif %}
    {% if s['interest_signal'] %}<p><em>Skapade intresse:</em> {{ s['interest_signal'] }}</p>{% endif %}
    {% if tags_by_signal.get(s['id']) %}
      <p class="tags">
        {% for t in tags_by_signal[s['id']] %}<span class="tag {{ t['category'] }}">{{ t['text'] }}</span>{% endfor %}
      </p>
    {% endif %}
    {% if hyps_by_signal.get(s['id']) %}
      <p class="hyps">
        {% for h in hyps_by_signal[s['id']] %}
          <span class="hyp {{ h['relation'] }}">{{ 'Stödjer' if h['relation'] == 'supports' else 'Motsäger' }}: {{ h['statement'] }}</span>
        {% endfor %}
      </p>
    {% endif %}
    {% if s['next_action'] %}
      <p class="next-action {{ 'done' if s['next_action_done'] else '' }}">
        Nästa steg: {{ s['next_action'] }}
        {% if not s['next_action_done'] %}
          <form method="post" action="{{ url_for('mark_next_action_done', signal_id=s['id']) }}" style="display:inline">
            <button type="submit">Klarmarkera</button>
          </form>
        {% else %}(klar){% endif %}
      </p>
    {% endif %}
    <p><a href="{{ url_for('edit_signal', signal_id=s['id']) }}">Redigera</a></p>
  </li>
{% endfor %}
</ul>
"""


@app.route("/")
@login_required
def feed():
    db = get_supabase()
    user_id = g.user.id
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

    return render_template_string(
        page("Signal Feed", FEED_TEMPLATE),
        signals=signals,
        tags_by_signal=tags_by_signal,
        hyps_by_signal=hyps_by_signal,
    )


@app.route("/signals/<uuid:signal_id>/done", methods=["POST"])
@login_required
def mark_next_action_done(signal_id):
    db = get_supabase()
    db.table("signals").update({"next_action_done": True}).eq("id", str(signal_id)).eq(
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
    <span class="tag role">{{ h['supports_count'] }} stödjer</span>
    <span class="tag problem">{{ h['contradicts_count'] }} motsäger</span>
  </li>
{% endfor %}
</ul>
"""

HYPOTHESIS_DETAIL_TEMPLATE = """
<p><a href="{{ url_for('hypotheses_list') }}">&larr; Alla hypoteser</a></p>
<h1>{{ hyp['statement'] }}</h1>
<form method="post" action="{{ url_for('update_hypothesis_status', hypothesis_id=hyp['id']) }}">
  <label>Status
    <select name="status" onchange="this.form.submit()">
      {% for s in ['exploring', 'strengthening', 'weakening', 'retired'] %}
        <option value="{{ s }}" {% if hyp['status'] == s %}selected{% endif %}>{{ s }}</option>
      {% endfor %}
    </select>
  </label>
</form>

<h2>Stödjande signaler ({{ supporting|length }})</h2>
<ul>
{% for s in supporting %}<li>{{ s['date'] }} — {{ s['person'] }}: {{ s['note'] }}</li>{% endfor %}
</ul>

<h2>Motsägande signaler ({{ contradicting|length }})</h2>
<ul>
{% for s in contradicting %}<li>{{ s['date'] }} — {{ s['person'] }}: {{ s['note'] }}</li>{% endfor %}
</ul>
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
        .select("relation, signals(date, person, note)")
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


REVIEW_TEMPLATE = """
<h1>Veckoöversikt</h1>
<p>{{ week_count }} signaler senaste 7 dagarna.</p>

<h2>Mest frekventa problem-taggar</h2>
<ul>{% for t in top_problem_tags %}<li>{{ t['text'] }} ({{ t['n'] }})</li>{% endfor %}</ul>

<h2>Mest frekventa roll-taggar</h2>
<ul>{% for t in top_role_tags %}<li>{{ t['text'] }} ({{ t['n'] }})</li>{% endfor %}</ul>

<h2>Hypoteser med ny evidens denna vecka</h2>
<ul>
{% for h in hyps_with_new_evidence %}
  <li><a href="{{ url_for('hypothesis_detail', hypothesis_id=h['id']) }}">{{ h['statement'] }}</a> — +{{ h['new_supports'] }} stödjer, +{{ h['new_contradicts'] }} motsäger</li>
{% endfor %}
</ul>

<h2>Obehandlade nästa steg</h2>
<ul>
{% for s in outstanding_actions %}<li>{{ s['date'] }} — {{ s['person'] }}: {{ s['next_action'] }}</li>{% endfor %}
</ul>
"""


@app.route("/review")
@login_required
def review():
    db = get_supabase()
    user_id = g.user.id
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    week_signals = (
        db.table("signals")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", week_ago)
        .order("date", desc=True)
        .execute()
        .data
    )
    week_ids = [s["id"] for s in week_signals]

    top_problem_tags = []
    top_role_tags = []
    hyps_with_new_evidence = []
    if week_ids:
        tag_rows = (
            db.table("signal_tags")
            .select("signal_id, tags(text, category)")
            .in_("signal_id", week_ids)
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
            .in_("signal_id", week_ids)
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
        page("Veckoöversikt", REVIEW_TEMPLATE),
        week_count=len(week_signals),
        top_problem_tags=top_problem_tags,
        top_role_tags=top_role_tags,
        hyps_with_new_evidence=hyps_with_new_evidence,
        outstanding_actions=outstanding_actions,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
