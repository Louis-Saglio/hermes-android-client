# tui_gateway contract catalog

Extracted from `tui_gateway/contracts` (doc strings) — 251 RPC methods, 13 server→client requests, 75 events. Param/result/payload schemas: see `gateway-contract.openrpc.json` (same source, official generator).
Regenerate: `<hermes-repo>/scripts/run-in-hermes-env python3 scripts/probe/gen_catalog.py <hermes-repo>`

## RPC methods (251)


### `agents.*`

- `agents.list` — Registry-wide background process summary for ``/agents``.

### `approval.*`

- `approval.pending` — Replay the approvals still waiting on this session (reconnect / polling).
- `approval.received` — Tell the backend the card is on screen, so its timeout clock starts.
- `approval.respond` — Deliver the user's decision on a dangerous command (falls back to durable identity on a stale sid).

### `billing.*`

- `billing.auto_reload` — Enable/disable auto top-up with its threshold and reload amount (billing:manage).
- `billing.charge` — Start a one-off top-up charge (billing:manage, idempotent).
- `billing.charge_status` — Poll one charge by id.
- `billing.state` — Read-only billing view (no scope); the Nous free tier is answered locally without a portal call.
- `billing.step_up` — Run the billing:manage device flow; the URL/code arrive via billing.step_up.verification.

### `bot_relay.*`

- `bot_relay.deliver` — Deliver a relayed DM into a Bot Chat on this gateway and return the one-turn reply (blocking).
- `bot_relay.outbox.drain` — Atomically claim every pending cross-connection envelope queued on this gateway.
- `bot_relay.reply` — Write a relayed reply and/or typed error for an envelope so the sender-side waiter resolves.
- `bot_relay.roster.sync` — Replace this gateway's view of agents on other connections; answers the accepted row count.

### `browser.*`

- `browser.controller.detach` — Hard-detach only the controller owned by this authenticated transport.
- `browser.controller.heartbeat` — Acknowledge a heartbeat only for this transport's own attached controller.
- `browser.controller.register` — Attach this connection as the browser controller for one session; fails closed (4403).
- `browser.controller.result` — Deliver one command result to the broker; accepted is false for unknown or settled command ids.
- `browser.manage` — Inspect, attach to, or drop the CDP browser the tools use, or switch Browser Use mode (``use``, applies to new sessions); ``messages`` narrate a connect.

### `clarify.*`

- `clarify.lock` — Lock one answer of a batch clarify request (editable until every question is locked).

### `cli.*`

- `cli.exec` — Run ``hermes <argv>`` non-interactively and capture its output; ``blocked`` explains a refusal.

### `client.*`

- `client.capabilities` — What the calling client handles, sent once per connection (after gateway.ready); returns the server→client request methods this backend may send.

### `clipboard.*`

- `clipboard.paste` — Save the host clipboard image into the session and queue it for the next turn.

### `command.*`

- `command.dispatch` — Run a quick/plugin/bundle/skill/built-in slash command and answer a structured directive.
- `command.resolve` — Canonical registry command for a name or alias.

### `commands.*`

- `commands.catalog` — Categorized slash metadata (registry, quick, plugin, skill) for completion menus.

### `complete.*`

- `complete.path` — Path / @-reference completions for the composer (files, folders, profiles, plugin providers).
- `complete.slash` — Ranked slash-command / skill completions for a ``/`` token.

### `config.*`

- `config.get` — Read one normalised config value (or the whole effective config) the way the UIs render it.
- `config.set` — Change one config key (persisted or session-scoped) and read back the normalised value.
- `config.show` — Masked, display-ready config summary (model / agent / environment rows).

### `connection.*`

- `connection.respond` — Per-target outcomes from the card, and an optional Continue.

### `connectors.*`

