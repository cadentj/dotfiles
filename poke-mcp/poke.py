import modal
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from codemcp import mcp

CURRENT_DIR = Path(__file__).parent
LOCAL_ENV_PATH = CURRENT_DIR / ".env"

load_dotenv(LOCAL_ENV_PATH)

image = (
    modal.Image.debian_slim()
    .apt_install("git", "gh")
    .run_commands(
        "git config --global credential.helper store",
        f"echo 'https://x-access-token:{os.environ.get('GITHUB_TOKEN')}@github.com' > ~/.git-credentials",
        "git config --global user.name 'poke-bot'",
        "git config --global user.email 'caden+poke-bot@example.com'",
    )
    .run_commands(
        "git clone https://github.com/cadentj/sinnoh.git /root/sinnoh",
    )
    .uv_pip_install(
        "mcp[cli]>=1.2.0",
        "ruff>=0.9.10",
        "toml>=0.10.2",
        "tomli>=2.1.1",
        "anyio>=3.7.0",
        "pyyaml>=6.0.0",
        "editorconfig>=0.17.0",
        "click>=8.1.8",
        "fastapi>=0.115.12",
        "uvicorn>=0.28.0",
        "starlette>=0.35.1",
        "pathspec>=0.12.1",
    )
    # Package import: poke.py runs as /root/poke.py; sibling `tools/` must exist in the image.
    .add_local_dir(
        local_path=str(CURRENT_DIR / "codemcp"),
        remote_path="/root/codemcp",
    )
    # Upload environment variables
    .add_local_file(
        local_path=str(LOCAL_ENV_PATH),
        remote_path="/root/.env",
    )
)

app = modal.App("poke-mcp", image=image)


def _with_api_secret(inner_app):
    """Require Authorization: Bearer <API_SECRET> or X-API-Secret when API_SECRET is set."""
    secret = os.environ.get("API_SECRET", "").strip()
    assert secret, "API_SECRET is not set"

    async def asgi(scope, receive, send):
        if scope["type"] != "http":
            return await inner_app(scope, receive, send)
        raw = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = raw.get("authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if not token:
            token = raw.get("x-api-secret", "").strip()
        ok = (
            len(token) == len(secret)
            and secrets.compare_digest(token.encode(), secret.encode())
        )
        if ok:
            return await inner_app(scope, receive, send)
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-type", b"text/plain; charset=utf-8")],
            }
        )
        await send({"type": "http.response.body", "body": b"unauthorized\n"})

    return asgi


@app.function()
@modal.concurrent(max_inputs=32)
@modal.asgi_app()
def poke_mcp():
    return _with_api_secret(mcp.streamable_http_app())