# HistoryABC Tools - upload script

Complete, working upload script used by the channel owner of HistoryABC (@History-ABC) for their own channel only.

- `yt_auth.py` - OAuth 2.0 installed-app login (Desktop client). The token is stored locally only.
- `yt_upload.py` - uploads one of the owner's own Shorts with `videos.insert` (resumable), private or scheduled with `status.publishAt`. It never uploads as public.

Usage:
```
python yt_auth.py
python yt_upload.py short.mp4 --title "Title #history #ww2 #shorts" --description "..." --publish-at "2026-12-01 13:00" --playlist "Secret WWII Weapons & Inventions"
```
Requires `google-api-python-client` and `google-auth-oauthlib`, and an OAuth client file `client_secret.json` next to the scripts (not published).

Privacy policy: https://korki00.github.io/HistoryABC/privacy.html
