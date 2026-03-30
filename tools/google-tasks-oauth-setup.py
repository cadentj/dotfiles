#!/usr/bin/env python3
"""One-time OAuth to obtain a refresh token for google-tasks-mcp.

Requires: pip install google-auth-oauthlib google-auth-httplib2

1. Create OAuth 2.0 Desktop credentials in Google Cloud Console.
2. Enable Google Tasks API for the project.
3. Run:
   GOOGLE_TASKS_CLIENT_ID=... GOOGLE_TASKS_CLIENT_SECRET=... python google-tasks-oauth-setup.py

Copy the printed refresh_token into your env or credentials JSON.
"""

import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

SCOPE = "https://www.googleapis.com/auth/tasks"


def main() -> None:
    cid = os.environ.get("GOOGLE_TASKS_CLIENT_ID", "").strip()
    secret = os.environ.get("GOOGLE_TASKS_CLIENT_SECRET", "").strip()
    if not cid or not secret:
        print(
            "Set GOOGLE_TASKS_CLIENT_ID and GOOGLE_TASKS_CLIENT_SECRET.",
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
