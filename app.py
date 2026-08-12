# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "flask",
# ]
# ///
"""Signals - market discovery for job search.

Kör: uv run app.py
Öppnas på http://localhost:5050 (och från mobilen via laptopens lokala IP,
samma WiFi).
"""
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, g, redirect, render_template_string, request, url_for

DB_PATH = Path(__file__).parent / "signals.db"

app = Flask(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    person TEXT NOT NULL,
    organization TEXT,
    signal_type TEXT NOT NULL,
    role_opportunity TEXT,
    channel TEXT,
    note TEXT NOT NULL,
    learning TEXT,
    problem_heard TEXT,
    interest_signal TEXT,
    next_action TEXT,
    next_action_done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('problem', 'role')),
    UNIQUE(text, category)
);

CREATE TABLE IF NOT EXISTS signal_tags (
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (signal_id, tag_id)
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'exploring'
        CHECK (status IN ('exploring', 'strengthening', 'weakening', 'retired')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS signal_hypotheses (
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    hypothesis_id INTEGER NOT NULL REFERENCES hypotheses(id),
    relation TEXT NOT NULL CHECK (relation IN ('supports', 'contradicts')),
    PRIMARY KEY (signal_id, hypothesis_id)
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


STYLE = """
<style>
  body { font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; color: #222; }
  nav a { margin-right: 0.25rem; padding: 0.6rem 0.5rem; display: inline-block; }
  form label { display: block; margin-bottom: 0.75rem; }
  input, select, textarea { width: 100%; padding: 0.6rem; box-sizing: border-box; font-size: 16px; font-family: inherit; }
  textarea { min-height: 6rem; }
  button { padding: 0.75rem 1.25rem; font-size: 16px; font-family: inherit; border-radius: 6px; min-height: 44px; }
  .btn-primary { width: 100%; margin-top: 0.5rem; }
  fieldset { margin-bottom: 0.75rem; border: 1px solid #ddd; }
  .feed { list-style: none; padding: 0; }
  .feed li { border-bottom: 1px solid #ddd; padding: 1rem 0; }
  .badge { display: inline-block; background: #eee; border-radius: 4px; padding: 0.1rem 0.5rem; font-size: 0.85rem; margin-right: 0.3rem; }
  .tag { display: inline-block; border-radius: 4px; padding: 0.1rem 0.5rem; font-size: 0.8rem; margin-right: 0.3rem; }
  .tag.problem { background: #fde2e2; }
  .tag.role { background: #e2ecfd; }
  .hyp { display: block; font-size: 0.85rem; }
  .hyp.supports { color: #1a7f37; }
  .hyp.contradicts { color: #b3261e; }
  .next-action.done { text-decoration: line-through; color: #888; }
</style>
"""

NAV = """
<nav>
  <a href="{{ url_for('feed') }}">Feed</a>
  <a href="/signals/new">+ Ny signal</a>
  <a href="/hypotheses">Hypoteser</a>
  <a href="/review">Veckoöversikt</a>
</nav>
"""


def page(title, body_template):
    return (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title>{STYLE}</head><body>{NAV}{body_template}</body></html>"
    )


SIGNAL_TYPE_SEED = [
    "kaffe", "lunch", "rekryterarkontakt", "linkedin-meddelande", "jobbannons",
    "intervju", "introduktion", "samtal", "avslag", "konsultuppdrag", "rollförslag",
]
CHANNEL_SEED = [
    "befintlig relation", "introduktion", "rekryterare", "linkedin", "ansökan", "tidigare kollega",
]


def parse_tag_list(raw):
    return [t.strip() for t in raw.split(",") if t.strip()]


def get_or_create_tag(db, text, category):
    text = text.strip().lower()
    row = db.execute(
        "SELECT id FROM tags WHERE text = ? AND category = ?", (text, category)
    ).fetchone()
    if row:
        return row["id"]
    cur = db.execute(
        "INSERT INTO tags (text, category) VALUES (?, ?)", (text, category)
    )
    return cur.lastrowid


def distinct_values(db, column, seed):
    rows = db.execute(
        f"SELECT DISTINCT {column} FROM signals WHERE {column} IS NOT NULL AND {column} != ''"
    ).fetchall()
    values = {r[column] for r in rows}
    values.update(seed)
    return sorted(values)


def resolve_select_or_other(form, select_name, other_name):
    other = (form.get(other_name) or "").strip()
    if other:
        return other
    return (form.get(select_name) or "").strip()


def set_signal_tags(db, signal_id, category, raw_text):
    db.execute(
        """DELETE FROM signal_tags WHERE signal_id = ? AND tag_id IN
           (SELECT id FROM tags WHERE category = ?)""",
        (signal_id, category),
    )
    for text in parse_tag_list(raw_text):
        tag_id = get_or_create_tag(db, text, category)
        db.execute(
            "INSERT OR IGNORE INTO signal_tags (signal_id, tag_id) VALUES (?, ?)",
            (signal_id, tag_id),
        )


def set_signal_hypothesis(db, signal_id, form):
    db.execute("DELETE FROM signal_hypotheses WHERE signal_id = ?", (signal_id,))
    relation = form.get("relation")
    new_hyp_statement = form.get("new_hypothesis", "").strip()
    existing_hyp_id = form.get("hypothesis_id")
    hypothesis_id = None
    if new_hyp_statement:
        existing_hyp = db.execute(
            "SELECT id FROM hypotheses WHERE statement = ?", (new_hyp_statement,)
        ).fetchone()
        if existing_hyp:
            hypothesis_id = existing_hyp["id"]
        else:
            cur2 = db.execute(
                "INSERT INTO hypotheses (statement, status) VALUES (?, 'exploring')",
                (new_hyp_statement,),
            )
            hypothesis_id = cur2.lastrowid
    elif existing_hyp_id:
        hypothesis_id = int(existing_hyp_id)

    if hypothesis_id and relation:
        db.execute(
            "INSERT INTO signal_hypotheses (signal_id, hypothesis_id, relation) VALUES (?, ?, ?)",
            (signal_id, hypothesis_id, relation),
        )


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
def new_signal():
    db = get_db()
    if request.method == "POST":
        form = request.form
        signal_type = resolve_select_or_other(form, "signal_type_select", "signal_type_other")
        channel = resolve_select_or_other(form, "channel_select", "channel_other") or None
        cur = db.execute(
            """INSERT INTO signals
               (date, person, organization, signal_type, role_opportunity, channel,
                note, learning, problem_heard, interest_signal, next_action)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                form["date"],
                form["person"],
                form.get("organization") or None,
                signal_type,
                form.get("role_opportunity") or None,
                channel,
                form["note"],
                form.get("learning") or None,
                form.get("problem_heard") or None,
                form.get("interest_signal") or None,
                form.get("next_action") or None,
            ),
        )
        signal_id = cur.lastrowid

        set_signal_tags(db, signal_id, "problem", form.get("problem_tags", ""))
        set_signal_tags(db, signal_id, "role", form.get("role_tags", ""))
        set_signal_hypothesis(db, signal_id, form)

        db.commit()
        return redirect(url_for("feed"))

    signal_types = distinct_values(db, "signal_type", SIGNAL_TYPE_SEED)
    channels = distinct_values(db, "channel", CHANNEL_SEED)
    hypotheses = db.execute(
        "SELECT id, statement FROM hypotheses WHERE status != 'retired' ORDER BY created_at DESC"
    ).fetchall()
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


@app.route("/signals/<int:signal_id>/edit", methods=["GET", "POST"])
def edit_signal(signal_id):
    db = get_db()
    signal = db.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
    if signal is None:
        return redirect(url_for("feed"))

    if request.method == "POST":
        form = request.form
        signal_type = resolve_select_or_other(form, "signal_type_select", "signal_type_other")
        channel = resolve_select_or_other(form, "channel_select", "channel_other") or None
        db.execute(
            """UPDATE signals SET
               date = ?, person = ?, organization = ?, signal_type = ?, role_opportunity = ?,
               channel = ?, note = ?, learning = ?, problem_heard = ?, interest_signal = ?,
               next_action = ?
               WHERE id = ?""",
            (
                form["date"],
                form["person"],
                form.get("organization") or None,
                signal_type,
                form.get("role_opportunity") or None,
                channel,
                form["note"],
                form.get("learning") or None,
                form.get("problem_heard") or None,
                form.get("interest_signal") or None,
                form.get("next_action") or None,
                signal_id,
            ),
        )

        set_signal_tags(db, signal_id, "problem", form.get("problem_tags", ""))
        set_signal_tags(db, signal_id, "role", form.get("role_tags", ""))
        set_signal_hypothesis(db, signal_id, form)

        db.commit()
        return redirect(url_for("feed"))

    signal_types = distinct_values(db, "signal_type", SIGNAL_TYPE_SEED)
    channels = distinct_values(db, "channel", CHANNEL_SEED)
    hypotheses = db.execute(
        "SELECT id, statement FROM hypotheses WHERE status != 'retired' ORDER BY created_at DESC"
    ).fetchall()

    tag_rows = db.execute(
        """SELECT t.text, t.category FROM signal_tags st
           JOIN tags t ON t.id = st.tag_id
           WHERE st.signal_id = ?""",
        (signal_id,),
    ).fetchall()
    problem_tags_value = ", ".join(r["text"] for r in tag_rows if r["category"] == "problem")
    role_tags_value = ", ".join(r["text"] for r in tag_rows if r["category"] == "role")

    hyp_link = db.execute(
        """SELECT hypothesis_id, relation FROM signal_hypotheses
           WHERE signal_id = ? ORDER BY hypothesis_id DESC LIMIT 1""",
        (signal_id,),
    ).fetchone()

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
def feed():
    db = get_db()
    signals = db.execute(
        "SELECT * FROM signals ORDER BY date DESC, created_at DESC"
    ).fetchall()
    signal_ids = [s["id"] for s in signals]

    tags_by_signal = {}
    hyps_by_signal = {}
    if signal_ids:
        placeholders = ",".join("?" * len(signal_ids))
        tag_rows = db.execute(
            f"""SELECT st.signal_id, t.text, t.category FROM signal_tags st
                JOIN tags t ON t.id = st.tag_id
                WHERE st.signal_id IN ({placeholders})""",
            signal_ids,
        ).fetchall()
        for r in tag_rows:
            tags_by_signal.setdefault(r["signal_id"], []).append(r)

        hyp_rows = db.execute(
            f"""SELECT sh.signal_id, sh.relation, h.statement FROM signal_hypotheses sh
                JOIN hypotheses h ON h.id = sh.hypothesis_id
                WHERE sh.signal_id IN ({placeholders})""",
            signal_ids,
        ).fetchall()
        for r in hyp_rows:
            hyps_by_signal.setdefault(r["signal_id"], []).append(r)

    return render_template_string(
        page("Signal Feed", FEED_TEMPLATE),
        signals=signals,
        tags_by_signal=tags_by_signal,
        hyps_by_signal=hyps_by_signal,
    )


@app.route("/signals/<int:signal_id>/done", methods=["POST"])
def mark_next_action_done(signal_id):
    db = get_db()
    db.execute("UPDATE signals SET next_action_done = 1 WHERE id = ?", (signal_id,))
    db.commit()
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
def hypotheses_list():
    db = get_db()
    rows = db.execute(
        """SELECT h.*,
                  SUM(CASE WHEN sh.relation = 'supports' THEN 1 ELSE 0 END) AS supports_count,
                  SUM(CASE WHEN sh.relation = 'contradicts' THEN 1 ELSE 0 END) AS contradicts_count
           FROM hypotheses h
           LEFT JOIN signal_hypotheses sh ON sh.hypothesis_id = h.id
           GROUP BY h.id
           ORDER BY h.created_at DESC"""
    ).fetchall()
    return render_template_string(page("Hypoteser", HYPOTHESES_LIST_TEMPLATE), hypotheses=rows)


@app.route("/hypotheses/<int:hypothesis_id>")
def hypothesis_detail(hypothesis_id):
    db = get_db()
    hyp = db.execute("SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)).fetchone()
    evidence = db.execute(
        """SELECT s.*, sh.relation FROM signal_hypotheses sh
           JOIN signals s ON s.id = sh.signal_id
           WHERE sh.hypothesis_id = ?
           ORDER BY s.date DESC""",
        (hypothesis_id,),
    ).fetchall()
    supporting = [e for e in evidence if e["relation"] == "supports"]
    contradicting = [e for e in evidence if e["relation"] == "contradicts"]
    return render_template_string(
        page("Hypotes", HYPOTHESIS_DETAIL_TEMPLATE),
        hyp=hyp,
        supporting=supporting,
        contradicting=contradicting,
    )


@app.route("/hypotheses/<int:hypothesis_id>/status", methods=["POST"])
def update_hypothesis_status(hypothesis_id):
    db = get_db()
    status = request.form["status"]
    db.execute("UPDATE hypotheses SET status = ? WHERE id = ?", (status, hypothesis_id))
    db.commit()
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
def review():
    db = get_db()
    week_signals = db.execute(
        "SELECT * FROM signals WHERE date >= date('now', '-7 days') ORDER BY date DESC"
    ).fetchall()
    week_ids = [s["id"] for s in week_signals]

    top_problem_tags = []
    top_role_tags = []
    hyps_with_new_evidence = []
    if week_ids:
        placeholders = ",".join("?" * len(week_ids))
        top_problem_tags = db.execute(
            f"""SELECT t.text, COUNT(*) AS n FROM signal_tags st
                JOIN tags t ON t.id = st.tag_id
                WHERE st.signal_id IN ({placeholders}) AND t.category = 'problem'
                GROUP BY t.text ORDER BY n DESC LIMIT 10""",
            week_ids,
        ).fetchall()
        top_role_tags = db.execute(
            f"""SELECT t.text, COUNT(*) AS n FROM signal_tags st
                JOIN tags t ON t.id = st.tag_id
                WHERE st.signal_id IN ({placeholders}) AND t.category = 'role'
                GROUP BY t.text ORDER BY n DESC LIMIT 10""",
            week_ids,
        ).fetchall()
        hyps_with_new_evidence = db.execute(
            f"""SELECT h.id, h.statement, h.status,
                       SUM(CASE WHEN sh.relation = 'supports' THEN 1 ELSE 0 END) AS new_supports,
                       SUM(CASE WHEN sh.relation = 'contradicts' THEN 1 ELSE 0 END) AS new_contradicts
                FROM signal_hypotheses sh
                JOIN hypotheses h ON h.id = sh.hypothesis_id
                WHERE sh.signal_id IN ({placeholders})
                GROUP BY h.id""",
            week_ids,
        ).fetchall()

    outstanding_actions = db.execute(
        """SELECT * FROM signals
           WHERE next_action IS NOT NULL AND next_action != '' AND next_action_done = 0
           ORDER BY date DESC"""
    ).fetchall()

    return render_template_string(
        page("Veckoöversikt", REVIEW_TEMPLATE),
        week_count=len(week_signals),
        top_problem_tags=top_problem_tags,
        top_role_tags=top_role_tags,
        hyps_with_new_evidence=hyps_with_new_evidence,
        outstanding_actions=outstanding_actions,
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5050, debug=False)
