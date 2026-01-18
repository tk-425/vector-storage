#!/usr/bin/env python
"""
vmem - Universal Vector Memory CLI
Works with any AI agent (Claude Code, Codex, Gemini, etc.)
"""

__version__ = "1.1.4"

import os
import sys
import json
import argparse
import subprocess
from typing import Optional, Dict, List
from pathlib import Path

try:
    import requests
except ImportError:
    print(
        "Error: 'requests' package not installed. Run: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None  # Optional, for config file


class VectorMemory:
    COMPACT_LIMIT = 10

    def __init__(self):
        self.base_url = os.getenv("VECTOR_BASE_URL") or os.getenv("VECTOR_URL")
        self.auth_token = os.getenv("VECTOR_AUTH_TOKEN") or os.getenv("AUTH_TOKEN")

        if not self.base_url or not self.auth_token:
            print(
                "Error: Set VECTOR_BASE_URL and VECTOR_AUTH_TOKEN environment variables",
                file=sys.stderr,
            )
            print("  or VECTOR_URL and AUTH_TOKEN", file=sys.stderr)
            sys.exit(1)

        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true",
        }

        # Load config
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load global and project config"""
        config = {
            "auto_save": {
                "global_mode": "off",
                "project_mode": None,
                "per_project": True,
            }
        }

        # Global config
        global_config_path = Path.home() / ".vmem" / "config.yml"
        if global_config_path.exists() and yaml:
            try:
                with open(global_config_path) as f:
                    global_config = yaml.safe_load(f)
                    if global_config and "auto_save" in global_config:
                        config["auto_save"]["global_mode"] = global_config[
                            "auto_save"
                        ].get("mode", "off")
            except Exception:
                pass

        # Project config
        project_config_path = Path.cwd() / ".vmem" / "config.yml"
        if project_config_path.exists() and yaml:
            try:
                with open(project_config_path) as f:
                    project_config = yaml.safe_load(f)
                    if project_config and "auto_save" in project_config:
                        config["auto_save"]["project_mode"] = project_config[
                            "auto_save"
                        ]
            except Exception:
                pass

        return config

    def get_project_id(self) -> str:
        """Auto-detect project ID from git repo or directory"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            path = result.stdout.strip()
        except Exception:
            path = os.getcwd()

        name = os.path.basename(path)
        slug = name.lower().replace(" ", "-").replace("_", "-")
        return slug

    def get_effective_mode(self) -> str:
        """Get the effective auto-save mode (project overrides global)"""
        project_mode = self.config["auto_save"]["project_mode"]
        if project_mode is not None:
            mode = project_mode
        else:
            mode = self.config["auto_save"]["global_mode"]

        # Normalize YAML boolean values (on/off parsed as True/False)
        if mode is True:
            return "on"
        elif mode is False:
            return "off"
        return mode if mode else "off"

    def is_initialized(self) -> bool:
        """Check if project is initialized (local config exists)"""
        cwd = Path.cwd()
        return (cwd / ".vmem" / "config.yml").exists() or (
            cwd / ".vmem" / "vmem.md"
        ).exists()

    def can_auto_save(self) -> bool:
        """Check if auto-save is allowed based on current mode"""
        mode = self.get_effective_mode()

        if mode == "off":
            return False
        elif mode == "on":
            return True
        elif mode == "prompt":
            response = input("💾 Save to vector storage? (y/n): ").strip().lower()
            return response in ["y", "yes"]
        else:
            return False

    def save(
        self,
        text: str,
        scope: str = "project",
        metadata: Optional[Dict] = None,
        agent: str = "cli",
        force: bool = False,
    ):
        """Save to vector storage

        Args:
            force: If True, bypass auto-save check (for manual saves)
        """
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        # Check auto-save permission (unless forced)
        if not force and not self.can_auto_save():
            mode = self.get_effective_mode()
            print(
                f"ℹ️  Auto-save is {mode.upper()}. Use --force to save manually.",
                file=sys.stderr,
            )
            return None

        metadata = metadata or {}
        metadata.update(
            {
                "agent": agent,
                "source": "manual" if force else "auto",
                "type": metadata.get("type", "note"),
            }
        )

        if scope == "project":
            project_id = self.get_project_id()
            payload = {"project_id": project_id, "text": text, "metadata": metadata}
            endpoint = "/write/project"
        else:
            payload = {"text": text, "metadata": metadata}
            endpoint = "/write/global"

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Saved to {result.get('collection', scope)}")
            if result.get("id"):
                print(f"  ID: {result['id']}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error saving: {e}", file=sys.stderr)
            sys.exit(1)

    def save_compact(self, text: str, scope: str = "project"):
        """Save a compact (project snapshot). Max 10 kept, oldest auto-deleted."""
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        # Get existing compacts
        compacts = self._get_compacts(scope)

        # If 5 or more exist, delete the oldest
        if len(compacts) >= self.COMPACT_LIMIT:
            oldest = compacts[-1]  # Last one is oldest (sorted desc by created_at)
            oldest_id = oldest.get("id")
            if oldest_id:
                self._delete_compact(oldest_id, scope)
                print(
                    f"ℹ️  Deleted oldest compact to make room (max {self.COMPACT_LIMIT})"
                )

        # Save new compact with type: compact
        metadata = {"type": "compact", "agent": "cli", "source": "manual"}

        if scope == "project":
            project_id = self.get_project_id()
            payload = {"project_id": project_id, "text": text, "metadata": metadata}
            endpoint = "/write/project"
        else:
            payload = {"text": text, "metadata": metadata}
            endpoint = "/write/global"

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Compact saved to {result.get('collection', scope)}")
            if result.get("id"):
                print(f"  ID: {result['id']}")
            print(
                f"  Total compacts: {min(len(compacts) + 1, self.COMPACT_LIMIT)}/{self.COMPACT_LIMIT}"
            )
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error saving compact: {e}", file=sys.stderr)
            sys.exit(1)

    def retrieve_compact(
        self, index: int = 1, scope: str = "project", show_all: bool = False
    ):
        """Retrieve compact(s). Index 1=newest, 10=oldest."""
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        compacts = self._get_compacts(scope)

        if not compacts:
            print(f"No compacts found in {scope} collection")
            return None

        if show_all:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📦 Compacts ({scope}): {len(compacts)}/{self.COMPACT_LIMIT}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for i, compact in enumerate(compacts, 1):
                meta = compact.get("metadata", {})
                created = (
                    meta.get("created_at", "Unknown")[:10]
                    if meta.get("created_at")
                    else "Unknown"
                )
                first_line = compact.get("text", "").split("\n")[0]
                text = first_line[:60] + ("..." if len(first_line) > 60 else "")
                print(f"[{i}] {created} | {text}")
            return compacts

        # Get specific compact by index
        if index < 1 or index > len(compacts):
            print(f"✗ Invalid index. Available: 1-{len(compacts)}")
            return None

        compact = compacts[index - 1]
        meta = compact.get("metadata", {})
        created = (
            meta.get("created_at", "Unknown")[:19]
            if meta.get("created_at")
            else "Unknown"
        )

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📦 Compact [{index}/{len(compacts)}] - {created}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(compact.get("text", ""))
        return compact

    def _get_compacts(self, scope: str = "project") -> List[Dict]:
        """Get all compacts, sorted by created_at descending (newest first)."""
        if scope == "project":
            project_id = self.get_project_id()
            payload = {"project_id": project_id, "limit": 100}
            endpoint = "/list/project"
        else:
            payload = {"limit": 100}
            endpoint = "/list/global"

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            documents = result.get("documents", [])

            # Filter for compacts only
            compacts = [
                d for d in documents if d.get("metadata", {}).get("type") == "compact"
            ]

            # Sort by created_at descending (newest first)
            compacts.sort(
                key=lambda d: d.get("metadata", {}).get("created_at", ""), reverse=True
            )

            return compacts[: self.COMPACT_LIMIT]  # Max 10
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching compacts: {e}", file=sys.stderr)
            return []

    def _delete_compact(self, doc_id: str, scope: str = "project"):
        """Delete a specific compact by ID."""
        if scope == "project":
            project_id = self.get_project_id()
            collection = f"project_{project_id}"
        else:
            collection = "global"

        try:
            response = requests.post(
                f"{self.base_url}/delete/document",
                headers=self.headers,
                json={"collection": collection, "ids": [doc_id]},
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"✗ Error deleting compact: {e}", file=sys.stderr)

    def delete_compact_bulk(
        self,
        scope: str = "project",
        older_than_days: int = None,
        delete_all: bool = False,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """Delete compacts based on criteria."""
        from datetime import datetime, timedelta

        compacts = self._get_compacts(scope)

        if not compacts:
            print("No compacts found")
            return

        to_delete = []

        # Determine which compacts to delete
        if delete_all:
            to_delete = compacts
        elif older_than_days:
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            for compact in compacts:
                meta = compact.get("metadata", {})
                created_str = meta.get("created_at", "")
                if created_str:
                    try:
                        created = datetime.fromisoformat(
                            created_str.replace("Z", "+00:00")
                        )
                        if created.replace(tzinfo=None) < cutoff:
                            to_delete.append(compact)
                    except (ValueError, TypeError):
                        pass
        else:
            print("Specify --all or --older-than to delete compacts")
            return

        if not to_delete:
            print("No compacts match the criteria")
            return

        # Show what will be deleted
        if scope == "project":
            project_id = self.get_project_id()
            collection = f"project_{project_id}"
        else:
            collection = "global"

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📦 Compacts to delete from {collection}:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for i, compact in enumerate(to_delete, 1):
            meta = compact.get("metadata", {})
            created = (
                meta.get("created_at", "Unknown")[:10]
                if meta.get("created_at")
                else "Unknown"
            )

            if verbose:
                print(f"\n[{i}] ID: {compact.get('id', 'Unknown')}")
                print(f"    Created: {created}")
                print(f"    Text: {compact.get('text', '')[:100]}...")
            else:
                text = compact.get("text", "")[:50] + (
                    "..." if len(compact.get("text", "")) > 50 else ""
                )
                print(f"[{i}] {created} | {text}")

        print(f"\nTotal to delete: {len(to_delete)}")

        if dry_run:
            print("\nℹ️  Dry run - no changes made. Remove --dry-run to delete.")
            return

        # Delete compacts
        ids_to_delete = [c["id"] for c in to_delete]
        try:
            response = requests.post(
                f"{self.base_url}/delete/document",
                headers=self.headers,
                json={"collection": collection, "ids": ids_to_delete},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            print(
                f"\n✓ Deleted {result.get('deleted_count', len(ids_to_delete))} compacts"
            )
        except requests.exceptions.RequestException as e:
            print(f"✗ Error deleting: {e}", file=sys.stderr)
            sys.exit(1)

    def delete_compact_by_index(
        self, index: int, scope: str = "project", dry_run: bool = False
    ):
        """Delete a specific compact by index (1=newest)."""
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        compacts = self._get_compacts(scope)

        if not compacts:
            print("No compacts found")
            return

        if index < 1 or index > len(compacts):
            print(f"Invalid index {index}. Valid range: 1-{len(compacts)}")
            return

        compact = compacts[index - 1]

        if scope == "project":
            project_id = self.get_project_id()
            collection = f"project_{project_id}"
        else:
            collection = "global"

        meta = compact.get("metadata", {})
        created = (
            meta.get("created_at", "Unknown")[:10]
            if meta.get("created_at")
            else "Unknown"
        )
        text = compact.get("text", "")[:60] + (
            "..." if len(compact.get("text", "")) > 60 else ""
        )

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📦 Compact to delete:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"[{index}] {created} | {text}")
        print(f"ID: {compact.get('id', 'Unknown')}")

        if dry_run:
            print("\nℹ️  Dry run - no changes made.")
            return

        try:
            response = requests.post(
                f"{self.base_url}/delete/document",
                headers=self.headers,
                json={"collection": collection, "ids": [compact["id"]]},
                timeout=30,
            )
            response.raise_for_status()
            print(f"\n✓ Deleted compact [{index}]")
        except requests.exceptions.RequestException as e:
            print(f"✗ Error deleting: {e}", file=sys.stderr)
            sys.exit(1)

    def query(
        self,
        query: str,
        scope: str = "project",
        top_k: int = 5,
        output_format: str = "text",
    ) -> List[Dict]:
        """Query vector storage"""
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        if scope == "project":
            project_id = self.get_project_id()
            payload = {"project_id": project_id, "query": query, "top_k": top_k}
            endpoint = "/query/project"
        else:
            payload = {"query": query, "top_k": top_k}
            endpoint = "/query/global"

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            matches = result.get("matches", [])
            # Filter by similarity threshold
            matches = [m for m in matches if m.get("similarity", 0) > 0.001]

            if output_format == "json":
                print(json.dumps(matches, indent=2))
            else:
                self._format_text(matches, result.get("collection", scope))

            return matches
        except requests.exceptions.RequestException as e:
            print(f"✗ Error querying: {e}", file=sys.stderr)
            sys.exit(1)

    def _format_text(self, matches: List[Dict], collection: str):
        """Format results as human-readable text"""
        if not matches:
            print(f"No relevant results found in {collection}")
            return

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📚 Results from {collection}:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for i, match in enumerate(matches, 1):
            similarity_pct = match.get("similarity", 0) * 100
            print(f"\n[{i}] Similarity: {similarity_pct:.2f}%")
            print(f"{match.get('text', '')}")

            meta = match.get("metadata", {})
            if meta.get("created_at"):
                print(f"   Saved: {meta['created_at'][:10]}")
            if meta.get("tags"):
                tags = meta["tags"]
                if isinstance(tags, list):
                    print(f"   Tags: {', '.join(tags)}")

    def search_all(self, query: str, top_k: int = 3):
        """Search both project and global collections"""
        # Note: We don't strictly enforce init for global search, but since this command
        # searches BOTH, and project search requires project ID...
        # Let's enforce init if we are in a project context, or warn?
        # Simpler: If not initialized, maybe just warn or skip project search?
        # But per user request "check status of project... before any other command"
        # Let's enforce it to be safe.
        if not self.is_initialized():
            print(
                "⚠️  Project not initialized. To search global only, use 'vmem query --global'",
                file=sys.stderr,
            )
            print("   Run 'vmem init' to enable project search.", file=sys.stderr)
            sys.exit(1)

        print("Searching project collection...")
        project_matches = self.query(
            query, scope="project", top_k=top_k, output_format="json"
        )

        print("\nSearching global collection...")
        global_matches = self.query(
            query, scope="global", top_k=top_k, output_format="json"
        )

        all_matches = project_matches + global_matches
        all_matches.sort(key=lambda m: m.get("similarity", 0), reverse=True)

        return all_matches[:top_k]

    def status(self, json_output: bool = False):
        """Show current status"""
        is_init = self.is_initialized()
        effective_mode = self.get_effective_mode()
        project_mode = self.config["auto_save"]["project_mode"]
        global_mode = self.config["auto_save"]["global_mode"]

        if json_output:
            import json

            status_data = {
                "mode": effective_mode,
                "global_mode": global_mode,
                "project_mode": project_mode if project_mode else None,
                "project": self.get_project_id(),
                "api_url": self.base_url,
            }
            print(json.dumps(status_data))
            return

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📊 Vector Memory Status (v.{__version__})")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Global Auto-save mode: {global_mode}")

        if project_mode:
            print(f"Project Auto-save mode: {project_mode}")
        else:
            print("Project Auto-save mode: not set")

        print(f"Current project: {self.get_project_id()}")

        # Local Status
        if is_init:
            print("Local Status: ✅ Initialized")
        else:
            print("Local Status: ❌ Not Initialized")

        # Remote Status (Check without creating)
        try:
            print("Remote Status: ", end="", flush=True)
            project_id = self.get_project_id()
            response = requests.post(
                f"{self.base_url}/check/project",
                headers=self.headers,
                json={"project_id": project_id},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("exists"):
                    count = data.get("count", 0)
                    print(f"✅ Active ({count} documents)")
                else:
                    print("❌ Not found (Clean)")
            else:
                print(f"⚠️  Unknown ({response.status_code})")
        except Exception:
            print("⚠️  Unreachable")

        # Check connectivity
        try:
            print("Connectivity: ", end="", flush=True)
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Online")
            else:
                print(f"⚠️  Issues (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Unreachable ({e})")

    def toggle(self, mode: str):
        """Toggle auto-save mode"""
        valid_modes = ["off", "on"]
        if mode not in valid_modes:
            print(
                f"Invalid mode: {mode}. Use: {', '.join(valid_modes)}", file=sys.stderr
            )
            sys.exit(1)

        if not self.is_initialized():
            print(
                "⚠️  Project not initialized. Run 'vmem init' first.",
                file=sys.stderr,
            )
            sys.exit(1)

        config_path = Path.cwd() / ".vmem" / "config.yml"
        # Ensure .vmem directory exists
        if not config_path.parent.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            f.write(f"auto_save: {mode}\n")
        print(f"✓ Project auto-save set to: {mode}")

    def _get_vmem_md_content(self) -> str:
        """Get content for .vmem.md"""
        return f"""# vmem - Vector Memory (v.{__version__})

## AUTO-RETRIEVAL (Before work)
When user asks about implementation, debugging, or "how did we do X":
1. Query: `vmem query "relevant keywords"`
2. Also try: `vmem search "keywords"` (searches project + global)
3. Use results as context for your response

## AUTO-SAVE (After work)
After completing implementation tasks:
1. Check: `vmem status`
2. If auto-save is **ON** → `vmem save "summary of work"`
3. If auto-save is **OFF** → only save if user asks (use `--force`)
4. If auto-save is **PROMPT** → ask user first

## What to Save
✅ Implementation decisions, bug fixes, API patterns, architecture choices
✅ Workflows, configurations, troubleshooting steps, lessons learned
✅ Key findings and conclusions from research/exploration
❌ Pure questions without answers, incomplete brainstorming
❌ Long documentation dumps (keep saves to 2-4 sentences max)

**Save format:** WHAT was done + WHY it matters + KEY function names


## Commands
| Command | Purpose |
|---------|---------|
| `vmem query "term"` | Search project collection |
| `vmem search "term"` | Search project + global |
| `vmem save "text"` | Save (respects toggle) |
| `vmem save "text" --force` | Force save (always works) |
| `vmem status` | Check auto-save toggle |
| `vmem toggle on` | Enable auto-save |
| `vmem toggle off` | Disable auto-save |
| `vmem ping` | Check server connectivity |
| `vmem history` | Show recent saves |
| `vmem delete --duplicates` | Remove duplicate entries |
| `vmem delete --days 30` | Remove entries >30 days old |
| `vmem delete --dry-run` | Preview without deleting |
| `vmem delete compact --all` | Remove all compacts |
| `vmem delete compact --all --dry-run` | Preview compact removal |
| `vmem delete compact --older-than 7` | Remove compacts >7 days old |
| `vmem compact "text"` | Save project snapshot (max 10) |
| `vmem retrieve compact` | Get recent compact |
| `vmem retrieve compact --all` | List all compacts |
| `vmem delete compact 2` | Delete compact at index 2 |
| `vmem init` | Initialize project |
| `vmem init on` | Initialize + enable hooks |
| `vmem upgrade-docs` | Refresh docs to match CLI version |
| `vmem add-agent` | Add agent configs to existing project |
| `vmem hooks status` | Check hooks status |
| `vmem hooks on` | Enable hooks (Claude Code) |
| `vmem hooks off` | Disable hooks |
"""

    def _get_gemini_rules_content(self) -> str:
        """Get content for .agent/rules/vmem.md"""
        return """# Agent Implementation Guide & Protocol

This rule defines the standard operating procedure for **Gemini** when working in this workspace.

## 1. PRE-WORK: Context Retrieval

Before starting any significant task (coding, planning, or complex Q&A), you MUST check for existing context.

### Auto-Retrieval

- **Trigger**: You are starting a new task or "Implementation Phase".
- **Action**: Run `vmem query` or `vmem search` with relevant keywords.
- **Goal**: Prevent re-learning things you've already solved or documented.

### Manual Retrieval

- **Trigger**: User explicitly asks "How did we do X?" or "Check vmem for Y".
- **Action**: Run `vmem query "exact user query"`.

---

## 2. EXECUTION: The Standard Loop

1.  **Analyze**: Understand the request.
2.  **Retrieve**: Check `vmem` (as above) and local files.
3.  **Plan**: Create/Update `implementation_plan.md` (if complex).
4.  **Execute**: Write code.
5.  **Verify**: Test changes.

---

## 3. POST-WORK: Memory Retention

After completing a task, you MUST consider saving technical insights for the future.

### Auto-Save (The Default Path)

1.  **Check Status**: Run `vmem status`.
2.  **If ON**:
    - **Action**: Automatically run `vmem save "Summary of what was done..."`.
    - **Content**: Keep it concise (2-4 sentences). Focus on _decisions_ and _patterns_, not just file edits.
3.  **If OFF**: Do NOT auto-save. Wait for user instruction.

### Manual Save

- **Trigger**: User says "remember this", "save this", or "store this".
- **Action**: Run `vmem save "Content..." --force` (overrides the OFF status).

### Compact (Project Snapshots)

- **Trigger**: End of a major milestone or long session.
- **Command**: `vmem compact "Comprehensive summary..."`.
- **Delete by index**: `vmem delete compact 2` (deletes compact #2).
- **Use Case**: When a simple 2-line save isn't enough to capture the complex state changes.

**For long multi-line compacts**, use heredoc to avoid shell quoting issues:

```bash
cat << 'EOF' | xargs -0 vmem compact
Session summary here...

BUG FIXES:
- Fixed X in file.py

NEW FEATURES:
- Added Y command

FILES: file1.py, file2.md
EOF
```

---

## 4. User Interaction Examples

The user will **not** run CLI commands directly. They will give natural language instructions, and **YOU (The Agent)** must translate them into `vmem` tool calls.

### Scenario A: Starting Work (Auto-Retrieval)

- **User says**: "Let's implement the JWT auth flow."
- **Agent does**:
  1.  _Thinking_: "I should check if we have any existing patterns for this."
  2.  _Tool Call_: `vmem query "JWT authentication patterns"`
  3.  _Response_: "I see we previously used HS256. I'll stick to that..."

### Scenario B: Saving Work (Manual Override)

- **User says**: "Great job. Remember that this API requires the `Authorization: Bearer` header."
- **Agent does**:
  1.  _Thinking_: "User explicitly wants to store this fact."
  2.  _Tool Call_: `vmem save "API Requirement: Endpoints require 'Authorization: Bearer' header." --force`
  3.  _Response_: "Got it, I've saved that requirement to memory."

### Scenario C: Checking Status

- **User says**: "Is auto-memory on?"
- **Agent does**:
  1.  _Tool Call_: `vmem status`
  2.  _Response_: "Yes, Auto-Save is currently ON for this project."
"""

    def _update_gitignore(self):
        """Add vmem files to .gitignore if not present"""
        gitignore_path = Path.cwd() / ".gitignore"

        # Files to ignore
        entries = [".vmem/", "# vmem"]

        # Check existing content
        existing = set()
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                existing = {line.strip() for line in f.readlines()}

        # Add missing
        to_add = [e for e in entries if e not in existing]

        if to_add:
            try:
                with open(gitignore_path, "a") as f:
                    if existing and list(existing)[-1] != "":
                        f.write("\n")
                    f.write("\n# vmem\n")
                    for entry in entries:
                        if entry != "# vmem" and entry not in existing:
                            f.write(f"{entry}\n")
                print("✓ Updated .gitignore")
            except OSError as e:
                print(f"⚠ Could not update .gitignore: {e}")

    def _prompt_selection(
        self, options: list[tuple[str, str]], prompt: str
    ) -> list[str]:
        """Prompt user to select multiple options from a list"""
        if not options:
            return []

        print(f"\n{prompt}")
        for i, (label, value) in enumerate(options, 1):
            print(f"  {i}. {label}")

        try:
            choice = input("\nSelect (e.g., 1 or 1,2): ").strip()
            if not choice:
                return []

            indices = [
                int(c.strip())
                for c in choice.replace(" ", ",").split(",")
                if c.strip().isdigit()
            ]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(options):
                    selected.append(options[idx - 1][1])
            return selected
        except (ValueError, EOFError, KeyboardInterrupt):
            return []

    def configure_integrations(self, enable_hooks: bool = False):
        """Configure agent config files and rule directories"""

        cwd = Path.cwd()

        # vmem reference to add
        vmem_reference = """

## Vector Memory
For vmem commands and auto-save/retrieval behavior, read: `@.vmem/vmem.md`
"""

        # 1. Select Agent Config Files
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📁 Agent Config Files")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        config_options = [
            ("CLAUDE.md (Claude Code)", "CLAUDE.md"),
            ("GEMINI.md (Gemini CLI)", "GEMINI.md"),
            ("QWEN.md (Qwen)", "QWEN.md"),
            ("AGENTS.md (Universal)", "AGENTS.md"),
        ]

        selected_configs = self._prompt_selection(
            config_options, "Which agent config files to create/update?"
        )

        # Default to AGENTS.md if nothing selected but user didn't abort
        if not selected_configs:
            print("No files selected. Skipping config injection.")

        for filename in selected_configs:
            filepath = cwd / filename
            is_new = not filepath.exists()

            with open(filepath, "a" if not is_new else "w") as f:
                if is_new:
                    f.write(vmem_reference)
                    print(f"✓ Created {filename}")
                else:
                    # Upgrade/Check logic
                    with open(filepath, "r") as r:
                        content = r.read()

                    old_ref = "For vmem commands and auto-save/retrieval behavior, read: `.vmem/vmem.md`"
                    new_ref = "For vmem commands and auto-save/retrieval behavior, read: `@.vmem/vmem.md`"

                    if new_ref in content:
                        print(f"ℹ️  {filename} already up to date")
                        continue

                    if old_ref in content:
                        # Upgrade existing reference
                        updated_content = content.replace(old_ref, new_ref)
                        pass  # handled below
                    else:
                        # Append new reference
                        f.write(vmem_reference)
                        print(f"✓ Updated {filename}")
                        continue

                    # If we got here, we are upgrading
                    with open(filepath, "w") as w:
                        w.write(updated_content)
                    print(f"✓ Upgraded {filename} (added @ symbol)")

        # 2. Select Rule Directories
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📂 Rule Directories")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        rule_options = [
            (".agent/rules (Standard)", ".agent"),
            (".claude (Claude Code)", ".claude"),
            (".gemini (Gemini)", ".gemini"),
            (".qwen (Qwen)", ".qwen"),
            (".codex (Codex)", ".codex"),
        ]

        selected_dirs = self._prompt_selection(
            rule_options, "Which rule directories to configure?"
        )
        gemini_rules_content = self._get_gemini_rules_content()

        for dir_name in selected_dirs:
            rules_dir = cwd / dir_name / "rules"

            # Special case for .agent, it usually has 'rules' inside, but others might need to create it
            # The prompt options just gave the root.

            try:
                (cwd / dir_name).mkdir(exist_ok=True)
                rules_dir.mkdir(parents=True, exist_ok=True)
                rule_path = rules_dir / "vmem.md"

                if rule_path.exists():
                    print(f"ℹ️  {dir_name}/rules/vmem.md already exists")
                else:
                    with open(rule_path, "w") as f:
                        f.write(gemini_rules_content)
                    print(f"✓ Created {dir_name}/rules/vmem.md")
            except OSError as e:
                print(f"⚠ Could not create in {dir_name}: {e}")

        # Add Claude Code hooks if enable_hooks
        if enable_hooks:
            print("  2. .claude/settings.json (for hooks)")
            if not (Path.cwd() / ".claude").exists():
                print(
                    "     (Note: .claude directory not found, hooks might not work locally)"
                )

        try:
            input("\nPress Enter to continue (Ctrl+C to cancel)...")
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)

    def add_agent(self):
        """Add agent configuration files and folders"""
        project_id = self.get_project_id()

        # Check Remote Initialization
        remote_status = self._check_remote_project(project_id)
        if not remote_status["exists"]:
            print(
                f"⚠️  Error: Project '{project_id}' not found in remote vector database."
            )
            print(
                "   Please run 'vmem init' (or 'vmem init on') to initialize the project first."
            )
            sys.exit(1)

        self.configure_integrations(enable_hooks=False)
        print("\n✓ Agent configuration updated.")

    def _check_remote_project(self, project_id: str) -> dict:
        """Check if project exists remotely

        Returns:
            dict: {"exists": bool, "count": int, "error": str/None}
        """
        try:
            response = requests.post(
                f"{self.base_url}/check/project",
                headers=self.headers,
                json={"project_id": project_id},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "exists": data.get("exists", False),
                    "count": data.get("count", 0),
                    "error": None,
                }
            else:
                return {
                    "exists": False,
                    "count": 0,
                    "error": f"Status: {response.status_code}",
                }
        except Exception as e:
            return {"exists": False, "count": 0, "error": str(e)}

    def init(self, enable_hooks: bool = False):
        """Initialize vmem in current project

        Args:
            enable_hooks: If True, set auto_save to 'on' and add Claude Code hooks
        """
        import json

        cwd = Path.cwd()

        # 1. Configure Integrations (Agent Configs + Rules)
        self.configure_integrations(enable_hooks=enable_hooks)

        # Create .vmem directory
        vmem_dir = cwd / ".vmem"
        vmem_dir.mkdir(parents=True, exist_ok=True)

        # .vmem/vmem.md content
        vmem_md_content = self._get_vmem_md_content()

        # Create .vmem/vmem.md (moved logic)
        vmem_md_path = vmem_dir / "vmem.md"
        if vmem_md_path.exists():
            print("ℹ️  .vmem/vmem.md already exists")
        else:
            with open(vmem_md_path, "w") as f:
                f.write(vmem_md_content)
            print("✓ Created .vmem/vmem.md")

        # Create .agent/rules/vmem.md (for Gemini)
        agent_rules_path = Path.cwd() / ".agent" / "rules" / "vmem.md"
        if not agent_rules_path.parent.exists():
            agent_rules_path.parent.mkdir(parents=True, exist_ok=True)

        if not agent_rules_path.exists():
            with open(agent_rules_path, "w") as f:
                f.write(self._get_gemini_rules_content())
            print("✓ Created .agent/rules/vmem.md")

        # Update .gitignore
        self._update_gitignore()

        # Enable hooks
        if enable_hooks:
            claude_dir = Path.cwd() / ".claude"
            if not claude_dir.exists():
                claude_dir.mkdir(exist_ok=True)

            settings_path = claude_dir / "settings.json"

            # Default hooks config
            hooks_config = {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "~/.vmem/vmem-pre-query.sh",
                                }
                            ],
                        }
                    ],
                    "Stop": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "~/.vmem/vmem-post-save.sh",
                                }
                            ],
                        }
                    ],
                }
            }

            with open(settings_path, "w") as f:
                json.dump(hooks_config, f, indent=2)
            print("✓ Created .claude/settings.json (hooks enabled)")

        print("\n✓ vmem initialized!")
        if not enable_hooks:
            print("  Run 'vmem toggle on' to enable auto-save.")
            print("  Or use 'vmem init on' to enable hooks.")

    def uninit(self):
        """Uninitialize vmem in current project (Complete Teardown)"""
        if not self.is_initialized():
            print(
                "ℹ️  Project not initialized. Nothing to uninitialize.", file=sys.stderr
            )
            return

        cwd = Path.cwd()
        project_id = self.get_project_id()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("⚠️  vmem Uninitialization (Project Teardown)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Project: {project_id}")

        # Check remote status first
        # Check remote status first
        print("Checking remote status...", end="", flush=True)
        remote_status = self._check_remote_project(project_id)
        remote_exists = remote_status["exists"]
        remote_count = remote_status["count"]

        if remote_exists:
            print(f" Found ({remote_count} items)")
        elif remote_status["error"]:
            print(f" Error ({remote_status['error']})")
        else:
            print(" Not found (Clean)")

        print("\nThis will:")
        print("  1. Remove all local vmem documentation and config files.")
        print("  2. Surgical removal of vmem hooks from .claude/settings.json.")

        if remote_exists:
            print(f"  3. PERMANENTLY DELETE {remote_count} items from server memory.")
        else:
            print("  3. (Skip) Remote memory delete (not found on server).")

        try:
            confirm = (
                input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
            )
            if confirm != "y":
                print("Aborted.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return

        # 1. Server-side deletion (only if exists)
        if remote_exists:
            print("\nDeleting remote project collection...", end="", flush=True)
            try:
                response = requests.post(
                    f"{self.base_url}/delete/project",
                    headers=self.headers,
                    json={"project_id": project_id},
                    timeout=30,
                )
                if response.status_code == 200:
                    print(" ✓ Deleted")
                else:
                    print(f" ✗ Failed (Status: {response.status_code})")
                    # Continue anyway to clean up local files
            except Exception as e:
                print(f" ✗ Error: {e}")
        else:
            print("\nSkipping remote deletion (not found).")

        # 2. Local file deletion
        # 2. Local file deletion
        files_to_delete = []

        # Remove .vmem directory
        vmem_dir = cwd / ".vmem"
        if vmem_dir.exists():
            import shutil

            try:
                shutil.rmtree(vmem_dir)
                print("✓ Deleted .vmem/ directory")
            except OSError as e:
                print(f"⚠ Could not delete .vmem/: {e}")

        # Check all possible rule dirs
        for dir_name in [".agent", ".claude", ".gemini", ".qwen", ".codex"]:
            files_to_delete.append(cwd / dir_name / "rules" / "vmem.md")

        for file_path in files_to_delete:
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"✓ Deleted {file_path.name}")
                except OSError as e:
                    print(f"⚠ Could not delete {file_path.name}: {e}")

        # 3. Strip references from agent config files
        agent_files = ["CLAUDE.md", "GEMINI.md", "QWEN.md", "AGENTS.md"]

        # Snippets to remove (handle both formats)
        snippets = [
            "\n## Vector Memory\nFor vmem commands and auto-save/retrieval behavior, read: `@.vmem/vmem.md`",
            "\n## Vector Memory\nFor vmem commands and auto-save/retrieval behavior, read: `.vmem/vmem.md`",
            "\n## Vector Memory\nFor vmem commands and auto-save/retrieval behavior, read: `.vmem.md`",
        ]

        for filename in agent_files:
            filepath = cwd / filename
            if filepath.exists():
                try:
                    with open(filepath, "r") as f:
                        content = f.read()

                    new_content = content
                    cleaned = False
                    for snippet in snippets:
                        if snippet in new_content:
                            new_content = new_content.replace(snippet, "").strip()
                            cleaned = True

                    if cleaned:
                        with open(filepath, "w") as f:
                            f.write(new_content)
                        print(f"✓ Cleaned {filename}")
                except Exception as e:
                    print(f"⚠ Could not clean {filename}: {e}")

        # 4. Cleanup .gitignore
        gitignore_path = cwd / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r") as f:
                    lines = f.readlines()

                # Specific lines to remove
                to_remove = {".vmem/", "# vmem"}
                new_lines = [line for line in lines if line.strip() not in to_remove]

                # If we have '# Agent tools' but nothing after it (or just empty lines), we could clean that too
                # but let's keep it simple for now and just remove the most obvious artifacts.

                with open(gitignore_path, "w") as f:
                    f.writelines(new_lines)
                print("✓ Cleaned .gitignore")
            except Exception as e:
                print(f"⚠ Could not clean .gitignore: {e}")

        # 5. Remove Claude hooks
        self.hooks("off")

        print("\n✨ vmem has been completely uninitialized for this project.")

    def upgrade_docs(self):
        """Update vmem documentation in current project"""
        cwd = Path.cwd()

        files_to_update = [
            (cwd / ".vmem" / "vmem.md", self._get_vmem_md_content()),
        ]

        # Update rules in all supported dirs if they exist
        rule_content = self._get_gemini_rules_content()
        for dir_name in [".agent", ".claude", ".gemini", ".qwen", ".codex"]:
            rule_path = cwd / dir_name / "rules" / "vmem.md"
            if rule_path.exists():
                files_to_update.append((rule_path, rule_content))

        updated_count = 0

        for file_path, content in files_to_update:
            if not file_path.parent.exists():
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                except OSError:
                    continue

            if file_path.exists():
                with open(file_path, "r") as f:
                    current = f.read()

                if current == content:
                    print(f"✓ {file_path.name} is up to date")
                    continue

                # Backup
                backup_path = file_path.with_suffix(".md.bak")
                try:
                    with open(backup_path, "w") as f:
                        f.write(current)
                    print(f"  Backed up {file_path.name} to {backup_path.name}")
                except OSError:
                    print(f"⚠ Failed to backup {file_path.name}")

            # Write new content
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                print(f"✓ Updated {file_path.name}")
                updated_count += 1
            except OSError as e:
                print(f"✗ Failed to update {file_path.name}: {e}")

        if updated_count > 0:
            print(f"\n✨ Updated {updated_count} files to vmem {__version__}")
        else:
            print(f"\n✨ All files are up to date (vmem {__version__})")

    def hooks(self, action: str):
        """Manage Claude Code hooks"""
        import json

        claude_dir = Path.cwd() / ".claude"
        settings_path = claude_dir / "settings.json"

        # Default hooks config
        hooks_config = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": "~/.vmem/vmem-pre-query.sh"}
                        ],
                    }
                ],
                "Stop": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": "~/.vmem/vmem-post-save.sh"}
                        ],
                    }
                ],
            }
        }

        if action == "status":
            if not settings_path.exists():
                print("Hooks: not configured (no .claude/settings.json)")
                return

            with open(settings_path, "r") as f:
                settings = json.load(f)

            if "hooks" in settings:
                print("Hooks: enabled")
                print(f"Config: {settings_path}")
            else:
                print("Hooks: disabled (no hooks in settings.json)")

        elif action == "on":
            # Check if .claude directory exists
            if not claude_dir.exists():
                print(
                    "ℹ️  .claude folder not available. Run this in a Claude Code project."
                )
                return

            # Load existing settings or create new
            if settings_path.exists():
                with open(settings_path, "r") as f:
                    settings = json.load(f)
            else:
                settings = {}

            # Add hooks config
            settings["hooks"] = hooks_config["hooks"]

            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)

            print("✓ Hooks enabled")
            print(f"  Config: {settings_path}")
            print("  Make sure hook scripts exist in ~/.vmem/")

        elif action == "off":
            if not claude_dir.exists():
                print("ℹ️  .claude folder not available.")
                return

            if not settings_path.exists():
                print("ℹ️  No .claude/settings.json found")
                return

            with open(settings_path, "r") as f:
                settings = json.load(f)

            if "hooks" in settings:
                del settings["hooks"]

                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)

                print("✓ Hooks disabled")
            else:
                print("ℹ️  Hooks were not enabled")

        else:
            print(f"Unknown action: {action}. Use: on, off, status", file=sys.stderr)

    def ping(self):
        """Check server health and connectivity"""
        import time

        start = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/health", headers=self.headers, timeout=10
            )
            elapsed = (time.time() - start) * 1000
            if response.status_code == 200:
                print(f"✓ Connected to Vector API ({elapsed:.0f}ms)")
                print(f"  URL: {self.base_url}")
                data = response.json()
                if data.get("status"):
                    print(f"  Status: {data['status']}")
            else:
                print(f"✗ Server returned {response.status_code}")
                sys.exit(1)
        except requests.exceptions.ConnectionError:
            print("✗ Cannot reach Vector API")
            print(f"  URL: {self.base_url}")
            print(
                "  Check if the vector server is running and the ngrok tunnel is active"
            )
            sys.exit(1)
        except requests.exceptions.Timeout:
            print("✗ Request timed out")
            print(f"  URL: {self.base_url}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"✗ Request failed: {e}")
            sys.exit(1)

    def history(self, scope: str = "project", limit: int = 10):
        """List recent saves from collection"""
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        if scope == "project":
            project_id = self.get_project_id()
            payload = {"project_id": project_id, "limit": limit}
            endpoint = "/list/project"
        else:
            payload = {"limit": limit}
            endpoint = "/list/global"

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            documents = result.get("documents", [])
            collection = result.get("collection", scope)

            if not documents:
                print(f"No saves found in {collection}")
                return []

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📜 Recent saves ({collection}):")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            for i, doc in enumerate(documents, 1):
                meta = doc.get("metadata", {})
                created = (
                    meta.get("created_at", "Unknown")[:10]
                    if meta.get("created_at")
                    else "Unknown"
                )
                text = doc.get("text", "")[:50] + (
                    "..." if len(doc.get("text", "")) > 50 else ""
                )
                print(f"[{i}] {created} | {text}")

            print(f"\nTotal: {len(documents)} entries")
            return documents

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching history: {e}", file=sys.stderr)
            sys.exit(1)

    def delete_history_by_index(
        self, index: int, scope: str = "project", dry_run: bool = False
    ):
        """Delete a history entry by its visual index"""
        # Fetch enough history to cover the index
        limit = index + 5

        # Suppress stdout temporarily since history() prints the list
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            documents = self.history(scope=scope, limit=limit)

        if not documents:
            print(f"No history found in {scope} to delete from.", file=sys.stderr)
            return

        if index < 1 or index > len(documents):
            print(f"Index {index} out of range (1-{len(documents)})", file=sys.stderr)
            return

        # Indices are 1-based for display, 0-based for list
        target_doc = documents[index - 1]
        doc_id = target_doc.get("id")
        text = target_doc.get("text", "")[:50] + "..."

        if not doc_id:
            print("Error: Could not determine ID for this entry.", file=sys.stderr)
            return

        print(f"Target: [{index}] {text}")

        if dry_run:
            print("Dry run: No changes made.")
            return

        collection = (
            f"project_{self.get_project_id()}" if scope == "project" else "global"
        )

        try:
            response = requests.post(
                f"{self.base_url}/delete/document",
                headers=self.headers,
                json={"collection": collection, "ids": [doc_id]},
                timeout=30,
            )
            response.raise_for_status()
            print(f"✓ Deleted item {index}")
        except Exception as e:
            print(f"✗ Failed to delete: {e}", file=sys.stderr)

    def delete_bulk(
        self,
        scope: str = "project",
        older_than_days: int = None,
        duplicates: bool = False,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """Remove duplicates and/or old entries from collection"""
        if scope == "project" and not self.is_initialized():
            print("⚠️  Project not initialized. Run 'vmem init' first.", file=sys.stderr)
            sys.exit(1)

        from datetime import datetime, timedelta
        from collections import defaultdict

        # Setup for pagination
        if scope == "project":
            project_id = self.get_project_id()
            base_payload = {"project_id": project_id, "limit": 1000}
            endpoint = "/list/project"
            collection = f"project_{project_id}"
        else:
            base_payload = {"limit": 1000}
            endpoint = "/list/global"
            collection = "global"

        # Fetch all documents with pagination
        documents = []
        offset = 0
        print(f"Fetching documents from {collection}...", end="", flush=True)

        try:
            while True:
                payload = {**base_payload, "offset": offset}
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()
                result = response.json()
                batch = result.get("documents", [])

                if not batch:
                    break

                documents.extend(batch)
                offset += len(batch)
                print(f" {len(documents)}...", end="", flush=True)

                # Stop if we got fewer than limit (last page)
                if len(batch) < 1000:
                    break

            print(f" Done. Total: {len(documents)}")

        except Exception as e:
            print(f"\n✗ Error fetching documents: {e}", file=sys.stderr)
            sys.exit(1)

        if not documents:
            print(f"No documents found in {collection}")
            return

        to_delete = []

        # 1. Old entries
        if older_than_days is not None:
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            for doc in documents:
                created_str = doc.get("metadata", {}).get("created_at")
                if not created_str:
                    continue
                try:
                    # Parse ISO format (handle potential Z)
                    created_at = datetime.fromisoformat(
                        created_str.replace("Z", "+00:00")
                    )
                    if created_at < cutoff.replace(tzinfo=created_at.tzinfo):
                        to_delete.append(doc["id"])
                        if verbose:
                            print(
                                f"  Target (Old): [{created_str[:10]}] {doc.get('text', '')[:30]}..."
                            )
                except ValueError:
                    continue

        # 2. Duplicates (exact text match)
        if duplicates:
            seen_texts = defaultdict(list)
            for doc in documents:
                text = doc.get("text", "")
                if text:
                    seen_texts[text].append(doc)

            for text, docs in seen_texts.items():
                if len(docs) > 1:
                    # Keep the most recent one, delete others
                    # documents are sorted by created_at desc, so index 0 is newest
                    # Wait, list endpoint sorts by created_at desc.
                    # So docs[0] is newest. Delete docs[1:]
                    for duplicate in docs[1:]:
                        to_delete.append(duplicate["id"])
                        if verbose:
                            print(
                                f"  Target (Dupe): {duplicate.get('text', '')[:30]}..."
                            )

        if not to_delete:
            print("No documents found matching criteria.")
            return

        unique_ids = list(set(to_delete))
        print(f"\nFound {len(unique_ids)} items to delete.")

        if dry_run:
            print("Dry run: No changes made.")
            return

        confirm = input("Delete these items? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        # Batch delete
        batch_size = 100
        for i in range(0, len(unique_ids), batch_size):
            batch = unique_ids[i : i + batch_size]
            try:
                response = requests.post(
                    f"{self.base_url}/delete/document",
                    headers=self.headers,
                    json={"collection": collection, "ids": batch},
                    timeout=30,
                )
                response.raise_for_status()
                print(f"✓ Deleted batch {i // batch_size + 1}")
            except Exception as e:
                print(f"✗ Failed to delete batch: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Vector Memory CLI - Universal memory for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vmem save "API uses JWT authentication"
  vmem save "Docker config" --global
  vmem query "authentication method"
  vmem query "docker" --global
  vmem search "deployment"
  vmem status
  vmem toggle on
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Save command
    save_parser = subparsers.add_parser(
        "save", help="Save information to vector storage"
    )
    save_parser.add_argument("text", help="Text to save")
    save_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force save (bypass auto-save toggle)",
    )
    save_parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Save to global collection (default: project)",
    )
    save_parser.add_argument("--tags", help="Comma-separated tags")
    save_parser.add_argument(
        "--importance", choices=["low", "medium", "high"], help="Importance level"
    )
    save_parser.add_argument(
        "--type", default="note", help="Content type (note, workflow, bug, etc.)"
    )
    save_parser.add_argument(
        "--agent", default="cli", help="Agent name (claude-code, codex, gemini, etc.)"
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Search vector storage")
    query_parser.add_argument("query", help="Search query")
    query_parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Search global collection (default: project)",
    )
    query_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results (default: 5)"
    )
    query_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Search command (both collections)
    search_parser = subparsers.add_parser(
        "search", help="Search both project and global"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results per collection (default: 3)",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output as JSON (for scripts/hooks)",
    )

    # Toggle command
    toggle_parser = subparsers.add_parser("toggle", help="Set auto-save mode")
    toggle_parser = subparsers.add_parser(
        "toggle", help="Enable/disable/prompt auto-save"
    )
    toggle_parser.add_argument("mode", choices=["off", "on"], help="Auto-save mode")

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize vmem in current project"
    )
    init_parser.add_argument(
        "mode", nargs="?", choices=["on"], help='Use "on" to enable auto-save and hooks'
    )

    # Uninit command
    subparsers.add_parser(
        "uninit", help="Completely remove vmem from project (local & remote)"
    )

    # Update command (deprecated/internal alias)
    # subparsers.add_parser("update", help="Update vmem documentation files (vmem.md)")

    # Add-Agent command
    subparsers.add_parser("add-agent", help="Add agent config files and folders")

    # Upgrade-Docs command
    subparsers.add_parser("upgrade-docs", help="Refresh documentation files")

    # Hooks command
    hooks_parser = subparsers.add_parser("hooks", help="Manage Claude Code hooks")
    hooks_parser.add_argument(
        "action",
        choices=["on", "off", "status"],
        help="Enable, disable, or check hooks status",
    )

    # Ping command
    subparsers.add_parser("ping", help="Check server connectivity")

    # History command
    history_parser = subparsers.add_parser("history", help="Show recent saves")
    history_parser.add_argument(
        "--limit", type=int, default=10, help="Number of entries (default: 10)"
    )
    history_parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Show global collection history",
    )

    # Compact command (save compact)
    compact_parser = subparsers.add_parser(
        "compact", help="Save a project snapshot (max 10 kept)"
    )
    compact_parser.add_argument("text", help="Compact text (can be long)")
    compact_parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Save to global collection",
    )

    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve compacts")
    retrieve_parser.add_argument("what", choices=["compact"], help="What to retrieve")
    retrieve_parser.add_argument(
        "index",
        nargs="?",
        type=int,
        default=1,
        help="Compact index (1=newest, 5=oldest)",
    )
    retrieve_parser.add_argument(
        "--all", dest="show_all", action="store_true", help="List all compacts"
    )
    retrieve_parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Retrieve from global collection",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete specific items")
    delete_parser.add_argument(
        "target",
        nargs="?",
        help="Item to delete: 'compact', index number, or leave empty for bulk flags",
    )
    delete_parser.add_argument(
        "index",
        nargs="?",
        type=int,
        help="Index to delete (required if target is 'compact')",
    )
    delete_parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Delete from global collection",
    )
    delete_parser.add_argument(
        "--days", "--older-than", dest="days", type=int, help="Delete older than N days"
    )
    delete_parser.add_argument(
        "--dupes",
        "--duplicates",
        dest="duplicates",
        action="store_true",
        help="Delete duplicates",
    )
    delete_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without deleting"
    )
    delete_parser.add_argument(
        "--all",
        action="store_true",
        help="Delete all items (use with caution, mostly for compacts)",
    )
    delete_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    vm = VectorMemory()

    if args.command == "save":
        metadata = {"type": args.type}
        if args.tags:
            metadata["tags"] = [t.strip() for t in args.tags.split(",")]
        if args.importance:
            metadata["importance"] = args.importance

        scope = "global" if args.global_scope else "project"
        vm.save(
            args.text,
            scope=scope,
            metadata=metadata,
            agent=args.agent,
            force=args.force,
        )

    elif args.command == "query":
        scope = "global" if args.global_scope else "project"
        format_type = "json" if args.json else "text"
        vm.query(args.query, scope=scope, top_k=args.top_k, output_format=format_type)

    elif args.command == "search":
        vm.search_all(args.query, top_k=args.top_k)

    elif args.command == "status":
        vm.status(json_output=args.json_output)

    elif args.command == "toggle":
        vm.toggle(args.mode)

    elif args.command == "init":
        enable_hooks = (
            args.mode == "on" if hasattr(args, "mode") and args.mode else False
        )
        vm.init(enable_hooks=enable_hooks)

    elif args.command == "uninit":
        vm.uninit()

    elif args.command == "hooks":
        vm.hooks(args.action)

    elif args.command == "add-agent":
        vm.add_agent()

    elif args.command == "upgrade-docs":
        vm.upgrade_docs()

    elif args.command == "ping":
        vm.ping()

    elif args.command == "history":
        scope = "global" if args.global_scope else "project"
        vm.history(scope=scope, limit=args.limit)

    elif args.command == "compact":
        scope = "global" if args.global_scope else "project"
        vm.save_compact(args.text, scope=scope)

    elif args.command == "retrieve":
        if args.what == "compact":
            scope = "global" if args.global_scope else "project"
            vm.retrieve_compact(index=args.index, scope=scope, show_all=args.show_all)

    elif args.command == "delete":
        scope = "global" if args.global_scope else "project"

        # Helper to check if any bulk flag is set
        is_bulk = args.days is not None or args.duplicates

        if args.target == "compact":
            # Check for bulk flags first
            is_compact_bulk = args.days is not None or getattr(args, "all", False)

            if is_compact_bulk:
                vm.delete_compact_bulk(
                    scope=scope,
                    older_than_days=args.days,
                    delete_all=getattr(args, "all", False),
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                )
            elif args.index is None:
                print(
                    "Usage: vmem delete compact <index> OR vmem delete compact --older-than <days>",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                vm.delete_compact_by_index(
                    index=args.index, scope=scope, dry_run=args.dry_run
                )
        elif is_bulk:
            if args.target:
                print(
                    f"⚠️  Ignoring target '{args.target}' because bulk flags are set.",
                    file=sys.stderr,
                )

            # Call delete_bulk
            vm.delete_bulk(
                scope=scope,
                older_than_days=args.days,
                duplicates=args.duplicates,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
        elif args.target:
            # Check if target is an integer (delete by history index)
            try:
                index = int(args.target)
                vm.delete_history_by_index(
                    index=index, scope=scope, dry_run=args.dry_run
                )
            except ValueError:
                print(
                    f"Unknown delete target: '{args.target}'.\nUse 'compact', an integer index, or flags like --duplicates.",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print(
                "Error: Specify a target (index/compact) or use bulk flags (--days/--dupes).",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
