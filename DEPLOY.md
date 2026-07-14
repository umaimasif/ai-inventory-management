# Deploying (free) — Vercel + Neon

Both the frontend and the API run on **one Vercel project, one domain**:

- the Next.js frontend is served by Vercel,
- the FastAPI backend runs as a **Python serverless function** at `/api/*`
  (see [`api/index.py`](api/index.py) and [`vercel.json`](vercel.json)),
- the database is **Neon** free PostgreSQL.

Because both live on the same domain, the browser makes same-origin requests and
CORS never comes into it.

Vercel's **Hobby** plan and Neon's free tier both cost nothing and need no card.

> **Note on Hugging Face.** This project also ships a working `Dockerfile` for a
> single-container deployment. It is *not* used on HF Spaces any more: HF now
> returns `402 Payment Required` for Docker Spaces on free hardware — only
> *Static* Spaces are free, and Docker requires a PRO subscription. The
> Dockerfile still works on any Docker host (see the bottom of this file).

---

## 1. Create the database (Neon — free, no card)

1. Sign up at <https://neon.tech> and create a project.
2. Copy the **pooled** connection string (Neon shows a "Pooled connection"
   toggle — use it; serverless functions open many short-lived connections).

   It looks like:

   ```
   postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
   ```

Keep it handy — this is your `DATABASE_URL`. The app rewrites `postgres://` to
`postgresql+psycopg2://` automatically, so either form works.

## 2. Generate a JWT secret

Anyone who knows the signing key can forge a login token for any account, so
this must be a fresh random value — never the placeholder in `.env.example`.

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The app **refuses to boot** in production with the default or a short (<32 char)
secret, and refuses to run on SQLite. Those are deliberate hard failures.

## 3. Create the schema

Vercel functions are stateless, so migrations are not run at deploy time. Apply
them once from your machine, pointing at Neon:

```bash
cd backend
DATABASE_URL="<your neon url>" python -m alembic upgrade head
```

You should see `Running upgrade -> a07ca653d78b, initial schema`. Re-run this
command any time new migrations are added.

## 4. Import the project on Vercel

1. Go to <https://vercel.com/new> and sign in with GitHub.
2. Import **`umaimasif/ai-inventory-management`**.
3. Leave the Root Directory as the repository root — `vercel.json` already
   describes how to build both parts. Do **not** set it to `frontend`.
4. Before clicking Deploy, add the environment variables below.

### Environment variables

Add these under **Settings → Environment Variables** (apply to Production):

| Name             | Value                                   | Required |
| ---------------- | --------------------------------------- | -------- |
| `ENVIRONMENT`    | `production`                            | **yes**  |
| `DATABASE_URL`   | your Neon pooled connection string      | **yes**  |
| `JWT_SECRET_KEY` | the secret from step 2                  | **yes**  |
| `GROQ_API_KEY`   | a Groq API key — enables LLM phrasing   | no       |

Leave `NEXT_PUBLIC_API_URL` **unset**. Empty means "same origin", which is
exactly right here.

If `ENVIRONMENT=production` is set without a valid `DATABASE_URL` and
`JWT_SECRET_KEY`, the function will fail to start — by design. Check the
function logs and you'll see precisely which check failed.

## 5. Deploy

Click **Deploy**. Vercel builds the Next.js app and the Python function.

Then open the URL and go to **/register** to create the first account. There is
no separate admin role — the first user is a normal user.

Pushing to `main` on GitHub redeploys automatically.

## 6. (Optional) Seed demo data

Run it from your machine against Neon:

```bash
cd backend
DATABASE_URL="<your neon url>" python seed_demo.py
```

> ⚠️ `seed_demo.py` **deletes** all existing products, categories, suppliers,
> customers and sales before inserting demo rows. User accounts are left alone.
> Never run it against data you care about.

---

## Local development (unchanged)

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev        # http://localhost:3000
```

`frontend/.env.local` points the dev frontend at `http://localhost:8000`. In
production that variable is absent, which means "same origin".

## What's hardened

| Concern             | Handling                                                     |
| ------------------- | ------------------------------------------------------------ |
| Schema changes      | Alembic migrations; `create_all` is disabled in production    |
| Weak JWT secret     | App refuses to boot in production                             |
| SQLite in prod      | App refuses to boot                                           |
| Credential stuffing | `10/minute` per-IP limit on `/api/auth/login` and `/register` |
| Secrets in git      | `.gitignore` excludes `.env`, `*.db`, `.venv`, `node_modules` |

## Known limitations

- **Cold starts.** A serverless function that hasn't run recently takes a second
  or two to wake up. Hobby-plan functions also have a 10s execution limit — fine
  for these endpoints, which are all fast queries.
- **Rate limiting is in-memory**, so it is per-function-instance rather than
  global. It still blunts naive credential stuffing but is not a strict global
  limit. A shared Redis backend would be needed for that.
- **The JWT is stored in `localStorage`**, readable by any XSS on the page.
  Acceptable for an internal tool; move to an httpOnly cookie before exposing
  this to untrusted users.
- **Migrations are manual** (step 3). They are not run automatically on deploy.

## Alternative: any Docker host

The `Dockerfile` builds a single container that statically exports the frontend
and serves it from FastAPI alongside the API on port 7860.

```bash
docker build -t inventory .
docker run --rm -p 7860:7860 \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" \
  inventory
# → http://localhost:7860
```

It runs migrations on start, runs as a non-root user, and has a healthcheck.
Works on Fly.io, a VPS, or an HF Space **with a PRO subscription**. It has not
been built on this machine (Docker isn't installed here), so the first real
build will be its first test.
