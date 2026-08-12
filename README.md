# Signals

A personal field journal for job-market discovery. Capture short signals — a coffee meeting, a recruiter's LinkedIn message, an interview, a lunch with a former colleague — and link them to evolving hypotheses about what the market actually wants. The goal is learning, not pipeline tracking: a conversation that produces no job opportunity but a sharp insight is worth more here than an application with none.

Live at **[signals-market-discovery.vercel.app](https://signals-market-discovery.vercel.app)**.

See [`HYPOTHESIS.md`](./HYPOTHESIS.md) for the experiment framing — what this is meant to prove and how success is measured.

## Core workflow

1. Log in
2. Capture a signal in under two minutes: who, what happened, what you learned, optional tags, and an optional link to a hypothesis it supports or contradicts
3. Browse the feed to re-read past signals, edit any of them, or mark a next step done
4. Check the weekly review for recurring tags and hypotheses that gained new evidence

## Tech stack

- **[Flask](https://flask.palletsprojects.com/)** — single-file app (`app.py`), server-rendered HTML, no build step, no client-side framework
- **[Supabase](https://supabase.com/)** — Postgres for storage, Auth for login, Row Level Security as the actual access boundary (each user can only ever see their own rows)
- **[Vercel](https://vercel.com/)** — zero-config Flask deployment, auto-deploys on push to `main`

## Running locally

Requires [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
# fill in SUPABASE_URL, SUPABASE_ANON_KEY, FLASK_SECRET_KEY

uv run app.py
```

Open http://localhost:5050. Accounts are created by hand in the Supabase dashboard — there's no public sign-up.

## Deployment

Pushing to `main` on GitHub triggers an automatic production deploy on Vercel. Environment variables (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `FLASK_SECRET_KEY`) are configured in the Vercel project settings, separate from local `.env`.

For architecture notes, known gotchas, and guidance for working in this codebase, see [`CLAUDE.md`](./CLAUDE.md).
