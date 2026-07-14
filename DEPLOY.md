# Deploying to Hugging Face Spaces (free)

The whole app ships as **one Docker container**: the Next.js frontend is
statically exported and served by FastAPI alongside the API, so the browser
talks to a single origin (no CORS, one URL).

Hugging Face Spaces gives you free Docker hosting. The database lives outside
the Space, on Neon's free PostgreSQL tier.

> **Why an external database?** Free HF Spaces have an **ephemeral filesystem**.
> Any file the container writes is destroyed when the Space restarts, sleeps, or
> rebuilds. A SQLite file there would silently lose every product, sale and user
> account. Neon persists.

---

## 1. Create the database (Neon — free, no card)

1. Sign up at <https://neon.tech> and create a project.
2. Copy the connection string. It looks like:

   ```
   postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

Keep it handy — this is your `DATABASE_URL`.

The app normalizes `postgres://` → `postgresql+psycopg2://` automatically, so
either form Neon gives you will work.

## 2. Generate a JWT secret

Anyone who knows your signing key can forge a login token for any account, so
this must be a fresh random value — never the default in `.env.example`.

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The app **refuses to boot** in production with the default or a short (<32 char)
secret, and refuses to boot on SQLite. Those are hard failures by design.

## 3. Create the Space

1. Go to <https://huggingface.co/new-space>.
2. Pick a name, license, and **SDK = Docker** (blank template).
3. Hardware: **CPU basic (free)**.
4. Visibility: public or private — both are free.

## 4. Set the Space secrets

In the Space: **Settings → Variables and secrets → New secret**.

| Name             | Value                                        | Required |
| ---------------- | -------------------------------------------- | -------- |
| `DATABASE_URL`   | your Neon connection string                  | **yes**  |
| `JWT_SECRET_KEY` | the secret you generated in step 2           | **yes**  |
| `GROQ_API_KEY`   | a Groq key, to enable LLM phrasing           | no       |

`ENVIRONMENT=production`, `STATIC_DIR` and `PORT=7860` are already baked into
the `Dockerfile` — you do not need to set them.

Add these as **secrets**, not public variables, so they aren't exposed in the
Space's build logs or repo.

## 5. Push the code

The Space is a git repo. From the project root:

```bash
git init
git add .
git commit -m "AI inventory management system"

# Replace <user>/<space-name> with your Space
git remote add space https://huggingface.co/spaces/<user>/<space-name>
git push space main
```

If your branch is called `master`, push `master:main` instead.

HF will build the `Dockerfile` and start the Space. First build takes a few
minutes (it installs npm and pip deps). Watch the **Logs** tab.

On startup the container runs `alembic upgrade head`, which creates the schema
in your Neon database. You should see:

```
Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> a07ca653d78b, initial schema
Starting server on port 7860...
```

## 6. First login

Open the Space URL and go to **/register** to create your account. The first
account is a normal user — there is no separate admin role yet.

## 7. (Optional) Seed demo data

The Space has no shell, so seed **from your machine against the Neon database**:

```bash
cd backend
DATABASE_URL="<your neon url>" python seed_demo.py
```

> ⚠️ `seed_demo.py` **deletes** all existing products, categories, suppliers,
> customers and sales before inserting demo rows. It leaves user accounts alone.
> Do not run it against a database that has real data you care about.

---

## Local development (unchanged)

Deployment does not change the local workflow — the two servers still run
separately, and `next dev` ignores the static-export config.

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev        # http://localhost:3000
```

`frontend/.env.local` points the dev frontend at `http://localhost:8000`. In the
container that variable is empty, which means "same origin".

## Running the production image locally

Requires Docker (not currently installed on this machine):

```bash
docker build -t inventory .
docker run --rm -p 7860:7860 \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" \
  inventory
# → http://localhost:7860
```

## What's hardened

| Concern            | Handling                                                        |
| ------------------ | --------------------------------------------------------------- |
| Schema changes     | Alembic migrations; `create_all` is disabled in production       |
| Weak JWT secret    | App refuses to boot in production                                |
| SQLite in prod     | App refuses to boot                                              |
| Credential stuffing| `10/minute` per-IP limit on `/api/auth/login` and `/register`    |
| Container user     | Runs as non-root `appuser` (uid 1000)                            |
| Secrets in image   | `.dockerignore` excludes `.env`, `*.db`, `node_modules`, `.venv` |
| Liveness           | Docker `HEALTHCHECK` against `/api/health`                       |

## Known limitations

- **Free Spaces sleep** after inactivity. The first request after a sleep is
  slow while the container wakes.
- **Rate limiting is in-memory**, so limits are per-process. Correct for this
  single-container deployment; a multi-replica setup needs Redis.
- **The JWT is stored in `localStorage`**, which is readable by any XSS on the
  page. Fine for an internal tool; move to an httpOnly cookie before exposing
  this to untrusted users.
- **The Docker image has not been built locally** (Docker isn't installed on the
  dev machine). Its individual parts are verified — the static export builds,
  `requirements.txt` installs into a clean venv, migrations apply, and FastAPI
  serves the export and the API on one origin — but the first real build happens
  on HF. Check the Logs tab if it fails.
