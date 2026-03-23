## What this project is

This repo is a small monorepo for **municipal data analytics**:

- **`apps/api`**: FastAPI backend
  - Accepts Excel uploads
  - Creates a `Project` + `Run` in Postgres
  - Enqueues background processing jobs via **Redis + RQ**
  - Serves run status + artifacts metadata
- **`apps/worker`**: RQ worker
  - Pulls the uploaded Excel files from S3-compatible storage (MinIO)
  - Produces artifacts (currently: `standardized.parquet`, `profile.json`)
  - Writes artifact records + run status into Postgres
- **`apps/web`**: React + Vite frontend
  - Upload page calls `POST /api/upload`
  - Projects page lists `GET /api/projects`

The intended runtime is **Docker Compose** (Redis + Postgres + MinIO + API + Worker + Web).

## How to run (recommended)

### Prerequisites

- Docker Desktop installed and **running**
  - If you see `failed to connect to the docker API ... dockerDesktopLinuxEngine`, start Docker Desktop first.

### Start the stack

From the repo root:

```bash
docker compose up --build
```

Then open:

- Web UI: `http://localhost:5173`
- API: `http://localhost:8000` (health: `GET /health`, API health: `GET /api/health`)
- MinIO console: `http://localhost:9001` (user/pass are in `.env`)

## Useful API endpoints

- `POST /api/upload` (multipart form, field name **`files`**): convenience endpoint used by the current UI
  - creates a project, stores uploads, creates a run, enqueues the worker job
- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `POST /api/projects/{project_id}/runs` (JSON body: `upload_ids: string[]`)
- `GET /api/runs/{run_id}`
- `GET /api/job/{job_id}`
