#!/usr/bin/env bash
# Copy local MCP/setup scripts into /home/sprite/ on the active sprite (sprite use).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sprite exec \
  --file "${SCRIPT_DIR}/code-mcp.py:/home/sprite/code-mcp.py" \
  --file "${SCRIPT_DIR}/edit.py:/home/sprite/edit.py" \
  --file "${SCRIPT_DIR}/git-mcp.py:/home/sprite/git-mcp.py" \
  --file "${SCRIPT_DIR}/setup.sh:/home/sprite/setup.sh" \
  -- ls -la /home/sprite/code-mcp.py /home/sprite/edit.py /home/sprite/git-mcp.py /home/sprite/setup.sh
