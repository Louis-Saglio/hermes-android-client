"""Probe 02b — clean mid-turn steer: one prompt with a long tool call, steer while the tool
runs (no competing submit), observe delivery in the answer + how it persists in history.
Captures to .probe/captures/p02b-steer-clean.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p02b_steer_clean.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=260):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)
        await gw.rpc("client.capabilities", {"server_requests": True})
        created = await gw.rpc("session.create", {"title": "probe-steer-clean"})
        sid = (created.get("result") or {}).get("session_id")

        await gw.rpc("prompt.submit", {
            "session_id": sid,
            "text": "Use the terminal tool to run exactly: sleep 10 && echo BASE_DONE. "
                    "After it finishes, reply with only the word BORING_WORD.",
        })

        # Wait until the terminal tool is actually running, then steer.
        await gw.collect_until(lambda e: ev_type(e) == "tool.start", timeout=90)
        steer = await gw.rpc("session.steer", {
            "session_id": sid,
            "text": "Change of plan: after the tool finishes, reply with only the word PINEAPPLE_9872.",
        })
        print("STEER:", short(steer))

        events = await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=120)
        for e in events:
            t = ev_type(e)
            if t not in ("thinking.delta", "reasoning.delta", "message.delta"):
                print("EV", t, short((e.get("params") or {}).get("payload", {}), 200))
        complete = [e for e in events if ev_type(e) == "message.complete"][-1]
        text = (complete.get("params") or {}).get("payload", {}).get("text", "")
        print("FINAL TEXT:", repr(text[:200]))
        print("STEER APPLIED:", "PINEAPPLE_9872" in text)

        hist = await gw.rpc("session.history", {"session_id": sid})
        for m in (hist.get("result") or {}).get("messages", []):
            print("HIST:", short({k: m.get(k) for k in ("role", "text", "display_kind", "row_id")}, 200))

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p02b-steer-clean.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
