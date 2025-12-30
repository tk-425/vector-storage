# vmem CLI - Implementation Steps

**Status: 🔄 IN PROGRESS** (2025-12-29)

Step-by-step guide to install and configure the vmem CLI tool on MacBook.

## Bug Fixes Applied

1. **ChromaDB volume mount** - Changed to `/data/chroma:/data`
2. **Similarity formula** - Changed to `1/(1+distance)` for L2 distance
3. **Threshold lowered** - From 0.5 to 0.001 for L2-based similarity
4. **Percentage display** - Shows 2 decimal places

## New Commands (2025-12-29)

| Command        | Status      | Server Changes                  |
| -------------- | ----------- | ------------------------------- |
| `vmem ping`    | ✅ Complete | None (uses `/health`)           |
| `vmem history` | ✅ Complete | `/list/project`, `/list/global` |
| `vmem prune`   | ✅ Complete | `/delete/document`              |

---

## Prerequisites

- [ ] Python 3.x installed (check: `python3 --version`)
- [ ] `requests` package installed (check: `pip show requests`)
- [ ] Vector Storage API running on tk-lenovo
- [ ] Environment variables set: `VECTOR_URL`, `AUTH_TOKEN`

---

## Step 1: Create ~/.bin Directory

```bash
mkdir -p ~/.bin
```

---

## Step 2: Add to PATH

Add to `~/.zshrc`:

```bash
# vmem CLI
export PATH="$HOME/.bin:$PATH"
export VECTOR_BASE_URL="$VECTOR_URL"
export VECTOR_AUTH_TOKEN="$AUTH_TOKEN"
```

Reload:

```bash
source ~/.zshrc
```

---

## Step 3: Create vmem Script

Create the file `~/.bin/vmem`:

```bash
touch ~/.bin/vmem
chmod +x ~/.bin/vmem
```

Then copy the contents from `vmem.py` in this folder.

---

## Step 4: Create Config Directory

```bash
mkdir -p ~/.vmem
```

Create default config `~/.vmem/config.yml`:

```yaml
auto_save:
  mode: off # off | on | prompt
  per_project: true
```

---

## Step 5: Verify Installation

```bash
# Check PATH
which vmem

# Test help
vmem --help

# Test save
vmem save "Test from vmem CLI"

# Test query
vmem query "test"

# Test status
vmem status
```

---

## Troubleshooting

### "command not found: vmem"

1. Check PATH includes ~/.bin:

   ```bash
   echo $PATH | grep .bin
   ```

2. Reload shell:
   ```bash
   source ~/.zshrc
   ```

### "Permission denied"

Make script executable:

```bash
chmod +x ~/.bin/vmem
```

### "Error: Set VECTOR_BASE_URL..."

Add to `~/.zshrc`:

```bash
export VECTOR_BASE_URL="$VECTOR_URL"
export VECTOR_AUTH_TOKEN="$AUTH_TOKEN"
```

---

## Code Structure (vmem.py)

```
vmem.py
├── Imports & Dependencies (lines 1-24)
├── VectorMemory Class (lines 27-500+)
│   ├── __init__          - Setup API connection
│   ├── _load_config      - Load ~/.vmem/config.yml
│   ├── get_project_id    - Auto-detect project from git/folder
│   ├── save              - Save text to vector storage
│   ├── query             - Search vector storage
│   ├── _format_text      - Pretty-print results
│   ├── search_all        - Search both project + global
│   ├── status            - Show current configuration
│   ├── toggle            - Set auto-save mode
│   ├── init              - Initialize vmem in project
│   ├── hooks             - Manage Claude Code hooks
│   ├── ping              - Health check (NEW)
│   ├── history           - List recent saves (NEW)
│   └── prune             - Remove duplicates/old entries (NEW)
└── main() - CLI argument parser
```

### Key Functions

| Function         | Purpose                                                             |
| ---------------- | ------------------------------------------------------------------- |
| `__init__`       | Reads `VECTOR_URL` and `AUTH_TOKEN` from env                        |
| `get_project_id` | Runs `git rev-parse` to detect project name                         |
| `save`           | POSTs to `/write/project` or `/write/global`                        |
| `query`          | POSTs to `/query/project` or `/query/global`, filters by similarity |
| `toggle`         | Writes config to `~/.vmem/config.yml` or `.vmem.yml`                |
| `ping`           | GETs `/health`, measures response time (NEW)                        |
| `history`        | GETs `/list/project`, displays recent entries (NEW)                 |
| `prune`          | DELETEs via `/delete/document`, removes duplicates (NEW)            |

### Similarity Threshold

Results are filtered by `similarity > 0.001`. Formula: `1/(1+distance)`

---

## New Command Implementation Details

### vmem ping

**Purpose:** Verify server connectivity before operations.

```python
def ping(self):
    """Check server health and connectivity"""
    import time
    start = time.time()
    try:
        response = requests.get(
            f'{self.base_url}/health',
            headers=self.headers,
            timeout=10
        )
        elapsed = (time.time() - start) * 1000
        if response.status_code == 200:
            print(f"✓ Connected to Vector API ({elapsed:.0f}ms)")
            print(f"  URL: {self.base_url}")
        else:
            print(f"✗ Server returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach Vector API")
        print(f"  URL: {self.base_url}")
        print(f"  Error: {e}")
```

**No server changes required** - uses existing `/health` endpoint.

---

### vmem history

**Purpose:** Show recent saves for a project.

```python
def history(self, scope: str = 'project', limit: int = 10):
    """List recent saves from collection"""
    # Requires server endpoint: GET /list/project
    # ChromaDB: GET /api/v2/.../collections/{id}/get
    pass  # Implementation pending server endpoint
```

**Server endpoint needed:**

```python
@app.get("/list/project")
async def list_project(project_id: str, limit: int = 20):
    # Get documents sorted by created_at descending
    pass
```

---

### vmem prune

**Purpose:** Remove duplicates and old entries.

```python
def prune(self, older_than_days: int = None, duplicates: bool = False, dry_run: bool = False):
    """Remove old or duplicate entries"""
    # 1. Fetch all documents via history
    # 2. Identify duplicates (same text) or old entries
    # 3. Delete via /delete/document endpoint
    pass  # Implementation pending server endpoint
```

**Server endpoint needed:**

```python
@app.delete("/delete/document")
async def delete_document(collection: str, ids: list[str]):
    # ChromaDB: DELETE /api/v2/.../collections/{id}/delete
    pass
```

---

## Implementation Order

1. **Phase 1:** Implement `vmem ping` (CLI-only, no server changes)
2. **Phase 2:** Add `/list/project` endpoint to server, then implement `vmem history`
3. **Phase 3:** Add `/delete/document` endpoint to server, then implement `vmem prune`
