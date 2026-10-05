# Hermes `tui_gateway` wire protocol

Wire protocol of the JSON-RPC server the Hermes desktop app, Ink TUI and web dashboard all speak,
served over WebSocket (and stdio). This is the protocol the Android client implements.

- **Verified against:** Hermes Agent `0.21.5` (release `2026.9.24`, config_version 49) on 2026-10-05,
  via a live disposable gateway (see [Probe setup](#probe-setup)).
- **Coverage rule:** core loop is verified live (verbatim frames below). The **whole** RPC surface is
  documented in [contract-catalog.md](contract-catalog.md) (251 methods, 13 server→client requests,
  75 events) with schemas in [gateway-contract.openrpc.json](gateway-contract.openrpc.json) — both
  derived from `tui_gateway/contracts` in the Hermes repo, the single source of truth. Items not yet
  exercised live are marked *(code-derived)*.
- **Official clients to watch for intended usage:** `apps/desktop` (Electron; gateway client in
  `apps/desktop/src/lib/gateway-*.ts` + `apps/shared/src/json-rpc-gateway*`), the Ink TUI
  (`hermes --tui`, stdio), the dashboard chat tab (same `/api/ws`).

## Transport

- Server: `hermes serve` (headless backend the desktop connects to; default `127.0.0.1:9119`).
  The WebSocket endpoint is **`/api/ws`** on that HTTP server.
- One text frame = one JSON-RPC 2.0 message, newline-delimited JSON semantics identical to the stdio
  transport (same `tui_gateway.server.dispatch` behind both).
- Frame kinds:
  - RPC request → `{"jsonrpc":"2.0","id":<id>,"method":<name>,"params":{...}}`
  - RPC response → `{"jsonrpc":"2.0","result":...,"id":<id>}` or `{"jsonrpc":"2.0","error":{"code","message"},"id":<id>}`
  - **Event** (server→client notification) → `{"jsonrpc":"2.0","method":"event","params":{"type":<name>,"payload":{...},"session_id":...}}`
  - **Server→client request** → `{"jsonrpc":"2.0","id":"srq-N","method":<name>,"params":{...}}` —
    a real request (string `srq-*` id) the client **must answer** with a normal response frame.
- Per-token streaming frames (`message.delta`, `reasoning.delta`, `thinking.delta`) are **coalesced
  server-side** and flushed in batches (~30 fps); any non-streaming frame flushes ahead, so ordering
  is preserved. Clients must tolerate burst delivery. *(code-derived, `tui_gateway/ws.py`)*

## Authentication

Two modes, decided by whether the server has an auth provider configured
(`GET /api/status` → `auth_required`, `auth_providers`, `auth_flows`).

### Ungated (loopback, no auth provider) — verified live

Every request carries the in-process session token:

- REST: header `X-Hermes-Session-Token: <token>`
- WS: query param `?token=<token>` (constant-time compared; missing → `no_credential`, wrong →
  `token_mismatch`, upgrade rejected)

The token comes from env `HERMES_DASHBOARD_SESSION_TOKEN` at server start, else is randomly
generated per process and injected into the SPA (`window.__HERMES_SESSION_TOKEN__`). It dies with
the process. Verified: probe gateway answered `/api/status` and `/api/ws` with the token, rejected
nothing else (no third leg in ungated mode).

### Gated (auth provider configured) — *(code-derived, `hermes_cli/web_server_chat.py::_ws_auth_reason`)*

WS upgrade accepts, in order:

1. `?internal=` — process-lifetime credential for server-spawned WS clients only (never for apps).
2. `?ticket=` — browser-minted, **single-use, 30 s TTL**. Also accepted via WebSocket subprotocol
   `hermes-gateway-ticket.<ticket>` alongside the stable public protocol (the ticket protocol is a
   credential: never reflected back, never logged).
3. `?token=` — a **user session access token** verified against the dashboard auth providers (same
   `verify_session` seam as REST bearer). This is what a remote native client uses after sign-in.

Remote native sign-in (the flow the desktop app uses, and the one a mobile app should use):
RFC 8252 PKCE against the gateway's `/auth/native/*` endpoints —
`GET /auth/native/authorize` (system browser, loopback redirect) → `POST /auth/native/token`
(code + verifier) → `{access_token, refresh_token, expires_at}`; rotate with
`POST /auth/native/refresh`. The gateway brokers the flow to the upstream IDP; capability is
advertised in `GET /api/status` → `auth_flows: ["cookie","native_pkce"]`. REST calls then use
`Authorization: Bearer <access_token>`; the WS upgrade uses `?token=<access_token>`.
Password providers land the browser on the gateway's `/login` form instead (same brokered flow).

## Connection lifecycle

Verified verbatim (probe, 2026-10-05):

1. **Accept → `gateway.ready`** (first frame, always):

   ```json
   {"jsonrpc":"2.0","method":"event","params":{"type":"gateway.ready","payload":{
     "skin":{...},"change_events":true,"heartbeat":true,"replay_epoch":"<epoch>"}}}
   ```

2. **Client MUST then advertise server-request support** — once per connection:

   ```json
   → {"jsonrpc":"2.0","id":"1","method":"client.capabilities","params":{"server_requests":true}}
   ← {"jsonrpc":"2.0","id":"1","result":{"server_requests":[
        "approval","clarify","display.install.sudo","preview.act","preview.read","secret","sudo",
        "terminal.read","tour","vault.code","vault.unlock_prompt","window.read","connection"]}}
   ```

   A WS client that never sends this is treated as pre-feature: **every** server→client request
   fails for it immediately (approvals are withdrawn, not auto-denied). *(Docs + code; the
   capabilities round-trip above is live-verified.)*

3. **Heartbeat**: client sends `gateway.ping`; server answers `{"result":{"ok":true}}` out of band
   (never queued behind a busy dispatch). Official desktop client policy worth mirroring on mobile
   *(code-derived, `apps/desktop/src/lib/gateway-liveness-policy.ts`)*:
   - probe budget 5 s; on window-lifecycle signals (focus/network) probe then force-close on timeout;
   - **while any session reports working, silence is expected** (long tool calls stall the loop):
     defer the first probe timeout, re-probe once, force-close only on a streak. Mobile equivalent:
     don't tear down the socket mid-turn just because the backend went quiet during a tool call.
   - server side: a `send_text` blocked >30 s on backpressure closes with `1011` (`send deadline`);
     fanout overflow closes `1011` (`fanout overflow`) → reconnect and replay.

## Sessions

Two ID spaces — do not conflate:

- **live `session_id`** (e.g. `"6ce03bb8"`) — process-local handle for a session open in this
  gateway process; used by `prompt.submit`, `session.interrupt`, `session.steer`, …
- **`stored_session_id`** (e.g. `"20261005_164743_fa8ac6"`) — durable transcript identity, what
  `session.list` returns and `session.resume` takes.

Verified verbatim round-trips:

```json
→ {"method":"session.create","params":{"title":"probe-core"}}
← {"result":{"session_id":"6ce03bb8","stored_session_id":"20261005_164743_fa8ac6",
   "message_count":0,"messages":[],"info":{"model":"kimi-k3",...}}}
```

`session.create` accepts per-session `model`/`provider` overrides; a pair the provider can't serve
is refused up front with `-32602` and up to five `suggestions` *(docs)*.

```json
→ {"method":"session.list"}
← {"result":{"sessions":[{"id":"20261005_164743_fa8ac6","title":"probe-core",
   "preview":"Reply with exactly: PROBE_OK","started_at":1791211663.5,"message_count":7,
   "source":"desktop"}]}}
```

```json
→ {"method":"session.usage","params":{"session_id":"6ce03bb8"}}
← {"result":{"model":"kimi-k3","input":7151,"output":471,"prompt":42991,"completion":471,
   "total":43462,"calls":3,"context_used":14558,"context_max":1048576,"context_percent":1,
   "cache_hit_pct":83,"avg_latency_s":5.2,...}}
```

```json
→ {"method":"session.history","params":{"session_id":"6ce03bb8"}}
← {"result":{"count":6,"messages":[{"role":"user","text":"Reply with exactly: PROBE_OK",
   "timestamp":1791211663.527,"row_id":1},{"role":"assistant","text":"PROBE_OK\n...",...}]}}
```

Notes:

- `session.status` returns **human-readable prose** (`"Hermes TUI Status\n\nSession ID: …"`):
  fine for a debug screen, wrong for app state — use the structured RPCs. *(verified)*
- `row_id` (durable SQLite row id) is the preferred address for rewind (`truncate_before_row_id`);
  ordinals are the back-compat path. **Row ids are global across sessions** (one `messages`
  table: probe sessions drew 8, 18, 21, 22…), never per-session. A rewind requires explicit
  `confirm_truncate`, and while a turn runs a rewind is refused `4009` (session busy) rather than
  queued — interrupt first, then resubmit. *(verified)*
- History rows are heterogeneous *(verified)*: `role:"tool"` rows carry `text:null` (tool I/O
  lives in events/transcript payloads); an assistant row can be empty when the turn's pre-tool
  content was reasoning-only; mid-turn user injections land with `display_kind:"steer"`.
  `display_kind` / `display_metadata` is the timeline-marker channel.
- Session lifecycle set: `create / resume / activate / active_list / close / delete / archive /
  branch / branch_stored / branch_whole / compress / undo / title / save / set_hidden / info /
  context_breakdown / events.since / events.stats / most_recent / workspace.move / cwd.set /
  control(.read/.update)` — see the catalog.

## Turn lifecycle & streaming events

`prompt.submit` ack, then the turn streams as events. Verified verbatim:

```json
→ {"method":"prompt.submit","params":{"session_id":"6ce03bb8","text":"Reply with exactly: PROBE_OK"}}
← {"result":{"status":"streaming","user_row_id":1}}
```

Observed event order over two turns (probe; event `type` sequence, `sessions.changed` elided):

```text
session.info → message.start → session.title (auto-generated) →
thinking.delta / reasoning.delta (many; model+config dependent) →
message.delta (answer tokens, coalesced) →
session.usage → reasoning.available → message.complete
```

A turn with a tool call inserts `tool.generating → tool.start → tool.complete` before the final
`message.delta` run. Verified verbatim tool frames:

```json
{"type":"tool.start","payload":{"tool_id":"tool_4uxRKfnWYqtVVBLgH42MfiyS","name":"terminal",
 "context":"echo PROBE_TOOL_$((40+2))","args":{"command":"echo PROBE_TOOL_$((40+2))"}}}
{"type":"tool.complete","payload":{"tool_id":"tool_4uxRKfnWYqtVVBLgH42MfiyS","name":"terminal",
 "args":{"command":"echo PROBE_TOOL_$((40+2))"},"duration_s":0.056,
 "result":{"output":"PROBE_TOOL_42","exit_code":0,"error":null}}}
```

`message.complete.payload.text` holds the final assistant text. `thinking.delta` vs
`reasoning.delta`: both stream model reasoning (names are config/provider-dependent; the probe ran
`reasoning_effort: max`, hence hundreds of deltas). *(verified; semantic split between the two
delta types still to be pinned down — treat both as collapsible "thinking" UI.)*

## Server→client requests

Approvals, clarify questions, sudo/secret prompts, vault unlocks, connection cards and the desktop
read/act bridges are **requests from the server bearing a string id** — answer with a response
frame carrying the same id:

```text
← {"jsonrpc":"2.0","id":"srq-7","method":"approval","params":{"session_id":"…","request_id":"…",
   "command":"rm -rf build","description":"…"}}
→ {"jsonrpc":"2.0","id":"srq-7","result":{"choice":"once"}}
```

Result shapes: `approval → {choice}`; `clarify → {answers}` keyed by question id (`{}` cancels,
`null` skips; `clarify.lock` locks one answer early); `sudo`, `secret`, `vault.code`,
`vault.unlock_prompt → {value}`; `connection → {settled_by, targets}`; `terminal.read`,
`window.read`, `preview.act`, `tour → {value}` (JSON text). Answer with JSON-RPC error `-32601`
for methods the client doesn't implement so the agent fails fast instead of waiting out the
timeout. When the server withdraws a question (timeout, interrupt, answered from another surface)
it emits `request.cancel {id, method, reason}`. *(Docs, programmatic-integration page — the
`approval` flow itself is verified in the probe captures of later probes; catalog lists 13 request
methods.)*

## Reconnect & resume

- `session.resume` / `session.activate` results carry `inflight` (the still-running or retained
  failed turn: `user`, partial `assistant`, `streaming`, mid-turn `corrections`, error fields, and
  `display_kind`/`display_metadata` for gateway-originated turns) and `open_requests` (the
  still-open server→client frames, re-answerable). Rebuild UI from those, then re-subscribe to live
  events. *(docs + `contracts/sessions.py::InflightTurn`)*
- `session.events.since` replays missed events; `gateway.ready.payload.replay_epoch` changes on
  backend restart → drop per-session watermarks.
- Attaching a second client to a live session adds a subscriber (streaming goes to all attached
  clients; disconnecting one doesn't end the session). Submit exclusivity and busy-input policy
  still apply per session. *(docs)*
- Busy-input policy **(verified)**: an ordinary `prompt.submit` during a running turn is queued —
  ack `{"result":{"status":"queued"}}` — and becomes the next turn. Race caveat: submitting while
  the first turn is still *starting* (before any delta) can **supersede** it: the first turn ends
  immediately with a placeholder `message.complete` (`"Stopped waiting for another Hermes process
  on this session. Your message was not processed."`, zero usage, `status:"interrupted"`) and the
  queued prompt takes over (the auto-title is then derived from the winning prompt). A rewind
  submit during a running turn is refused `4009` instead — interrupt first, then resubmit.
- `session.interrupt` answers `{"result":{"status":"interrupted"}}` **(verified)**.
- `session.steer` answers `{"result":{"status":"queued","text":...}}`; the text is delivered at the
  next tool boundary (the model's continuation honors it) and **persists in history as a
  `role:"user"` row with `display_kind:"steer"`** — render it as an inline marker, not a user
  bubble. **(verified end-to-end)**

## Errors

Standard JSON-RPC: `-32700` parse error, `-32601` method not found, `-32602` invalid params,
`-32603` internal. Gateway-specific codes (all verified live unless noted):

| Code | Meaning | Verified case |
|---|---|---|
| `-32601` | unknown method | `no.such.method`, `session.frobnicate` — message adds *"client and backend out of sync, run `hermes update`"* |
| `-32602` | invalid params | `session.create` with `model:"gpt-5.5", provider:"anthropic"` — message lists closest models (`error.data.suggestions`) |
| `4000` | params contract violation | `session.create` with unknown key → `bogus_key: Extra inputs are not permitted` + field path |
| `4001` | session not found | `session.usage` with a bad `session_id` |
| `4007` | session not found (resume path) | `session.resume` with a bad stored id — **different code per method** |
| `4009` | session busy | rewind `prompt.submit` while a turn runs |
| `4018` | rewind target not in history | stale `truncate_before_row_id` — `error.data` carries `user_turn_count`, `ordinal`, `segment_ordinal`, `prefix_user_count` |
| `4029` | truncation without `confirm_truncate` | `prompt.submit` with `truncate_before_user_ordinal` only |
| `4004` | invalid truncate intent / boolean as target | *(docs-derived)* |

Caveat: params validation is Pydantic-**coercive**, not strict — `session.create {title: 42}`
succeeded (coerced to `"42"`). Don't rely on the server to reject wrong-but-coercible types.
*(verified)*

## Full surface

- [contract-catalog.md](contract-catalog.md) — all 251 methods / 13 server requests / 75 events
  with one-line docs, grouped by namespace.
- [gateway-contract.openrpc.json](gateway-contract.openrpc.json) — official OpenRPC render of the
  contracts (schemas), vendored from `apps/shared/src/gateway-contract.openrpc.json` at Hermes
  0.21.5 (MIT © Nous Research). Regenerate both:
  `<hermes-repo>/scripts/run-in-hermes-env python3 scripts/probe/gen_catalog.py <hermes-repo>`
  (catalog) and `<hermes-repo>/scripts/gen_gateway_contracts.py` (OpenRPC/TS, official).

## Probe setup

Disposable gateway used for live verification (never touches the main Hermes instance):

```bash
# one-time: fresh home with sanitized config (no MCP servers, telemetry off)
mkdir -p .probe/home && cp ~/.hermes/.env .probe/home/.env   # provider keys only
# config.yaml copied minus mcp_servers, telemetry disabled; random token:
openssl rand -hex 24 > .probe/token

# run
HERMES_HOME=$PWD/.probe/home HERMES_DASHBOARD_SESSION_TOKEN=$(cat .probe/token) \
  hermes serve --host 127.0.0.1 --port 9877 --skip-build
```

Probe scripts: `scripts/probe/gw.py` (WS JSON-RPC client + capture), `p01_core_loop.py` (this
document's core-loop round-trips). Raw frame captures stay local (`.probe/captures/`, gitignored).

## Verification log

| Date | Hermes | What was verified live |
|---|---|---|
| 2026-10-05 | 0.21.5 | Transport + ungated auth; `gateway.ready`; `client.capabilities`; `session.create/list/usage/history/status`; `prompt.submit` ×2 (plain + terminal tool); full turn event sequence; `tool.start/complete` verbatim. |
| 2026-10-05 | 0.21.5 | `session.steer` (queued → delivered at tool boundary → persisted as `display_kind:"steer"`); `session.interrupt`; busy queueing + turn-supersede race; errors `-32601/-32602/4000/4001/4007/4009/4018/4029`; params coercion caveat; global `row_id` space. |
