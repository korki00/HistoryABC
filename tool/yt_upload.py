"""Upload one of the channel's own Shorts via the YouTube Data API (videos.insert).

  .venv\\Scripts\\python api\\yt_upload.py <mp4> --title "..." [--description "..."]
                                        [--publish-at "YYYY-MM-DD HH:MM"] [--playlist "<title>"]...

Safety rules (hard-coded):
- NEVER uploads as public. Without --publish-at the video stays PRIVATE.
  With --publish-at it is uploaded private and YouTube publishes it at that time
  (local time Europe/Vienna). publishAt must be in the future.
- Until the Google Cloud project has passed the YouTube API audit, YouTube locks every
  API upload to private, and publishAt has no effect. Uploads then still use the browser.
- Not made for kids, no paid promotion, no altered/synthetic content.
Prints UPLOADED: <video id> https://youtube.com/shorts/<id>
"""
import argparse
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_auth import youtube  # noqa: E402

TZ = ZoneInfo("Europe/Vienna")
CATEGORY_EDUCATION = "27"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="history,ww2,shorts")
    ap.add_argument("--publish-at", help='"YYYY-MM-DD HH:MM" local time; omit = stays private')
    ap.add_argument("--playlist", action="append", default=[], help="existing playlist title (repeatable)")
    a = ap.parse_args()

    if not os.path.isfile(a.file):
        sys.exit(f"File not found: {a.file}")
    if len(a.title) > 100:
        sys.exit("Title longer than 100 characters.")

    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": False}
    if a.publish_at:
        when = dt.datetime.strptime(a.publish_at, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if when <= dt.datetime.now(TZ) + dt.timedelta(minutes=15):
            sys.exit("publish-at must be at least 15 minutes in the future (never publish directly).")
        status["publishAt"] = when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    assert status["privacyStatus"] == "private"  # never public

    body = {
        "snippet": {"title": a.title, "description": a.description,
                    "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
                    "categoryId": CATEGORY_EDUCATION, "defaultLanguage": "en",
                    "defaultAudioLanguage": "en"},
        "status": status,
        "paidProductPlacementDetails": {"hasPaidProductPlacement": False},
    }
    yt = youtube()
    media = MediaFileUpload(a.file, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status,paidProductPlacementDetails", body=body, media_body=media)
    resp = None
    try:
        while resp is None:
            st, resp = req.next_chunk()
            if st:
                print(f"  {int(st.progress() * 100)} %")
    except HttpError as e:
        sys.exit(f"UPLOAD_FAILED: {e.status_code} {e.reason}")

    vid = resp["id"]
    s = resp.get("status", {})
    print(f"UPLOADED: {vid} https://youtube.com/shorts/{vid}")
    print(f"  privacy={s.get('privacyStatus')} publishAt={s.get('publishAt', '-')} upload={s.get('uploadStatus')}")

    if a.playlist:
        from yt_playlist import find_playlist, in_playlist
        for title in a.playlist:
            pl, _ = find_playlist(yt, title)
            if not pl:
                print(f"  PLAYLIST_NOT_FOUND: '{title}'")
            elif not in_playlist(yt, pl, vid):
                yt.playlistItems().insert(part="snippet", body={"snippet": {
                    "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
                print(f"  ADDED to '{title}'")


if __name__ == "__main__":
    main()
