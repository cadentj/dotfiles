#!/usr/bin/env python3
"""One-time OAuth to obtain a refresh token for google-tasks-mcp.

Requires: pip install google-auth-oauthlib google-auth-httplib2

1. Create OAuth 2.0 Desktop credentials in Google Cloud Console and download JSON.
2. Enable Google Tasks API for the project.
3. Either:
     GOOGLE_TASKS_CLIENT_SECRETS_JSON=/path/to/client_secret....json python ...
   or:
     GOOGLE_TASKS_CLIENT_ID=... GOOGLE_TASKS_CLIENT_SECRET=... python ...

Save the printed refresh_token into GOOGLE_TASKS_TOKEN_JSON on the sprite, or env.
"""

import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

SCOPE = "https://www.googleapis.com/auth/tasks"


def main() -> None:
    secrets_path = os.environ.get("GOOGLE_TASKS_CLIENT_SECRETS_JSON", "").strip()
    if secrets_path and os.path.isfile(secrets_path):
        flow = InstalledAppFlow.from_client_secrets_file(secrets_path, scopes=[SCOPE])
    else:
        cid = os.environ.get("GOOGLE_TASKS_CLIENT_ID", "").strip()
        secret = os.environ.get("GOOGLE_TASKS_CLIENT_SECRET", "").strip()
        if not cid or not secret:
            print(
                "Set GOOGLE_TASKS_CLIENT_SECRETS_JSON to the downloaded JSON, or "
                "GOOGLE_TASKS_CLIENT_ID and GOOGLE_TASKS_CLIENT_SECRET.",
                file=sys.stderr,
            )
            sys.exit(1)
        client_config = {
            "installed": {
                "client_id": cid,
                "client_secret": secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=[SCOPE])
    creds = flow.run_local_server(port=0)
    print("refresh_token:", creds.refresh_token)
    print("\nAdd to sprite env or credentials file:")
    print(f'  GOOGLE_TASKS_REFRESH_TOKEN="{creds.refresh_token}"')


if __name__ == "__main__":
    main()
