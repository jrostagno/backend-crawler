# backend-crawler

Backend challenge built with FastAPI using layered architecture:
`controller -> service -> repository -> client`.

## Architecture

- `app/controllers`: HTTP endpoints (`POST /crawl`, `GET /words/top`)
- `app/services`: business orchestration and validations
- `app/repositories`: persistence operations over Redis
- `app/clients`: external integrations (Amazon HTTP fetch + Redis connection)
- `app/core`: config and text normalization utilities

## Requirements

- Python 3.12+ (tested on 3.14)
- Redis running locally

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Redis (Docker)

```bash
docker run --name crawler-redis -p 6379:6379 -d redis:7
```

## Run API

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

## Run with Docker (one command)

From project root:

```bash
docker compose up --build
```

API will be available at `http://localhost:8000`.

Useful commands:

```bash
docker compose down
docker compose logs -f backend
```

## Environment variables

All variables are optional and use defaults if not provided.

- `CRAWLER_APP_NAME=Backend Challenge API`
- `CRAWLER_REDIS_URL=redis://localhost:6379/0`
- `CRAWLER_REDIS_SEEN_PREFIX=crawler:seen`
- `CRAWLER_REDIS_WORD_SCORES_KEY=crawler:word_scores`
- `CRAWLER_CRAWL_TIMEOUT_SECONDS=10`
- `CRAWLER_CRAWL_USER_AGENT=Mozilla/5.0 (...)`
- `CRAWLER_REQUEST_RETRIES=2`
- `CRAWLER_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
- `CRAWLER_LOG_LEVEL=INFO`
- `CRAWLER_ENV=development`

## API examples

### Crawl one product URL

```bash
curl -X POST "http://localhost:8000/crawl?productUrl=https%3A%2F%2Fwww.amazon.com%2Fgp%2Fproduct%2FB00VVOCSOU"
```

### Get top words

```bash
curl "http://localhost:8000/words/top?limit=10"
```

## Run tests

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```
