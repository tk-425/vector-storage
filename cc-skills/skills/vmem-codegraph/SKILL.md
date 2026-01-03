---
name: vmem-codegraph
description: Combined skill for using vector memory (vmem) with code-graph for complete code understanding. Vector memory provides WHY/WHAT context, code-graph provides WHERE locations.
---

# vmem + Code-Graph Integration

**The Perfect Combination:**

- **vmem** → Remembers WHY (context, decisions, history)
- **code-graph** → Finds WHERE (file:line locations)

Use BOTH together for complete code understanding.

## When to Use Which

| Question Type           | Tool       | Example                         |
| ----------------------- | ---------- | ------------------------------- |
| "How does X work?"      | vmem first | `vmem query "authentication"`   |
| "Where is X defined?"   | code-graph | `/cg-search "authenticateUser"` |
| "Show me X code"        | Both       | vmem → code-graph → read file   |
| "Why did we choose X?"  | vmem only  | `vmem query "why JWT"`          |
| "Who calls X?"          | code-graph | `/cg-callers "validateToken"`   |
| "What bugs did we fix?" | vmem only  | `vmem query "bug fix"`          |

## Combined Workflow

### Pattern 1: "Show me the code for X"

```bash
# Step 1: Get context from vmem
vmem query "authentication"
# Returns: "JWT auth via authenticateUser() in src/auth..."

# Step 2: Extract function name, use code-graph
/cg-search "authenticateUser"
# Returns: src/auth/passport.ts:34

# Step 3: Read the file at that location
```

### Pattern 2: "How does X work?"

```bash
# Step 1: vmem for high-level understanding
vmem query "caching strategy"
# Returns: "Redis caching with 5min TTL, cacheUser()..."

# Step 2: code-graph for details
/cg-search "cacheUser"
/cg-callees "cacheUser"  # What it calls
/cg-callers "cacheUser"  # Who calls it
```

### Pattern 3: After Implementation

```bash
# Step 1: Complete the work
# (implement feature, fix bug, etc.)

# Step 2: Save to vmem WITH function names
vmem save "Password reset via resetPassword() in src/auth/reset.ts. Uses email tokens with 1-hour expiry."

# This enables future code-graph lookups!
```

## Key Rule: Save Function Names

When saving to vmem, **always include function names and file paths** for code implementations:

**Good (enables code-graph lookup):**

```
"JWT auth via authenticateUser() in src/auth/passport.ts.
 Token validation: validateToken(). 24-hour expiry."
```

**Bad (code-graph can't help later):**

```
"We use JWT authentication with tokens."
```

The function names in vmem become search terms for code-graph later.

## Quick Reference

### vmem Commands

| Command                    | Purpose                 |
| -------------------------- | ----------------------- |
| `vmem query "term"`        | Search project memory   |
| `vmem search "term"`       | Search project + global |
| `vmem save "text"`         | Save (respects toggle)  |
| `vmem save "text" --force` | Force save              |
| `vmem history`             | Show recent saves       |
| `vmem status`              | Check auto-save mode    |

### code-graph Commands

| Command                | Purpose                  |
| ---------------------- | ------------------------ |
| `/cg-init`             | Initialize in project    |
| `/cg-build`            | Rebuild databases        |
| `/cg-search "name"`    | Find symbol definition   |
| `/cg-callers "name"`   | Who calls this function  |
| `/cg-callees "name"`   | What this function calls |
| `/cg-signature "name"` | Get function signature   |

## Example Session

```
User: "Show me how we handle authentication"

AI Process:
1. vmem query "authentication"
   → Returns: "JWT authentication via authenticateUser() in
      src/auth/passport.ts. Tokens stored in httpOnly cookies.
      24-hour expiration. Uses jsonwebtoken library."

2. /cg-search "authenticateUser"
   → Returns: src/auth/passport.ts:34

3. Read file and show code to user

AI Response:
"We use JWT authentication with httpOnly cookies and 24-hour
expiration. Here's the main function:

[Shows code from src/auth/passport.ts:34]

The authenticateUser function validates tokens using
jsonwebtoken. Want me to show the token generation code too?"
```

## Comparison Table

| Aspect       | vmem                        | code-graph                |
| ------------ | --------------------------- | ------------------------- |
| **Data**     | Summaries, decisions, notes | Code symbols, call graphs |
| **Storage**  | Vector database (ChromaDB)  | Local SQLite              |
| **Search**   | Semantic similarity         | Exact symbol match        |
| **Speed**    | ~300ms (network)            | <100ms (local)            |
| **Best for** | "Why/What/How" questions    | "Where" questions         |
| **Offline**  | No (needs server access)    | Yes (fully local)         |

## Prerequisites

### vmem Setup

```bash
# Requires environment variables
export VECTOR_BASE_URL="https://..."
export VECTOR_AUTH_TOKEN="..."

# Test connection
vmem ping
```

### code-graph Setup

```bash
# Initialize in project (one-time)
/cg-init

# Rebuild after code changes
/cg-build
```

## Summary

1. **Start with vmem** for context and understanding
2. **Extract function names** from vmem results
3. **Use code-graph** to find exact locations
4. **Read the actual code** at those locations
5. **Save back to vmem** with function names for future lookups

**They don't overlap—they complement perfectly!**

---

**Version**: 1.0.0
**Dependencies**: vmem CLI, code-graph-skills CLI
**Offline**: vmem=No, code-graph=Yes
