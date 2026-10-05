# Hermes Android Client — agent conventions

Native Android client for [Hermes Agent](https://github.com/NousResearch/hermes-agent), driving the agent through its `tui_gateway` JSON-RPC protocol over WebSocket.

## Protocol: use the purpose-built route for every feature

`docs/gateway-api.md` documents the **whole** RPC surface — not only the routes the app uses today.
Every claim in it is verified against a live disposable gateway, or explicitly marked as code-derived.
Keep it accurate whenever the data layer changes.

Before implementing any feature:

1. Look it up in `docs/gateway-api.md`.
2. Check how the official Hermes clients (desktop app, Ink TUI, web dashboard) do the same thing —
   they define intended usage.
3. Only then write code. Never shoehorn a feature into a route the data layer already happens to implement.

## Public repo hygiene

This repo is public from day one. Never commit anything machine- or user-specific:

- `local.properties`, `AGENTS.local.md`, `google-services.json`, `scripts/*.local.*` are gitignored — keep them that way.
- Commit messages: no personal paths, hosts, or setup references.
- Docs and scripts must work from a clean clone with just an Android SDK installed.

Local setup specifics live in `AGENTS.local.md` (gitignored).

## Testing policy

No unit tests. Everything is verified end-to-end on the Android emulator:
Compose UI tests via `./gradlew connectedAndroidTest`, plus adb-driven checks (screencap, uiautomator).
The emulator reaches a gateway running on the host machine via `10.0.2.2`.
