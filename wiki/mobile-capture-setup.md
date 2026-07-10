# Mobile capture — Android → mewwiki inbox (B6)

Ideas die between desk sessions. This pipe gets a voice note or quick text from your Android phone into `mewwiki/_inbox/` with zero vault changes on the phone side.

## How it works

```
Android note/dictation → synced folder → (mew wiki sync sweeps it) → mewwiki/_inbox/ → "process the inbox"
```

The sweep runs automatically at every `mew wiki sync` (and therefore at every wrap). Only `.txt`/`.md` files move; they get date-prefixed names; originals are deleted after copy. Inbox discipline is unchanged — nothing auto-processes until you say "process the inbox".

## Setup (once, ~15 min) — Syncthing route (recommended)

1. **Laptop**: `brew install syncthing && brew services start syncthing` → web UI at 127.0.0.1:8384 → add folder `~/Sync/mew-inbox`.
2. **Phone**: install Syncthing-Fork (F-Droid or Play Store) → pair with the laptop (QR) → share a folder, e.g. `Documents/mew-inbox`, with the laptop folder.
3. **Capture**: any notes app that saves plain text into that folder. Two good routes:
   - Markor (F-Droid): point its notebook at `mew-inbox`, use its QuickNote + share-target. Voice: keyboard dictation into Markor.
   - Or a home-screen widget → new file in folder.
4. Done — next `mew wiki sync` sweeps anything there.

Peer-to-peer, no cloud, works offline (syncs when both devices are on the same network or via relay).

## Alternative — Google Drive route (simpler, cloud)

1. Phone: any note app that saves to Drive, into a folder `mew-inbox`.
2. Laptop: Google Drive for desktop syncing that folder locally.
3. Point the vault at it: `echo "$HOME/Google Drive/mew-inbox" > mewvault/.inbox-drop` (or set `MEW_INBOX_DROP`).

## Config

Drop folder resolution order: `$MEW_INBOX_DROP` env → `mewvault/.inbox-drop` pointer file → default `~/Sync/mew-inbox`.

## Voice specifically

Gboard/keyboard dictation into the notes app is the lowest-friction route and needs nothing extra. If you want true one-tap voice capture, Tasker (+AutoVoice) can record → transcribe → write a file into the synced folder — build only if dictation friction actually bothers you.
