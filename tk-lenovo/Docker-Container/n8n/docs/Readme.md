# Accounts
Gemini - wtk4949@gmail.com
Ngrok - wtk4949@gmail.com


# For `.env`

## File-System Permissions
Limit who can read the file.
```bash
chmod 600 .env
chown $USER:$USER .env
```
Output: 
Only your user can read/write the file. No other local users can access secrets.

## Gitignore
Ensure it's never committed.
```bash
echo ".env" >> .gitignore
```

If it were ever commited:
```bash
git rm --cached .env
git commit -m "Remove .env from repository"
```

# Change Home directory

Change the home directory path from files to your current home directory.
Files that needs to be fixed:
- `docker-compose.yml`
- `compose-*.sh`

# Dockerfile
Dockerfile is needed

# Gemini
> **Gemini CLI is running *inside the n8n container*, not on your host**, and the way the `.gemini` directories are mounted is preventing Gemini from writing required files.

Let’s break this down precisely and fix it.

---

## What is actually happening (root cause)

From the error:

```
EROFS: read-only file system, open '/home/node/.gemini/oauth_creds.json'
EACCES: permission denied, mkdir '/home/node/.gemini/tmp/.../chats'
```

This tells us **three important facts**:

1. The `Execute Command` node runs **inside the container**
2. Gemini CLI **needs to write**:

   * OAuth credentials
   * Session / chat cache
   * Temp files
3. Your mount is **read-only**, so Gemini cannot write

You currently have:

```yaml
- /home/tk-lenovo/.gemini:/home/node/.gemini:ro
```

That `:ro` is the problem.

---

## Key clarification: “local Gemini” vs container Gemini

Even though:

* Gemini CLI is installed on your host
* Credentials exist on your host

Once you run:

```yaml
type: executeCommand
command: gemini ...
```

👉 **That command executes inside the n8n container**, as user `node`.

So:

* Gemini must exist **inside the image**
* Gemini must be able to **write to `/home/node/.gemini`**

There is no way for `Execute Command` to call your host shell directly.

---

## ✅ Correct fix (RECOMMENDED)

### 1. Make `.gemini` writable (remove `:ro`)

Update **both** n8n services:

```yaml
volumes:
  - /home/tk-lenovo/.gemini:/home/node/.gemini
  - /home/tk-lenovo/.gemini-tmp:/home/node/.gemini/tmp
```

❌ Remove `:ro`

---

### 2. Fix host permissions (very important)

On your host machine:

```bash
sudo chown -R 1000:1000 /home/tk-lenovo/.gemini
sudo chown -R 1000:1000 /home/tk-lenovo/.gemini-tmp
```

**Why:**
The `n8n` container runs as user `node` (UID 1000).
Without this, you will get `EACCES`.

---

### 3. Restart cleanly

```bash
docker compose down
docker compose up -d
```

---

## Verify inside the container (optional but useful)

```bash
docker exec -it n8n-primary sh
ls -la /home/node/.gemini
touch /home/node/.gemini/test.txt
```

If `touch` works → permissions are correct.

---

## Why this happens specifically with Gemini CLI

Gemini CLI **always writes**:

* OAuth cache
* Session metadata
* Chat recordings
* Temp JSON blobs

Even with:

```bash
--allowed-tools none
--approval-mode yolo
```

It still needs filesystem write access.

---

## Important best-practice note

If you want **maximum isolation**, the *better long-term pattern* is:

```
/home/node/.gemini          → writable volume
/home/node/.gemini/config   → secrets only
```

But for now, your approach is perfectly fine.

---

## Summary (one sentence)

> The error occurs because Gemini CLI runs inside the n8n container and cannot write to `/home/node/.gemini` due to a read-only mount and permissions mismatch.

> You are sharing only the Gemini OAuth data from the host, while the Gemini CLI itself runs entirely inside the Docker container.

---

