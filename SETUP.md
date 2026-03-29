# Quick Setup

Canonical contributor setup now lives in [docs/development.md](docs/development.md).
Use the `uv` + `npm ci` flow there unless you have a deployment-specific reason
to do otherwise.

## Docker (recommended)

```bash
git clone https://github.com/contractorr/stewardme.git && cd stewardme
cp .env.example .env   # then fill in SECRET_KEY, NEXTAUTH_SECRET, and at least one OAuth provider
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). The first-run wizard walks you through LLM provider setup and profile onboarding.

### Generate required secrets

```bash
# SECRET_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# NEXTAUTH_SECRET
openssl rand -base64 32
```

### OAuth setup

You need at least one OAuth provider for login:

- **GitHub**: [Create OAuth app](https://github.com/settings/developers) — callback URL: `http://localhost:3000/api/auth/callback/github`
- **Google**: [Create credentials](https://console.cloud.google.com/apis/credentials) — callback URL: `http://localhost:3000/api/auth/callback/google`

## Local development (no Docker)

```bash
# Backend
uv sync --frozen --extra dev --extra web --extra all-providers
uv run uvicorn src.web.app:app --reload --port 8000

# Frontend (separate terminal)
npm --prefix web run dev
```

Configure `web/.env.local` with OAuth vars + `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Production

Use `docker-compose.prod.yml` with Caddy for auto-HTTPS:

```bash
cp .env.example .env  # fill in DOMAIN + all secrets
docker compose -f docker-compose.prod.yml up -d
```

See `Caddyfile` for reverse proxy config.
