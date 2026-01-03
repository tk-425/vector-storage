# Vector Storage Server Implementation

Guide for setting up the vector storage server.

> **Note:** The current implementation uses a FastAPI service at `vector-storage/vector-api/main.py`. Earlier versions used n8n as a gateway — those references are obsolete.

---

## Architecture

```
Client                               Server
┌─────────────────┐                  ┌─────────────────────────┐
│ vmem CLI        │                  │ Docker Compose          │
│                 │    HTTPS/ngrok   │ ┌─────────────────────┐ │
│ vmem save ...   │ ───────────────→ │ │ vector-api (FastAPI)│ │
│ vmem query ...  │                  │ │      :8080          │ │
└─────────────────┘                  │ └──────────┬──────────┘ │
                                     │            │            │
                                     │ ┌──────────▼──────────┐ │
                                     │ │ ChromaDB   :8000    │ │
                                     │ │ + Ollama embeddings │ │
                                     │ └─────────────────────┘ │
                                     └─────────────────────────┘
```

---

## Server Setup

### Prerequisites

- Docker + Docker Compose
- Ollama with `nomic-embed-text` model
- ngrok account (free tier works)

### Directory Structure

```
/path/to/vector-storage/
├── docker-compose.yml
├── vector-api/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
└── data/
    └── chromadb/
```

### Docker Compose

```yaml
version: "3.8"
services:
  vector-api:
    build: ./vector-api
    ports:
      - "8080:8080"
    environment:
      - CHROMA_API_BASE=http://chromadb:8000/api/v2/tenants/default_tenant/databases/default_database
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - AUTH_TOKEN=${AUTH_TOKEN}
    depends_on:
      - chromadb

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data/chromadb:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
```

### Start Server

```bash
cd /path/to/vector-storage
docker compose up -d
```

### ngrok Tunnel

```bash
ngrok http 8080
```

Copy the HTTPS URL for client configuration.

---

## API Endpoints

| Endpoint           | Method | Purpose                    |
| ------------------ | ------ | -------------------------- |
| `/health`          | GET    | Health check               |
| `/write/project`   | POST   | Save to project collection |
| `/write/global`    | POST   | Save to global collection  |
| `/query/project`   | POST   | Search project             |
| `/query/global`    | POST   | Search global              |
| `/list/project`    | POST   | List project documents     |
| `/list/global`     | POST   | List global documents      |
| `/delete/document` | POST   | Delete documents by ID     |

### Authentication

All endpoints require:

```
Authorization: Bearer <YOUR_TOKEN>
```

### Write Request

```json
{
  "project_id": "my-app",
  "text": "Content to save",
  "metadata": {
    "type": "note",
    "agent": "claude-code"
  }
}
```

### Query Request

```json
{
  "project_id": "my-app",
  "query": "search terms",
  "top_k": 5
}
```

### Query Response

```json
{
  "collection": "project_my-app",
  "count": 2,
  "matches": [
    {
      "id": "1234_abc",
      "text": "Content...",
      "metadata": {...},
      "similarity": 0.85
    }
  ]
}
```

---

## Troubleshooting

| Issue              | Solution                                       |
| ------------------ | ---------------------------------------------- |
| Connection refused | Check Docker containers: `docker compose ps`   |
| 401 Unauthorized   | Verify AUTH_TOKEN matches                      |
| No embeddings      | Ensure Ollama is running with nomic-embed-text |
| Data lost          | Check volume mount in docker-compose.yml       |

### View Logs

```bash
docker compose logs -f vector-api
```

---

## Client Configuration

On your local machine, set environment variables:

```bash
export VECTOR_BASE_URL="https://your-ngrok-url.ngrok-free.dev"
export VECTOR_AUTH_TOKEN="your-token"
```

Then use vmem CLI:

```bash
vmem ping
vmem save "Test note"
vmem query "test"
```
