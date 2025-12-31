# ChromaDB Vector Storage

A standalone vector storage API using ChromaDB and Ollama for embeddings.

## Quick Start

```bash
# 1. Copy to tk-lenovo
scp -r chroma-db tk-lenovo@192.168.1.154:~/

# 2. SSH to tk-lenovo
ssh tk-lenovo@192.168.1.154

# 3. Start services
cd ~/chroma-db
docker compose up -d --build

# 4. Test health
curl http://localhost:8080/health
```

## Endpoints

| Endpoint         | Method | Description                 |
| ---------------- | ------ | --------------------------- |
| `/health`        | GET    | Health check                |
| `/write/global`  | POST   | Write to global collection  |
| `/write/project` | POST   | Write to project collection |
| `/query/global`  | POST   | Query global collection     |
| `/query/project` | POST   | Query project collection    |

## Usage Examples

### Write Global

```bash
curl -X POST "http://localhost:8080/write/global" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "metadata": {}}'
```

### Query Global

```bash
curl -X POST "http://localhost:8080/query/global" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "hello", "top_k": 5}'
```

### Write Project

```bash
curl -X POST "http://localhost:8080/write/project" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "my-app", "text": "Project docs", "metadata": {}}'
```

### Query Project

```bash
curl -X POST "http://localhost:8080/query/project" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "my-app", "query": "docs", "top_k": 5}'
```

## External Access (via ngrok)

The ngrok URL `https://idioplasmic-unaesthetically-brandon.ngrok-free.dev` should forward to port 8080.

Update ngrok config to point to 8080:

```yaml
tunnels:
  vector-api:
    addr: 8080
    proto: http
```

Then test externally:

```bash
export VECTOR_URL="https://idioplasmic-unaesthetically-brandon.ngrok-free.dev"
curl -X POST "$VECTOR_URL/write/global" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{"text": "test", "metadata": {}}'
```

## Configuration

Environment variables in `.env`:

- `AUTH_TOKEN` - Bearer token for authentication

Environment variables in `docker-compose.yml`:

- `OLLAMA_URL` - Ollama endpoint (default: `http://192.168.1.154:11434`)
- `CHROMA_URL` - ChromaDB endpoint (default: `http://chroma:8000`)
