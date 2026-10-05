# Hermes Android Client — agent conventions

Native Android client for [Hermes Agent](https://github.com/NousResearch/hermes-agent), talking to the
`tui_gateway` JSON-RPC protocol over WebSocket (`/api/ws`).

## Stack

Kotlin, Jetpack Compose, Hilt (KSP), OkHttp, kotlinx.serialization. Release APK via `./gradlew :app:assembleRelease`.

## The protocol doc is the contract

`docs/gateway-api.md` is the wire-protocol reference. It covers the **whole** RPC surface, not just the
routes the app currently uses, and every claim in it is verified against a live disposable gateway (or
marked as code-derived, never guessed). Keep it accurate whenever the data layer changes.

### Golden rule: use the purpose-built route for every feature

Before implementing any feature, pick the RPC the Hermes developers designed for it:

1. Look it up in `docs/gateway-api.md` (full catalog, not only familiar routes).
2. Check what the **official clients** do for the same feature — the desktop app
   (`apps/desktop` in the Hermes repo), the Ink TUI, and the web dashboard. They define intended usage.
3. Only then write code. Never shoehorn a feature into a route that happens to be already implemented
   in the data layer.

(Skipped during the Kimi client project — partial docs led to reusing known routes where better,
purpose-built ones existed. Not making that mistake again.)

## Git hygiene (repo is public from day one)

Nothing machine- or user-specific ever lands in git:

- `local.properties` (SDK path), `AGENTS.local.md` (local paths, publish targets, device names),
  `google-services.json`, `scripts/*.local.*` are gitignored — keep them that way.
- Commit messages: no personal paths, hosts, or setup references.
- Docs and scripts must work from a clean clone on any machine with an Android SDK.

Local setup specifics live in `AGENTS.local.md` (gitignored).

## Testing

- Unit tests: `./gradlew test`.
- End-to-end: local emulator (headless) — Compose UI tests via `./gradlew connectedAndroidTest`,
  plus adb-driven verification (screencap / uiautomator). The emulator reaches a gateway running on
  the host via `10.0.2.2`.
