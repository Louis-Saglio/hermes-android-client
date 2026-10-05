"""Probe 01 — core loop: ready, capabilities, session create/list/history/usage/status,
prompt with streaming, prompt with terminal tool call. Captures raw frames to
.probe/captures/p01-core-loop.jsonl (local only).

Run from repo root:  uv run --with websockets scripts/probe/p01_core_loop.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=220):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        # 1. gateway.ready is the first frame after accept
        ready = await gw.next_event(timeout=15)
        print("READY:", short(ready))

        # 2. advertise server→client request support
        caps = await gw.rpc("client.capabilities", {"server_requests": True})
        print("CAPABILITIES:", short(caps))

        # 3. create a session
        created = await gw.rpc("session.create", {"title": "probe-core"})
        print("SESSION.CREATE:", short(created))
        sid = (created.get("result") or {}).get("session_id") or (created.get("result") or {}).get("id")
        assert sid, f"no session id in {created}"
        print("SESSION_ID:", sid)

        # 4. plain prompt, collect until assistant turn completes
        sub = await gw.rpc("prompt.submit", {"session_id": sid, "text": "Reply with exactly: PROBE_OK"})
        print("PROMPT.SUBMIT:", short(sub))
        events = await gw.collect_until(lambda e: ev_type(e) in ("message.complete", "session.status"), timeout=90)
        types = [ev_type(e) for e in events]
        print("TURN1 EVENT TYPES:", types)
        completes = [e for e in events if ev_type(e) == "message.complete"]
        print("TURN1 COMPLETE:", short(completes[-1]) if completes else "NONE")

        # 5. prompt that forces a terminal tool call
        await gw.rpc("prompt.submit", {
            "session_id": sid,
            "text": "Use the terminal tool to run exactly: echo PROBE_TOOL_$((40+2))\nThen reply with only the tool output.",
        })
        events2 = await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=120)
        types2 = [ev_type(e) for e in events2]
        print("TURN2 EVENT TYPES:", types2)
        for e in events2:
            if ev_type(e) in ("tool.start", "tool.complete"):
                print(" ", ev_type(e), short((e.get("params") or {}).get("payload", {}), 300))

        # 6. session introspection RPCs
        for method, params in (
            ("session.list", {}),
            ("session.status", {"session_id": sid}),
            ("session.usage", {"session_id": sid}),
            ("session.history", {"session_id": sid}),
        ):
            resp = await gw.rpc(method, params)
            print(f"{method.upper()}:", short(resp, 400))

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p01-core-loop.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
