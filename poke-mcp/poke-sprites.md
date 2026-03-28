# Setting up Poke to have filesystem access

We'll use fly.io's sprites to give Poke filesystem access.

## Set up sprites

```bash
curl -fsSL https://sprites.dev/install.sh | sh
sprite create <name>

# First time creation should open the console by default.
# In the future, you may need to run `use` and then `console` to open the sprite.
sprite use <name>
sprite console
```

## Set up the filesystem mcp

```bash
# install an MCP server that exposes shell + filesystem tools
# e.g. the filesystem one, or a more general shell one
npm install -g @modelcontextprotocol/server-filesystem

# Install mcp python packages for HTTP transport (not just stdio)
pip install mcp-proxy mcp
```

## Set up mcp servers on your sprite

Use `sprite-env` to create services that spin up on wake.

```bash
PROXY_PATH=$(which mcp-proxy)
echo $PROXY_PATH  # verify it found something

cat > /home/sprite/start-mcp.sh << EOF
#!/bin/bash
exec $PROXY_PATH --port 8081 -- npx @modelcontextprotocol/server-filesystem /home/sprite
EOF

chmod +x /home/sprite/start-mcp.sh

sprite-env services create mcp-server --cmd /home/sprite/start-mcp.sh
```

Set up git mcp and credentials.


```bash
git config --global credential.helper store
echo "https://x-access-token:github_pat_...@github.com" > ~/.git-credentials

git config --global user.name "poke-bot"
git config --global user.email "caden+poke-bot@example.com"
```

Create the git mcp. Copy `/tools/git-server.py` to a file.

```bash
PROXY_PATH=$(which mcp-proxy)

cat > /home/sprite/start-git-mcp.sh << EOF
#!/bin/bash
cd /home/sprite/sinnoh && git pull
exec $PROXY_PATH --port 8082 -- python /home/sprite/git-server.py
EOF
chmod +x /home/sprite/start-git-mcp.sh

sprite-env services create git-mcp --cmd /home/sprite/start-git-mcp.sh
```

## Set up NGNIX

sprites only forward 8080 by default. Set up an ngnix server to forward our internal ports.

```bash
sudo apt install -y nginx

cat > /etc/nginx/sites-enabled/default << 'EOF'
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
EOF

cat > /home/sprite/start-nginx.sh << 'EOF'
#!/bin/bash
exec nginx -g 'daemon off;'
EOF
chmod +x /home/sprite/start-nginx.sh

sprite-env services create nginx --cmd /home/sprite/start-nginx.sh
```

## Set up the Poke MCP

To get:
- The `<url>`, run `sprite list` to view your list of sprites and copy the url.
- The `<sprite-auth-token>` visit the `sprites.dev` dashboard and create a token.

```bash
poke mcp add https://<url>/fs/mcp \
  --name "Sprite FS" \
  --api-key <sprite-auth-token>

poke mcp add https://ndif--poke-mcp-git-server.modal.run/mcp \
    --name "codemcp" \
    --api-key <sprite-auth-token>
```