- `connectors.accounts` — The scoped member's hosted connector accounts, optionally filtered by connector slug.
- `connectors.accounts.remove` — Remove one hosted connector account owned by the scoped member.
- `connectors.catalog` — The hosted connector catalog available to the scoped member.
- `connectors.connect` — Start or re-initiate authorization for named connectors on a session or account operation.
- `connectors.list` — Connector catalog + connection state for one session or profile account owner.
- `connectors.operation.status` — The current snapshot of one open session or account operation.
- `connectors.operation.wake` — The browser leg came back (hermes://connections/done): read the accounts now, not at the next tick.
- `connectors.policy.get` — Policy layers for the scoped member, from organization to member scope.
- `connectors.policy.set` — Apply one scoped member connector or tool-list policy change.
- `connectors.tools` — The scoped profile's cached or current tool list for one connector.

### `cron.*`

- `cron.manage` — List/add/remove/pause/resume cron jobs in the (optionally profile-scoped) cron store.

### `delegation.*`

- `delegation.pause` — Block/unblock NEW spawns globally (active children keep running); returns the new state.
- `delegation.status` — Running subagent tree plus the spawn pause flag and limits.

### `diagnostics.*`

- `diagnostics.share_nous` — Upload a force-redacted debug bundle to Nous-internal diagnostics storage.

### `display.*`

- `display.install` — Run the distro package install on the gateway host; progress streams as display.install.log/.done.
- `display.lease.acquire` — Take over: the human named by a viewer id this connection minted controls the screen.
- `display.lease.release` — Hand back. Without a viewer id the release is refused while a human holds unless force.
- `display.observe` — Mint a single-use ticket for /api/display/ws and the server-minted viewer id for this connection.
- `display.start` — Start this profile's Xvnc + Xfce (idempotent); blocks until the display is published.
- `display.status` — Runtime + lease snapshot for this profile's screen.
- `display.stop` — Stop the screen. Refused (5300, code viewer_mismatch) while a human holds unless force.
- `display.switchSandboxImage` — Decide the pending default sandbox image switch for this profile; refused when none is pending.
- `display.thumbnail` — One JPEG grab of the bot's screen; read-only, never changes the lease.

### `file.*`

- `file.attach` — Stage a non-image file into the session workspace and hand back its @file: ref.

### `free_tier.*`

- `free_tier.ack_notice` — Mark the one-time availability notice as shown on the free-tier identity.
- `free_tier.provision` — Explicit retry of the free-tier identity mint when the boot bootstrap could not create it.
- `free_tier.status` — Pure read of the focused profile's free-tier identity state (no network, no side effects).

### `gateway.*`

- `gateway.capabilities` — What THIS build enforces (a client withholds a feature unless advertised).

### `groups.*`

- `groups.approve` — Resolve one exact pending approval raised by a local or peer room member.
- `groups.capabilities` — Describe the hosted-room protocol implemented by this gateway.
- `groups.create` — Create a hosted room idempotently; authority is this gateway's stable install identity.
- `groups.demote` — Fence this gateway's stale room authority against a proven newer epoch.
- `groups.disband` — Permanently tombstone a hosted room id after stopping its work and revoking peer routes.
- `groups.list` — List rooms hosted by this gateway, most recently changed first.
- `groups.log` — A monotonic room-log delta after since_seq, bounded by count and page bytes.
- `groups.peer.invite` — Mint one target-issued room/profile grant for a prospective room home.
- `groups.peer.register` — Register and probe one scoped peer route on the room home.
- `groups.peer.revoke` — Revoke one target-issued grant using its exact profile scope.
- `groups.promote` — Continue a replicated room on this gateway at epoch + 1; requires confirm=true.
- `groups.rename` — Rename one hosted room atomically with its replay event.
- `groups.replica_state` — The local replica's coverage and authority lineage for one room.
- `groups.replicate` — Persist one authority-stamped replay page into the local replica store; idempotent.
- `groups.retry` — Retry one indeterminate room task after explicit user confirmation.
- `groups.send` — Append one inert message.user event idempotently; the actor is server-owned.
- `groups.state` — One hosted room's replay cursor and fenced authority state, plus live driver status.
- `groups.stop` — Durably cancel queued or running work for one hosted room.

### `handoff.*`

- `handoff.fail` — Fail a not-yet-claimed handoff (client poll timeout); CAS against the watcher.
- `handoff.request` — Queue a handoff to a messaging platform's home channel; the gateway watcher claims it.
- `handoff.state` — Poll the handoff row for this session.

### `i18n.*`

- `i18n.catalog` — Pack + overlay messages for one language and surface; the renderer merges them over its bundled catalog.
- `i18n.languages` — Every language some layer supplies (bundled ∪ user overlay ∪ plugin packs), en first.

### `image.*`

- `image.attach` — Queue a gateway-visible image file for the next turn.
- `image.attach_bytes` — Queue an image uploaded as base64 (remote client); reply mirrors image.attach.
- `image.detach` — Drop a queued image before the turn is sent.
- `image.generate` — Generate an image through the tool's provider dispatcher and hand the renderer a data URL.

### `input.*`

- `input.detect_drop` — Recognise a terminal file drop pasted into the composer and turn it into an attachment.

### `insights.*`

- `insights.get` — Session/message counts over the last ``days`` for the (optionally scoped) profile store.

### `learning.*`

- `learning.delete` — Archive a skill (restorable via curator) or remove a memory chunk.
- `learning.detail` — Node content (SKILL.md or memory chunk) for an edit prefill.
- `learning.edit` — Rewrite a node's content (SKILL.md or memory chunk).
- `learning.frames` — Pre-render the /journey timeline (frames + legend/summary) so the TUI walks it locally.

### `llm.*`

- `llm.oneshot` — Stateless one-shot LLM completion (titles, ideas) on the session's or the task backend.

### `mcp.*`

- `mcp.catalog` — Curated MCP presets with per-profile installed/enabled state and the env keys each needs.
- `mcp.servers.add` — Add a server to the profile's config from a catalog preset and/or an explicit config.
- `mcp.servers.list` — Configured MCP servers for the (scoped) profile, secrets redacted to env-key names.
- `mcp.servers.oauth.callback` — Relay a client-captured redirect into a client_redirect_uri flow.
- `mcp.servers.oauth.cancel` — Cancel a flow owned by the resolved profile, waking its callback worker.
- `mcp.servers.oauth.poll` — Poll a flow; approved persists tokens for the profile and returns the probed tools.
- `mcp.servers.oauth.start` — Begin a PKCE OAuth flow; the client opens auth_url and polls mcp.servers.oauth.poll.
- `mcp.servers.remove` — Drop a server from the profile's config.yaml.
- `mcp.servers.set_api_key` — Store a credential in the profile's .env and reference it from the server config (header or env).
- `mcp.servers.status` — Cached runtime state per configured server; never connects, probes, or starts auth.
- `mcp.servers.test` — Connect, list tools, disconnect — an OAuth server with no token on disk is reported as not ok.

### `message.*`

- `message.react` — Set/clear one author's emoji reaction on a message; returns the row's full reaction list.

### `model.*`

- `model.disconnect` — Remove every credential (env keys and OAuth state) for a provider.
- `model.options` — Provider/model inventory for the picker, layered over the session's live provider when given.
- `model.save_key` — Save an API key for a provider and return its refreshed inventory row.

### `onboarding.*`

- `onboarding.ensure_setup_profile` — Create-or-read the backend-owned setup profile; the backend picks the name and finds it by role.
- `onboarding.reset_setup_profile` — Restore the setup profile to its created state in place (soul, memories, skills, sessions).

### `paste.*`

- `paste.collapse` — Spill a large paste to a file and hand back the inline placeholder.

### `pdf.*`

- `pdf.attach` — Render a PDF's pages to PNG and queue them as images for the next turn.

### `pet.*`

- `pet.cancel` — Stop an in-flight pet generate/hatch by token (idempotent).
- `pet.cells` — Half-block cell frames (or a kitty placement) for one pet state.
- `pet.disable` — Turn the pet display off from the desktop picker.
- `pet.export` — Export an installed pet as a re-importable .zip.
- `pet.gallery` — Petdex gallery + local install state (installed-only offline); localOnly skips the remote manifest.
- `pet.generate` — Candidate base looks for a new pet (draft step); drafts also stream via pet.generate.progress.
- `pet.generate.status` — Whether pet generation is possible (a reference-capable image backend) and which providers.
- `pet.hatch` — Turn a base draft into a full spritesheet pet; progress streams via pet.hatch.progress.
- `pet.info` — Active pet for sprite renderers: spritesheet (base64) + frame geometry + state-row taxonomy.
- `pet.info.meta` — Cheap active-pet metadata used to avoid full payload refreshes.
- `pet.remove` — Uninstall a pet (delete its directory); if it was active, turn the display off.
- `pet.rename` — Rename a pet's display name + realign its slug/dir; follows the active slug in config.
- `pet.scale` — Persist display.pet.scale (clamped to engine bounds) from the desktop slider.
- `pet.select` — Adopt a pet: install (if needed) + activate; writes display.pet.* to config.
- `pet.thumb` — Idle-frame PNG data URI for the picker (desktop CSP breaks CDN <img>).

### `ping.*`

- `ping` — Cheapest liveness probe; answered on the WS reader thread even while every agent is mid-turn.

### `plugins.*`

- `plugins.list` — Loaded plugin manager entries (legacy flat view); the Plugins Hub uses plugins.manage list.
- `plugins.manage` — Plugins Hub backend: list installed plugins, toggle, git-install, re-pin a catalog install, or remove a user install.

### `preview.*`

- `preview.restart` — Spawn a hidden agent that brings the desktop preview's dev server back up.

### `process.*`

- `process.kill` — Kill one background process the caller's session owns and return its output snapshot.
- `process.list` — Background processes owned by the caller's session (desktop status stack poll).
- `process.stop` — Kill every background process in the registry (``/stop``), answering the count killed.

### `profiles.*`

- `profiles.configure` — Editor Save: apply any subset of a profile's sections and report each one.
- `profiles.create` — Create a profile (ws twin of POST /api/profiles), mirroring launch credentials by default.
- `profiles.describe` — Everything the profile editor shows: soul, model pin, skills, toolsets, MCP servers.
- `profiles.get_asset` — A profile asset as a data URL.
- `profiles.list` — Roster of profiles with previews so a client paints without N follow-up calls.
- `profiles.remember_onboarding` — Write the onboarding facts into the default profile's user memory and confirm they landed.
- `profiles.set_asset` — Store or clear a profile asset (avatar) atomically.

### `project.*`

- `project.facts` — Structured project facts for a cwd so UIs don't re-sniff the workspace.

### `projects.*`

- `projects.add_folder` — Attach a folder to a project (optionally as its primary path).
- `projects.archive` — Archive (or with ``restore`` un-archive) a project; answers the full listing.
- `projects.create` — Create a project from a name + folders; duplicate primary paths are refused (5063).
- `projects.delete` — Delete a project and its folders; answers the full listing.
- `projects.discover_repos` — Repos for the desktop overview: scanned-from-disk (cached) ∪ session-derived.
- `projects.for_cwd` — Which project (if any) owns a directory, plus the resolved cwd and its git branch.
- `projects.get` — One stored project with its folders.
- `projects.list` — Every project of the profile (archived included) plus which one is active.
- `projects.project_sessions` — Fully hydrated lanes for one project, from the same grouping as projects.tree.
- `projects.record_repos` — Persist repo roots found by the client's (desktop-side) scan; return the merged list.
- `projects.remove_folder` — Detach a folder from a project.
- `projects.set_active` — Switch (or clear) the active project for the profile.
- `projects.set_primary` — Make one attached folder the project's primary path.
- `projects.tree` — Project → repo → lane overview with counts and a few preview sessions per project.
- `projects.update` — Patch a project's display fields; answers the refreshed project.

### `prompt.*`

- `prompt.background` — Run a task on a fresh agent in the background; the answer arrives as background.complete.
- `prompt.btw` — Side question over a snapshot of the live conversation; the answer arrives as btw.complete.
- `prompt.submit` — Send a user turn to a live session; busy sessions queue / steer / redirect instead of refusing.

### `reload.*`

- `reload.env` — Re-read ~/.hermes/.env (CLI /reload parity); built agents keep their pool until /new.
- `reload.mcp` — Tear down and rediscover MCP servers for every live session (prompt cache is invalidated).

### `request.*`

- `request.answer` — Answer an open server→client request from a client that never received the frame.

### `rollback.*`

- `rollback.diff` — Diff between a checkpoint and the working tree, with an ANSI rendering sized to the TUI.
- `rollback.list` — Checkpoints for the session's cwd; ``enabled: false`` when checkpointing is off.
- `rollback.restore` — Restore the working tree (or one file) to a checkpoint by hash or 1-based index.

### `session.*`

- `session.activate` — Attach the frontend to a live session without closing the previously focused one.
- `session.active_list` — Live sessions in this process, insertion order (not a DB browser).
- `session.archive` — Set/clear archived (soft-hide, messages kept) on a session + lineage; Desktop PATCH parity.
- `session.branch` — Fork a live session into a new stored child that shares the parent's history so far.
- `session.branch_stored` — Whole-session branch of a stored parent: the owning backend reads and copies the transcript, which never crosses the wire (a separate method so an older gateway fails loudly, not with an empty branch).
- `session.branch_whole` — session.branch of the whole history without echoing the copied transcript back.
- `session.close` — Tear down a live session (its stored row stays resumable).
- `session.compress` — Manual /compress of an idle session, optionally focused on a topic.
- `session.context_breakdown` — Cursor-style split of the context window by category.
- `session.control` — Run one allowlisted goal / loop / subgoal / heartbeat action and return the exact resulting snapshot.
- `session.control.read` — Stable, allowlisted snapshot of one live session's goal / loop / heartbeat state.
- `session.create` — Mint a live session (agent builds after the reply); a DB row appears on the first prompt unless seeded.
- `session.cwd.set` — Change a live, idle session's working directory.
- `session.delete` — Delete a stored session + transcripts; refused while it is live here.
- `session.events.since` — Replay events after a seq watermark on WS reconnect; truncated means refetch state.
- `session.events.stats` — Replay-buffer occupancy telemetry (ops/debug).
- `session.foreign.import` — Import a foreign session into this profile's history (idempotent per origin).
- `session.foreign.list` — One page of Claude Code / Codex sessions found on the serving backend.
- `session.foreign.preview` — Preview a foreign session's tail before importing it.
- `session.history` — The durable display transcript (ancestors included, row ids attached).
- `session.interrupt` — Stop the running turn (and streaming TTS); retires the crash-recovery marker.
- `session.list` — Human-facing stored sessions, most recent first (sub-agent / kanban sources denied).
- `session.most_recent` — Most recent human-facing session; errors fold into a null session_id.
- `session.redirect` — Redirect the active turn (queued for the next turn while the agent is still building).
- `session.resume` — Attach to a stored session: reuse it if live here, else lazy / deferred / cold / eager rebuild.
- `session.save` — Export the transcript to ~/.hermes/sessions/saved (classic /save).
- `session.set_hidden` — Set/clear hidden (out of the default list, still resumable by its owner) on a session + lineage.
- `session.status` — Rendered /status text for the session.
- `session.steer` — Inject text into the next tool result without interrupting the turn.
- `session.title` — Read or set a live session's title; a title set before the row exists is queued.
- `session.undo` — Drop the last user turn (and everything after it) from an idle session.
- `session.usage` — Token / context / cost counters for the session (+ Nous credit lines when available).
- `session.workspace.move` — Re-home a stored session's workspace; git identity is replaced and a live agent follows.

### `setup.*`

- `setup.runtime_check` — Strict provider check through the same runtime resolution the agent uses on session creation.
- `setup.status` — Loose provider check: is ANY provider auth state discoverable for the (launch or named) profile.

### `shared_metrics.*`

- `shared_metrics.desktop_daily` — Record one finished Desktop day (mode use + button presses); recorded=false keeps it for a retry.
- `shared_metrics.desktop_dislike` — Count one Desktop dislike signal (fire-and-forget; capped per signal per day; a no-op unless on).
- `shared_metrics.desktop_feature_use` — Count one Desktop area used today (fire-and-forget; once per area per UTC day; a no-op unless on).
- `shared_metrics.desktop_friction` — Count one Desktop friction event (fire-and-forget; capped per day; a no-op unless on).
- `shared_metrics.desktop_onboarding` — Count one Desktop first-run step transition (fire-and-forget; once per step+event; a no-op unless on).
- `shared_metrics.set` — Write both shared-metrics opt-ins at once (send requires collection) and reconcile consent windows.
- `shared_metrics.slash_command` — Count one user-typed slash command (fire-and-forget; a no-op unless shared metrics are on).
- `shared_metrics.startup_latency` — Record one client launch-to-ready latency (fire-and-forget; a no-op unless shared metrics are on).
- `shared_metrics.status` — Pure read of the focused profile's shared-metrics opt-ins (collection, upload, answered).
- `shared_metrics.update_run` — Count one Desktop packaged self-update outcome (fire-and-forget; a no-op unless shared metrics are on).

### `shell.*`

- `shell.exec` — Run a safe (non-dangerous) shell command captured for ``!cmd`` / inline substitution.

### `skills.*`

- `skills.manage` — Skills hub backend: list the profile's skills or search / browse / inspect / install from the hub.
- `skills.reload` — Re-scan skill dirs; the pre-rendered ``output`` is what /reload-skills prints.

### `slash.*`

- `slash.exec` — Execute a slash command against the session's slash worker (or a live/plugin shortcut).

### `spawn_tree.*`

- `spawn_tree.list` — Saved spawn-tree snapshots, newest first.
- `spawn_tree.load` — Read one saved spawn-tree snapshot (path must be under the spawn-trees root).
- `spawn_tree.save` — Persist a finished delegation tree snapshot under the session's spawn-trees dir.

### `subagent.*`

- `subagent.interrupt` — Hard-interrupt one owned child; ``found`` is false when it already finished.
- `subagent.list` — Live children owned by this session (other sessions' children never leak).
- `subagent.steer` — Queue steering text into a live delegated child owned by this session.
- `subagent.tail` — Last 16KB of an owned child's live transcript.

### `subscription.*`

- `subscription.change` — Schedule a downgrade / same-price change or a period-end cancellation.
- `subscription.preview` — Chargeless quote of what a plan change would do (billing:manage).
- `subscription.resume` — Clear a scheduled downgrade / cancellation (re-enables recurring spend).
- `subscription.state` — Current plan, tier catalog and usage for the picker; fail-open when logged out.
- `subscription.upgrade` — Prorate, charge and flip the plan (billing:manage, idempotent).

### `system.*`

- `system.battery` — Host battery for the status bar; always resolves, ``available: false`` when unreadable.

### `terminal.*`

- `terminal.resize` — Record the client's column width for server-side rendering.

### `tools.*`

- `tools.configure` — Persist a toolset / MCP enable-disable change and rebuild the session agent so it takes effect now.
- `tools.list` — Every toolset with its resolved tool names, flagged against the session's (or config's) enabled set.
- `tools.show` — The /tools listing grouped by toolset, including tools deferred behind the tool_search bridge.

### `toolsets.*`

- `toolsets.list` — Toolset summaries (no tool names) for the desktop Toolsets tab.

### `usage.*`

- `usage.bars` — Two-bar dollar usage view shared by /usage, /topup and /subscription; fail-open to unavailable.

### `vault.*`

- `vault.add` — Add a login / payment / address item to the local vault.
- `vault.list` — Metadata-only listing across the local vault and every unlocked password manager.
- `vault.lock` — Forget a manager's session token (every manager when no name is given).
- `vault.remove` — Remove a local vault item by id.
- `vault.source.set` — Enable or disable an external password manager (disabling also locks it).
- `vault.sources` — Status of every login source (local vault + detected password managers).
- `vault.unlock` — Unlock a password manager for this session with its master password.

### `verification.*`

- `verification.status` — Best known verification evidence for a cwd/session; read-only, never runs checks.

### `voice.*`

- `voice.record` — VAD-bounded push-to-talk; the transcript arrives as a voice.transcript event.
- `voice.toggle` — /voice parity: report, flip voice mode on/off, or toggle speech output.
- `voice.tts` — Speak text through the backend TTS engine (barge-in aware).

### `wake.*`

- `wake.feed` — Push client-captured PCM into the armed detector (mic-less remote backends).
- `wake.pause` — Release the mic (e.g. while the desktop's browser captures audio).
- `wake.resume` — Reclaim the mic after a pause; no-op if the listener isn't armed.
- `wake.start` — Arm the wake-word listener for the calling surface; refusals explain why.
- `wake.status` — Everything a client needs to draw the wake-word state and decide whether to (re)arm.
- `wake.stop` — Stop this surface's listener; persist also writes wake_word.enabled: false.

## Server→client requests (13)


### `approval.*`

- `approval` — A dangerous command awaits the user's decision.

### `clarify.*`

- `clarify` — The clarify tool: ask the user 1-5 questions.

### `display.*`

- `display.install.sudo` — Masked sudo password for the Bot Screen package install; app-level (empty session).

### `preview.*`

- `preview.act` — Click / type / scroll / annotate inside the in-app browser preview.
- `preview.read` — Read the in-app browser preview's text (JSON text answer).

### `secret.*`

- `secret` — Masked value for a named env var (skills / setup flows).

### `sudo.*`

- `sudo` — Masked sudo password for the terminal tool.

### `terminal.*`

- `terminal.read` — Read the visible in-app terminal buffer (JSON text answer).

### `tour.*`

- `tour` — Drive a guided tour highlight in the desktop renderer.

### `vault.*`

- `vault.code` — A one-time / 2FA code the user reads from their device.
- `vault.save_login` — Save a login for a site the agent is about to fill; the answer is JSON {identifier, password}.
- `vault.unlock_prompt` — Master password to unlock an external password manager for this session.

### `window.*`

- `window.read` — Enumerate the native window below the app (JSON text answer).

## Events (75)


### `agent.*`

- `agent.terminal.output` — Output chunk from an agent-owned background process.

### `approval.*`

- `approval.cancelled` — Pending gateway approvals were dropped by interrupt/reap/teardown; the wait resolved as deny (not a user refusal).

### `background.*`

- `background.complete` — A /background side agent finished.

### `billing.*`

- `billing.step_up.verification` — Device-flow URL + code for the billing scope step-up; the client opens the browser.

### `bot_relay.*`

- `bot_relay.outbox.pending` — A bot-relay outbox envelope is queued; drain it.

### `browser.*`

- `browser.controller.cancel` — Withdraw a pending controller command.
- `browser.controller.command` — Dispatch one browser action to the attached controller.
- `browser.progress` — Browser (CDP) connect / install progress line.

### `btw.*`

- `btw.complete` — A /btw side question was answered.

### `connection.*`

- `connection.request` — A connection operation opened on this session; the desktop renders its card.
- `connection.update` — One transition or the settlement of an open connection operation.

### `cron.*`

- `cron.changed` — cron/jobs.json moved; refetch the cron list.

### `display.*`

- `display.install.done` — The install ended (0 ok, -1 cancelled, -2 no sudo: the command to run by hand was streamed).
- `display.install.log` — One line of package-manager output.
- `display.lease` — The takeover lease changed hands; every client repaints.
- `display.status` — This profile's screen started or stopped (also for transitions made outside hermes serve).

### `error.*`

- `error` — A session-level failure outside a turn (agent init, model switch, compression, resume).

### `gateway.*`

- `gateway.ready` — First frame of a connection: the resolved skin, the change-event capability and the replay epoch.

### `layout.*`

- `layout.apply` — Apply a named desktop layout preset.

### `message.*`

- `message.complete` — The turn ended: final text, usage and outcome.
- `message.delta` — One streamed chunk of the assistant reply.
- `message.interim` — Interim assistant commentary (text beside tool calls) sealed as its own segment.
- `message.reaction` — The agent reacted to a message; paint it live.
- `message.start` — A turn began streaming; no payload.

### `moa.*`

- `moa.aggregating` — The MoA aggregator started.
- `moa.phase` — MoA phase transition (currently only ``aggregator``).
- `moa.progress` — MoA reference fan-out progress (n/total).
- `moa.reference` — One MoA reference model's output.

### `notice.*`

- `notice` — Informational one-liner for the session (capabilities refreshed).

### `notification.*`

- `notification.clear` — Withdraw the notice with this key.
- `notification.show` — Show / replace a keyed out-of-band notice (toast or status bar).

### `pairing.*`

- `pairing.changed` — Pairing state moved; refetch pairing.

### `pane.*`

- `pane.reveal` — Focus / reveal a named desktop pane.

### `pet.*`

- `pet.changed` — The active pet / its spritesheet changed (watcher).
- `pet.generate.progress` — Pet base-draft generation progress.
- `pet.hatch.progress` — Pet hatch (row drawing) progress.

### `platforms.*`

- `platforms.changed` — gateway_state.json moved; refetch platform status.

### `preview.*`

- `preview.close` — Close the preview pane or one tab.
- `preview.open` — Open a URL / file in the desktop preview pane.
- `preview.restart.complete` — The hidden preview-restart agent finished.
- `preview.restart.progress` — Progress line from the preview-restart agent.

### `projects.*`

- `projects.changed` — projects.db moved; refetch the project list + tree.

### `reaction.*`

- `reaction` — Affection reaction detected in the user's message (hearts etc.).

### `reasoning.*`

- `reasoning.available` — A completed reasoning block (non-streaming providers).
- `reasoning.delta` — One streamed chunk of the model's reasoning.

### `request.*`

- `request.cancel` — The backend withdrew an open server→client request; clear the matching card only.

### `review.*`

- `review.summary` — Background review of the last turn finished.

### `session.*`

- `session.control.update` — Persisted goal / loop / heartbeat state changed.
- `session.info` — Live session settings snapshot (``server._session_info``); also the ``info`` of create/resume/activate.
- `session.reclaimed` — The backend reclaimed a live session out from under its clients.
- `session.resume_progress` — Deferred resume hydration progress.
- `session.title` — Auto-titling renamed the session (``session_id`` is the stored key).
- `session.usage` — Mid-turn usage tick; message.complete carries the authoritative final usage.

### `sessions.*`

- `sessions.changed` — state.db moved; refetch the session list.

### `setup.*`

- `setup.ready` — The free-tier bootstrap finished (broadcast); the desktop's setup gate reads the record.

### `skin.*`

- `skin.changed` — The active skin moved (name switch or live colour edit); repaint from this palette.

### `status.*`

- `status.update` — Transient status line (kind: status, lifecycle, compacting, goal, loop, heartbeat, process, …).

### `subagent.*`

- `subagent.complete` — A child finished (status + observability rollup).
- `subagent.progress` — Batched tool-name progress from a child.
- `subagent.spawn_requested` — delegate_task accepted a child goal (before the child starts).
- `subagent.start` — A delegated child started running.
- `subagent.thinking` — A child's reasoning chunk.
- `subagent.tool` — A child called a tool.

### `terminal.*`

- `terminal.close` — An agent-owned background process closed.

### `thinking.*`

- `thinking.delta` — Legacy thinking-text chunk (thinking_callback).

### `tip.*`

- `tip.show` — Point at a desktop element with a one-line tip bubble.

### `todo.*`

- `todo.updated` — Full todo snapshot after a todo tool ran.

### `tool.*`

- `tool.complete` — A tool call finished: parsed result, summary, optional diff / todo snapshot.
- `tool.generating` — The model is emitting a tool call's arguments.
- `tool.output_risk` — Tool output was classified as risky (prompt-injection / secret findings).
- `tool.start` — A tool call began (stable id + full args).

### `voice.*`

- `voice.interrupted` — Barge-in: the spoken interjection interrupted the turn; no payload.
- `voice.status` — Voice recorder state changed.
- `voice.transcript` — A voice capture produced text (or a stop phrase / silence limit).

### `wake.*`

- `wake.detected` — A wake phrase fired.
