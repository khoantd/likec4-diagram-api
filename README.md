# LikeC4 Diagram API

FastAPI backend for generating **LikeC4** diagrams in D2, Mermaid, and PlantUML from a processed view JSON. Built with the Python backend template (FastAPI, Pydantic, Docker, pytest).

## Project overview

- **POST** `/api/v1/generate/d2` – generate D2 diagram
- **POST** `/api/v1/generate/mermaid` – generate Mermaid diagram  
- **POST** `/api/v1/generate/puml` – generate PlantUML diagram
- **POST** `/api/v1/generate/{format}` – generate by format (`d2`, `mermaid`, `puml`)
- **POST** `/api/v1/ai/generate` – **(optional)** generate LikeC4 DSL from natural language using AI
- **GET** `/health` – health check
- **GET** `/docs` – OpenAPI (Swagger) docs

The request body is a **LikeC4 processed view** (nodes, edges, autoLayout). The generators mirror the logic in the LikeC4 monorepo (`@likec4/generators`) so output is compatible with D2/Mermaid/PlantUML tooling.

## Setup

- Python **3.11+**
- Create a virtualenv and install:

```bash
cd devops/likec4-diagram-api
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

Then copy the example configuration file and adjust it:

```bash
cp .env.example .env
```

## Running locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or:

```bash
make run
```

Then open http://localhost:8000/docs to try the API.

## Docker deployment

```bash
docker compose up --build
```

API is at http://localhost:8000. Health check: http://localhost:8000/health.

## Testing

```bash
pytest -v
# or
make test
```

## Turso database integration (optional)

This service can integrate with a **Turso** (libSQL) database using the `pyturso`
package. Turso is optional and disabled by default.

### Enable Turso

1. Install dependencies (already included in `pyproject.toml`):

```bash
pip install -e ".[dev]"
```

2. Configure environment variables (for example in `.env` or Docker):

| Variable | Description |
|----------|-------------|
| `LIKEC4_API_TURSO_ENABLED` | Set to `true` to enable Turso integration |
| `LIKEC4_API_TURSO_DB_PATH` | Local SQLite file path or `:memory:` (default `:memory:`) |
| `LIKEC4_API_TURSO_REMOTE_URL` | Optional Turso remote URL (used as `remote_url` for embedded replica sync) |
| `LIKEC4_API_TURSO_AUTH_TOKEN` | Optional auth token for the remote Turso database |

When `LIKEC4_API_TURSO_REMOTE_URL` / `LIKEC4_API_TURSO_AUTH_TOKEN` are not set,
the service also looks at the standard Turso environment variables:

- `LIBSQL_URL`
- `LIBSQL_AUTH_TOKEN`

On startup the app initialises a process-wide Turso connection using
`turso.sync.connect(...)` and closes it on shutdown. You can obtain the
connection in your own code via `app.services.db.get_turso_connection()`.

## API reference

### Request body (processed view)

Send a JSON body with:

| Field       | Type   | Description                          |
|------------|--------|--------------------------------------|
| `nodes`    | array  | `{ id, parent?, title, children[], shape }` |
| `edges`    | array  | `{ source, target, label? }`          |
| `autoLayout` | object | `{ direction: "TB" \| "BT" \| "LR" \| "RL" }` (default `TB`) |

Example:

```json
{
  "nodes": [
    { "id": "user", "parent": null, "title": "User", "children": [], "shape": "person" },
    { "id": "system", "parent": null, "title": "System", "children": ["system.api"], "shape": "rectangle" },
    { "id": "system.api", "parent": "system", "title": "API", "children": [], "shape": "rectangle" }
  ],
  "edges": [
    { "source": "user", "target": "system.api", "label": "uses" }
  ],
  "autoLayout": { "direction": "TB" }
}
```

Response is plain text (D2, Mermaid, or PlantUML source).

### AI-generated LikeC4 DSL (optional)

To let the API generate **LikeC4 source code** from a short description, enable AI and install the optional dependency:

```bash
pip install -e ".[ai,dev]"
```

Set environment variables (e.g. in `.env` or Docker):

| Variable | Description |
|----------|-------------|
| `LIKEC4_API_AI_ENABLED` | Set to `true` to enable the AI endpoint |
| `LIKEC4_API_OPENAI_API_KEY` | API key (use a placeholder like `sk-1234` if your proxy does not validate) |
| `LIKEC4_API_OPENAI_BASE_URL` | Optional. OpenAI-compatible base URL (e.g. Azure OpenAI) |
| `LIKEC4_API_LITELLM_BASE_URL` | **LiteLLM proxy** base URL (e.g. `https://litellm.example.com/v1`). When set, all AI requests go to this URL; overrides `OPENAI_BASE_URL` |
| `LIKEC4_API_AI_MODEL` | Model name (default: `gpt-4o-mini`). For LiteLLM use provider prefix, e.g. `openai/gpt-4o`, `anthropic/claude-3-5-sonnet` |

**Using LiteLLM proxy**

Point the AI service at your LiteLLM proxy so you can use any supported model (OpenAI, Anthropic, local LLMs, etc.):

```bash
# .env or environment
LIKEC4_API_AI_ENABLED=true
LIKEC4_API_LITELLM_BASE_URL=https://your-litellm-host.com/v1   # or http://localhost:4000/v1 for local
LIKEC4_API_OPENAI_API_KEY=sk-1234   # placeholder if LiteLLM does not require a key
LIKEC4_API_AI_MODEL=openai/gpt-4o    # or anthropic/claude-3-5-sonnet, etc.
```

The API uses the OpenAI client with your LiteLLM base URL; no code changes are required beyond configuration.

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A customer actor uses a web app; the app has an API and a database."}'
```

Response:

```json
{
  "likec4_dsl": "model { ... }\nviews { ... }",
  "explanation": null
}
```

Use the returned `likec4_dsl` in a `.likec4` or `.c4` file, or feed it to the diagram generators (e.g. after parsing with the LikeC4 language server) to get D2/Mermaid/PlantUML.

## Optional next steps

- Add **API key** or **JWT** auth for production (see Python backend template `auth_method`).
- Add **Redis** or **SQLite** to cache generated diagrams by view hash.
- Add **CI/CD** (e.g. GitHub Actions: lint, test, build Docker image).
- Integrate with the monorepo’s `@likec4/generators` via a small Node helper for pixel-perfect parity with the TS implementation.
