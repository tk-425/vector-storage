# vmem CLI

The command-line interface for vector memory operations.

## Installation

```bash
cp vmem.py ~/.bin/vmem
chmod +x ~/.bin/vmem
```

Make sure `~/.bin` is in your PATH:

```bash
export PATH="$HOME/.bin:$PATH"
```

## Environment Variables

Add to `~/.zshrc`:

```bash
export VECTOR_BASE_URL="https://your-ngrok-url.ngrok-free.dev"
export VECTOR_AUTH_TOKEN="your-token"
```

## Quick Reference

```bash
vmem save "text"            # Save to project
vmem query "term"           # Search project
vmem search "term"          # Search project + global
vmem status                 # Check auto-save mode
vmem toggle on              # Enable auto-save
vmem ping                   # Test connectivity
vmem history                # Recent saves
vmem prune --duplicates     # Remove duplicates
vmem prune compact --all    # Remove all compacts
vmem compact "text"         # Save project snapshot
vmem retrieve compact       # Get latest compact
```

## Files

| File               | Purpose                         |
| ------------------ | ------------------------------- |
| `vmem.py`          | CLI implementation              |
| `vmem-cli-tool.md` | Full command reference (legacy) |
