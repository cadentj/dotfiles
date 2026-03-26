#!/usr/bin/env bash
# Poke sprite MCP setup (see poke-sprites.md).
# Prerequisites on the sprite: sprite CLI installed, `sprite use <name>` for this machine,
# and this dotfiles repo cloned (any path). Run:
#   cd /path/to/dotfiles/tools && bash setup.sh
# Or from repo root: bash tools/setup.sh
#
# Fill in CONFIG below before running.

set -euo pipefail

# --- CONFIG: edit placeholders before running ---
GITHUB_PAT="<GITHUB_PAT>"
GIT_USER_NAME="poke-bot"
GIT_USER_EMAIL="caden+poke-bot@example.com"
# Clone or sync your repo here; must match what git MCP tools use.
SINNOH_REPO_PATH="/home/sprite/sinnoh"
# After setup, add MCPs in Poke (local machine). From `sprite list` and sprites.dev dashboard:
SPRITE_URL="<SPRITE_URL>"
SPRITE_AUTH_TOKEN="<SPRITE_AUTH_TOKEN>"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_SERVER_SRC="$SCRIPT_DIR/git-server.py"
SPRITE_HOME="/home/sprite"
DEST_GIT_SERVER="$SPRITE_HOME/git-server.py"
START_MCP="$SPRITE_HOME/start-mcp.sh"
START_GIT_MCP="$SPRITE_HOME/start-git-mcp.sh"
START_NGINX="$SPRITE_HOME/start-nginx.sh"

die() { echo "error: $*" >&2; exit 1; }

[[ -f "$GIT_SERVER_SRC" ]] || die "missing $GIT_SERVER_SRC (run from cloned dotfiles repo)"

placeholder_ok() {
  local v="$1"
  [[ -n "$v" && "$v" != *'<'* ]]
}

if ! placeholder_ok "$GITHUB_PAT"; then
  die "set GITHUB_PAT in this script (GitHub PAT for https git)"
fi
if ! placeholder_ok "$GIT_USER_NAME"; then
  die "set GIT_USER_NAME in this script"
fi
if ! placeholder_ok "$GIT_USER_EMAIL"; then
  die "set GIT_USER_EMAIL in this script"
fi

command -v npm >/dev/null || die "npm not found"
command -v python3 >/dev/null || die "python3 not found"
command -v sprite-env >/dev/null || die "sprite-env not found (install/configure sprite tooling)"

echo "==> Installing MCP packages"
npm install -g @modelcontextprotocol/server-filesystem
python3 -m pip install --user mcp-proxy mcp

export PATH="${HOME}/.local/bin:${PATH}"
PROXY_PATH="$(command -v mcp-proxy || true)"
[[ -n "$PROXY_PATH" ]] || die "mcp-proxy not on PATH after pip install (~/.local/bin may need to be on PATH)"

echo "==> mcp-proxy at $PROXY_PATH"

echo "==> Writing $START_MCP"
cat > "$START_MCP" << EOF
#!/bin/bash
exec $PROXY_PATH --port 8081 -- npx @modelcontextprotocol/server-filesystem $SPRITE_HOME
EOF
chmod +x "$START_MCP"

echo "==> sprite-env: mcp-server (ignore error if service already exists)"
sprite-env services create mcp-server --cmd "$START_MCP" || true

echo "==> Git credentials and identity"
git config --global credential.helper store
printf 'https://x-access-token:%s@github.com\n' "$GITHUB_PAT" > "$SPRITE_HOME/.git-credentials"
chmod 600 "$SPRITE_HOME/.git-credentials"
git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"

echo "==> Deploying git MCP server to $DEST_GIT_SERVER"
sed "s|/home/sprite/sinnoh|${SINNOH_REPO_PATH}|g" "$GIT_SERVER_SRC" > "$DEST_GIT_SERVER"

echo "==> Writing $START_GIT_MCP"
cat > "$START_GIT_MCP" << EOF
#!/bin/bash
cd $SINNOH_REPO_PATH && git pull
exec $PROXY_PATH --port 8082 -- python3 $DEST_GIT_SERVER
EOF
chmod +x "$START_GIT_MCP"

echo "==> sprite-env: git-mcp (ignore error if service already exists)"
sprite-env services create git-mcp --cmd "$START_GIT_MCP" || true

echo "==> nginx (requires sudo)"
sudo apt-get update -qq
sudo apt-get install -y nginx

sudo tee /etc/nginx/sites-enabled/default >/dev/null << 'NGINXEOF'
server {
    listen 8080;

    location /fs/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }

    location /git/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }
}
NGINXEOF

cat > "$START_NGINX" << 'EOF'
#!/bin/bash
exec nginx -g 'daemon off;'
EOF
chmod +x "$START_NGINX"

echo "==> sprite-env: nginx (ignore error if service already exists)"
sprite-env services create nginx --cmd "$START_NGINX" || true

echo ""
echo "==> Done. If pip installed to ~/.local/bin, ensure it is on PATH for sprite services."
echo ""

if placeholder_ok "$SPRITE_URL" && placeholder_ok "$SPRITE_AUTH_TOKEN"; then
  # SPRITE_URL: full base URL from \`sprite list\`, e.g. https://your-sprite.sprites.dev (no trailing slash)
  base="${SPRITE_URL%/}"
  echo "Add these MCPs in Poke (run on your local machine where \`poke\` is installed):"
  echo ""
  echo "poke mcp add ${base}/fs/mcp \\"
  echo "  --name \"Sprite FS\" \\"
  echo "  --api-key $SPRITE_AUTH_TOKEN"
  echo ""
  echo "poke mcp add ${base}/git/mcp \\"
  echo "    --name \"Git\" \\"
  echo "    --api-key $SPRITE_AUTH_TOKEN"
  echo ""
else
  echo "Set SPRITE_URL and SPRITE_AUTH_TOKEN in this script and re-run to print \`poke mcp add\` commands,"
  echo "or add manually (see poke-sprites.md):"
  echo "  - URL: sprite list"
  echo "  - Token: sprites.dev dashboard"
fi
