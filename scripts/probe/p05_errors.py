"""Probe 05 — error taxonomy: unknown method (-32601), params validation (4000),
bad session id, model/provider override mismatch (-32602 + suggestions), rewind guards
(4004 without confirm, 4018 stale row_id, 4009 busy). Captures to .probe/captures/p05-errors.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p05_errors.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def show(label, resp, n=260):
    s = json.dumps(resp, ensure_ascii=False)
    print(f"{label}:", s if len(s) <= n else s[:n] + "…")


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)
        await gw.rpc("client.capabilities", {"server_requests": True})

        show("UNKNOWN METHOD", await gw.rpc("no.such.method"))
        show("UNKNOWN NAMESPACE", await gw.rpc("session.frobnicate"))
        show("PARAMS UNKNOWN KEY", await gw.rpc("session.create", {"title": "x", "bogus_key": 1}))
        show("PARAMS WRONG TYPE", await gw.rpc("session.create", {"title": 42}))
        show("BAD SESSION ID (usage)", await gw.rpc("session.usage", {"session_id": "deadbeef"}))
        show("BAD SESSION ID (resume)", await gw.rpc("session.resume", {"session_id": "20260101_000000_zzzzzz"}))
        show("MODEL OVERRIDE MISMATCH", await gw.rpc(
            "session.create", {"title": "probe-model", "model": "gpt-5.5", "provider": "anthropic"}))

        # Rewind guards on a real session.
        created = await gw.rpc("session.create", {"title": "probe-errors"})
        sid = (created.get("result") or {}).get("session_id")
        show("REWIND NO CONFIRM", await gw.rpc("prompt.submit", {
            "session_id": sid, "text": "hi", "truncate_before_user_ordinal": 0}))
        show("REWIND STALE ROW ID", await gw.rpc("prompt.submit", {
            "session_id": sid, "text": "hi", "truncate_before_row_id": 999999, "confirm_truncate": True}))
        show("REWIND EMPTY NO CONFIRM2", await gw.rpc("prompt.submit", {
            "session_id": sid, "text": "hi", "truncate_before_user_ordinal": 0,
            "confirm_truncate": True}))

        # Busy: start a slow turn then fire a rewind (expect 4009).
        await gw.rpc("prompt.submit", {"session_id": sid, "text": "Use the terminal tool to run: sleep 15 && echo T. Then say done."})
        await gw.collect_until(lambda e: ev_type(e) in ("message.start", "thinking.delta", "reasoning.delta"), timeout=30)
        show("REWIND WHILE BUSY", await gw.rpc("prompt.submit", {
            "session_id": sid, "text": "edited", "truncate_before_row_id": 1, "confirm_truncate": True}))
        show("INTERRUPT", await gw.rpc("session.interrupt", {"session_id": sid}))
        try:
            await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=40)
        except TimeoutError:
            print("(no complete after interrupt within 40s)")

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p05-errors.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
