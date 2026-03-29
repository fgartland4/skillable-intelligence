# Skillable Intelligence

A unified platform for evaluating, designing, and discovering Skillable lab program opportunities.

## Tools

| Tool | Path | Audience | Status |
|---|---|---|---|
| **Inspector** | `/inspector` | Sales / Solution Engineers | Live |
| **Designer** | `/designer` | Learning Consultants / PS / Customers | Phase 3 |
| **Prospector** | `/prospector` | Marketing | Phase 4 |

## Local Development

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000/inspector

## Environment Variables

Copy `.env.example` to `backend/.env` and fill in:

```
ANTHROPIC_API_KEY=your_key_here
SERPER_API_KEY=your_key_here   # optional, improves search quality
```

## Deployment

Deployed to Render via `render.yaml`. Push to `main` → auto-deploys.

Future production URL: `intelligence.skillable.com`

## Architecture

- **Backend:** Python / Flask (`backend/`)
- **Templates:** Per-tool in `tools/{inspector,designer,prospector}/templates/`
- **Static:** Shared CSS/JS/images in `static/`
- **Storage:** JSON files locally (`storage/`) → Azure SQL in production
- **Auth:** API key now, Entra ID later (abstracted in `backend/auth.py`)

## Prior Repos

- `fgartland4/labability-engine` → archived, migrated here as Inspector
- `fgartland4/lab-designer` → archived, migrated here as Designer (Phase 3)
