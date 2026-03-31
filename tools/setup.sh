#!/usr/bin/env bash
# Run on the sprite with dotfiles cloned. See poke-sprites.md.
# Edit the three values below, then: bash dotfiles/tools/setup.sh

GITHUB_PAT="<github-pat>"
SPRITE_URL="https://<sprite-url>"
SPRITE_AUTH_TOKEN="<sprite-auth-token>"

#######################
# Set Git credentials #
#######################

git config --global credential.helper store
echo "https://x-access-token:${GITHUB_PAT}@github.com" > ~/.git-credentials

git config --global user.name "poke-bot"
git config --global user.email "caden+poke-bot@example.com"

########################
# Install MCP servers #
########################

pip install mcp-proxy mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
sudo apt install -y ripgrep nginx

SCRIPTS_DIR=$(python -c 'import sysconfig; print(sysconfig.get_path("scripts"))')
PROXY_PATH="${SCRIPTS_DIR}/mcp-proxy"
if [ ! -x "$PROXY_PATH" ]; then
  echo "mcp-proxy not found at $PROXY_PATH" >&2
  exit 1
fi
echo "$PROXY_PATH"

##################
# Filesystem MCP #
##################

cat > /home/sprite/start-mcp.sh << EOF
#!/usr/bin/env bash
set -euo pipefail
cd /home/sprite
exec "$PROXY_PATH" --port 8081 -- python /home/sprite/code-mcp.py
EOF
chmod +x /home/sprite/start-mcp.sh

sprite-env services create mcp-server --cmd /home/sprite/start-mcp.sh

###########
# Git MCP #
###########

cat > /home/sprite/start-git-mcp.sh << EOF
#!/usr/bin/env bash
set -euo pipefail
cd /home/sprite
exec "$PROXY_PATH" --port 8082 -- python /home/sprite/git-mcp.py
EOF
chmod +x /home/sprite/start-git-mcp.sh

sprite-env services create git-mcp --cmd /home/sprite/start-git-mcp.sh

############
# Docs MCP #
############

cat > /home/sprite/start-docs-mcp.sh << EOF
#!/usr/bin/env bash
set -euo pipefail
cd /home/sprite
exec "$PROXY_PATH" --port 8083 -- python /home/sprite/docs-mcp.py
EOF
chmod +x /home/sprite/start-docs-mcp.sh

sprite-env services create docs-mcp --cmd /home/sprite/start-docs-mcp.sh

################
# Set up NGINX #
################

sudo tee /etc/nginx/sites-enabled/default << 'EOF'
server {
    listen 8080;

    location /code/ {
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

    location /docs/ {
        proxy_pass http://127.0.0.1:8083/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }
}
EOF

cat > /home/sprite/start-nginx.sh << 'EOF'
#!/bin/bash
exec nginx -g 'daemon off;'
EOF
chmod +x /home/sprite/start-nginx.sh

sprite-env services create nginx --cmd /bin/bash -- /home/sprite/start-nginx.sh

########################

echo
echo "On your machine (where poke is installed):"
echo "poke mcp add ${SPRITE_URL}/code/mcp \\"
echo "  --name \"Sprite Code MCP\" \\"
echo "  --api-key ${SPRITE_AUTH_TOKEN}"
echo
echo "poke mcp add ${SPRITE_URL}/git/mcp \\"
echo "    --name \"Sprite Git MCP\" \\"
echo "    --api-key ${SPRITE_AUTH_TOKEN}"
echo
echo "poke mcp add ${SPRITE_URL}/docs/mcp \\"
echo "    --name \"Sprite Docs MCP\" \\"
echo "    --api-key ${SPRITE_AUTH_TOKEN}"
