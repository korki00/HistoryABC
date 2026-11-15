"""OAuth login for the HistoryABC YouTube APIs (installed-app flow).

First run:  .venv\\Scripts\\python api\\yt_auth.py
  -> opens the browser; the user logs in and grants access themselves.
  -> stores the refresh token in api/token.json (never printed).
Other scripts call get_credentials() / youtube() / analytics().
"""
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(HERE, "client_secret.json")
TOKEN = os.path.join(HERE, "token.json")
CHANNEL_ID = "UCLJQEKmvbGIVBtpUhaGDM5g"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",  # playlists
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def get_credentials(interactive=False):
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save(creds)
            return creds
        except Exception as e:  # revoked / expired refresh token
            print(f"Token refresh failed ({type(e).__name__}).", file=sys.stderr)
    if not interactive:
        raise SystemExit("API_AUTH_NEEDED: run .venv\\Scripts\\python api\\yt_auth.py once (user login).")
    if not os.path.exists(CLIENT_SECRET):
        raise SystemExit(f"Missing {CLIENT_SECRET} (download the OAuth Desktop client JSON).")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline",
                                  open_browser=True)
    _save(creds)
    return creds


def _save(creds):
    with open(TOKEN, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def youtube(creds=None):
    return build("youtube", "v3", credentials=creds or get_credentials(), cache_discovery=False)


def analytics(creds=None):
    return build("youtubeAnalytics", "v2", credentials=creds or get_credentials(), cache_discovery=False)


if __name__ == "__main__":
    c = get_credentials(interactive=True)
    ch = youtube(c).channels().list(part="snippet", mine=True).execute()
    items = ch.get("items", [])
    if not items:
        raise SystemExit("Login worked, but no channel found for this Google account.")
    cid, title = items[0]["id"], items[0]["snippet"]["title"]
    ok = "OK" if cid == CHANNEL_ID else "WARNING: not the HistoryABC channel!"
    print(f"Authenticated: {title} ({cid}) -> {ok}")
    print(f"Refresh token saved to {TOKEN} (content not shown).")
