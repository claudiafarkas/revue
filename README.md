# Revue.ai

Revue.ai is a calm, editorial-style career review product. The current repository contains a working frontend prototype and placeholder scaffolding for the backend, orchestration, vector storage, and infrastructure layers that will be added later.

## Repository Layout

```text
revue/
├── frontend/
│   ├── pages/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── styles/
│   │   └── utils/
│   ├── next-env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── node_modules/
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── airflow/
│   ├── dags/
│   ├── tasks/
│   └── Dockerfile
├── vector_db/
│   ├── embeddings.py
│   ├── init.py
│   └── queries.py
├── infra/
│   ├── docker-compose.yml
│   └── terraform/
├── Makefile
└── README.md
```

## Current Status

- The frontend is implemented now and lives in `frontend/`.
- The frontend is now served by the Next.js dev server.
- The backend now has a minimal FastAPI shell with route registration, health checks, and stub endpoints for job postings, resume upload, and report status.
- Airflow, vector database, and infrastructure areas remain scaffold-only by design.
- The frontend uses TypeScript and `.tsx` files, even though the original desired shape referenced `.jsx`. Wrapper files are included where helpful so the structure stays close to the intended product layout without rewriting the current implementation.

## Frontend Prototype Flow

The current UI includes:

1. Home / Get Started page
2. Job posting input page
3. Resume upload page
4. Processing page with staged progress
5. Report page with editorial report sections

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

To create a production build:

```bash
cd frontend
npm run build
```

## Run From The Repo Root

Use the root Makefile for common development commands:

```bash
make frontend-install
make frontend-dev
make backend-install
make backend-dev
```

Other convenience targets:

```bash
make frontend-build
make backend-run
make help
```

The backend commands use your currently active Python environment (for you, Anaconda base), and frontend commands use a repo-local npm cache under `frontend/.npm-cache`.

Frontend defaults to `http://localhost:3101` on `make frontend-dev`.
Backend defaults to `http://127.0.0.1:8011` on `make backend-dev`.
The backend serves FastAPI docs at `/docs` and a basic health endpoint at `/health`.

## Planned Backend Responsibilities

- `backend/api/`: FastAPI application, routes, schemas, models, and services
- `airflow/`: DAGs and task modules for the Revue analysis pipeline
- `vector_db/`: embeddings and query helpers for semantic comparison and retrieval
- `infra/`: local orchestration and future infrastructure provisioning

## Notes

- The backend endpoints currently return stub responses and do not persist data yet.
- Airflow, Terraform, and vector database implementation is intentionally left for later.
- The working UI was preserved while the repo was reorganized around the longer-term architecture.