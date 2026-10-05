"""Probe 04 — disconnect/reconnect mid-turn: drop the WS while a turn runs, reconnect,
session.resume (inflight + open_requests), session.events.since replay, live re-attach.
Captures to .probe/captures/p04-reconnect.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p04_reconnect.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=360):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def main() -> None:
    cap1 = Capture()
    sid_live = sid_stored = None
    # ── connection 1: create + start a slow turn, then drop the socket mid-turn
    async with GW(load_base_url(ROOT), load_token(ROOT), cap1) as gw1:
        await gw1.next_event(timeout=15)
        await gw1.rpc("client.capabilities", {"server_requests": True})
        created = await gw1.rpc("session.create", {"title": "probe-reconnect"})
        r = created.get("result") or {}
        sid_live, sid_stored = r.get("session_id"), r.get("stored_session_id")
        await gw1.rpc("prompt.submit", {
            "session_id": sid_live,
            "text": "Use the terminal tool to run exactly: sleep 12 && echo RECONNECT_MARK. "
                    "Then reply with only the word TURN_FINISHED_NORMALLY.",
        })
        await gw1.collect_until(lambda e: ev_type(e) == "tool.start", timeout=90)
        print("tool started; disconnecting NOW")
    cap1.dump_jsonl(ROOT / ".probe" / "captures" / "p04-reconnect-conn1.jsonl")

    await asyncio.sleep(2)  # let the turn run while no client is attached

    # ── connection 2: resume the stored session, inspect inflight + replay
    cap2 = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap2) as gw2:
        await gw2.next_event(timeout=15)
        await gw2.rpc("client.capabilities", {"server_requests": True})

        res = await gw2.rpc("session.resume", {"session_id": sid_stored})
        print("RESUME:", short(res, 900))

        live_id = (res.get("result") or {}).get("session_id") or sid_live
        since = await gw2.rpc("session.events.since", {"session_id": live_id, "last_seen": 0})
        print("EVENTS.SINCE:", short(since, 700))

        # The turn should still finish; live events must arrive on this new connection.
        try:
            events = await gw2.collect_until(lambda e: ev_type(e) == "message.complete", timeout=90)
            types = [ev_type(e) for e in events]
            print("POST-RESUME LIVE EVENTS:", [t for t in types if "delta" not in t])
            complete = [e for e in events if ev_type(e) == "message.complete"][-1]
            print("FINAL TEXT:", repr((complete.get("params") or {}).get("payload", {}).get("text", "")[:120]))
        except TimeoutError:
            print("no message.complete within 90s after resume")

    cap2.dump_jsonl(ROOT / ".probe" / "captures" / "p04-reconnect-conn2.jsonl")
    print("CAPTURES WRITTEN")


if __name__ == "__main__":
    asyncio.run(main())
