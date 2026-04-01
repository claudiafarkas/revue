# Revue.ai

Revue.ai is a career review tool: paste job postings, upload a resume, and get a structured alignment report with matched skills, missing signals, and concrete recommendations.
![1775005577414](image/README/1775005577414.png)

## System Flow

```mermaid
flowchart TD
		U[User Browser]
		FE[Frontend Next.js]
		BE[Backend FastAPI]
		DB[(PostgreSQL)]
		AF[Airflow DAG revue_processing_pipeline]
		GM[Gemini 2.0 Flash]

		U --> FE
		FE -->|POST /api/job-postings| BE
		FE -->|POST /api/resume/upload| BE
		FE -->|POST /api/resume/trigger| BE
		FE -->|GET /api/report/:job_id/status| BE
		FE -->|GET /api/report/:job_id/content| BE

		BE --> DB
		BE -->|Trigger DAG run with job_id| AF

		AF -->|read postings + resume + write report_json| DB
		AF -->|LLM analysis prompt| GM
		GM -->|structured JSON response| AF
```

## File Communication Map

```mermaid
flowchart LR
		subgraph Frontend
			JPP[src/pages/JobPostingsPage.tsx]
			RUP[src/pages/ResumeUploadPage.tsx]
			PRP[src/pages/ProcessingPage.tsx]
			REP[src/pages/ReportPage.tsx]
			API[src/utils/api.ts]
		end

		subgraph Backend
			MAIN[backend/api/main.py]
			JR[backend/api/routes/job_postings.py]
			RR[backend/api/routes/resume.py]
			RPR[backend/api/routes/report.py]
			DBS[backend/api/services/database.py]
			ATS[backend/api/services/airflow_trigger.py]
		end

		subgraph Airflow
			DAG[airflow/dags/revue_pipeline.py]
			T1[airflow/tasks/compare_resume.py]
			T2[airflow/tasks/llm_analysis.py]
			T3[airflow/tasks/generate_report.py]
			T4[airflow/tasks/store_output.py]
		end

		JPP --> API
		RUP --> API
		PRP --> API
		REP --> API

		API --> JR
		API --> RR
		API --> RPR

		MAIN --> JR
		MAIN --> RR
		MAIN --> RPR

		JR --> DBS
		RR --> DBS
		RPR --> DBS
		RR --> ATS
		ATS --> DAG

		DAG --> T1 --> T2 --> T3 --> T4
		T4 --> DBS
```

## Pipeline Stages (Current)

```mermaid
flowchart LR
		A[extract_resume_text_step]
		B[build_initial_payload]
		C[clean_step]
		D[resume_features_step]
		E[compare_step - heuristic overlap]
		F[llm_analysis_step - Gemini skills + narrative]
		G[embeddings_step - hashed vector similarity]
		H[report_step - assemble report_json]
		I[store_step - persist report]

		A --> B --> C --> D --> E --> F --> G --> H --> I
```

`llm_analysis_step` is fallback-safe. If `GEMINI_API_KEY` is not set (or `google-genai` is unavailable), the pipeline continues with heuristic comparison output.

## Report JSON Shape

```mermaid
flowchart TD
		R[report_json]
		R --> S[summary: match_score, embedding_similarity, fit_label]
		R --> H[highlights: matched/missing/resume/posting keywords, tools, domains]
		R --> N[narrative: overview, strengths_summary, gaps_summary, level hints]
		R --> C[recommendations]
```

## Repository Layout

```text
revue/
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── context/
│       ├── styles/
│       └── utils/
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── services/
│   └── migrations/
├── airflow/
│   ├── dags/
│   └── tasks/
├── vector_db/
├── infra/
│   ├── docker-compose.yml
│   └── terraform/
├── Makefile
└── README.md
```

## Local Development

Start services from the repo root:

```bash
make db-up
make db-migrate
make backend-dev
make frontend-dev
```

Useful defaults:

- Frontend: `http://localhost:3101`
- Backend: `http://127.0.0.1:8011`
- Backend docs: `http://127.0.0.1:8011/docs`
- Database: `localhost:5434`

Install/update Airflow Python dependencies (after `airflow/requirements.txt` changes):

```bash
docker compose -f infra/docker-compose.yml build airflow
docker compose -f infra/docker-compose.yml up -d airflow
```

To enable LLM analysis in pipeline runs:

```bash
export GEMINI_API_KEY=your_key_here
```

## Notes

- Frontend report download now uses a clean print document generated from `buildPreviewHtml` in `ReportPage.tsx`.
- `compare_step` still provides deterministic baseline behavior.
- `llm_analysis_step` upgrades extracted skills and narrative quality when available.