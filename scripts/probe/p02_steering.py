"""Probe 02 — mid-turn control: session.steer during a running turn, prompt.submit while busy
(busy-input policy), session.interrupt. Captures to .probe/captures/p02-steering.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p02_steering.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=200):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)  # gateway.ready
        await gw.rpc("client.capabilities", {"server_requests": True})
        created = await gw.rpc("session.create", {"title": "probe-steering"})
        sid = (created.get("result") or {}).get("session_id")

        # Start a slow turn: long reasoning + terminal sleep so we have time to act.
        sub = await gw.rpc("prompt.submit", {
            "session_id": sid,
            "text": "First use the terminal tool to run: sleep 20 && echo SLEPT. "
                    "While it runs, count slowly from 1 to 30 in your reply.",
        })
        print("SUBMIT:", short(sub))

        # Wait until the turn is actually streaming, then steer mid-turn.
        await gw.collect_until(lambda e: ev_type(e) in ("message.start", "thinking.delta", "reasoning.delta"), timeout=30)
        steer = await gw.rpc("session.steer", {"session_id": sid, "text": "STEER_PROBE: stop counting, just wait for the command."})
        print("STEER:", short(steer))

        # While busy: submit an ordinary prompt → observe busy-input policy.
        busy = await gw.rpc("prompt.submit", {"session_id": sid, "text": "SECOND_PROMPT_WHILE_BUSY"})
        print("BUSY SUBMIT:", short(busy))

        # Interrupt the turn.
        await asyncio.sleep(1)
        intr = await gw.rpc("session.interrupt", {"session_id": sid})
        print("INTERRUPT:", short(intr))

        # Drain until the session settles (message.complete or explicit interrupted state).
        try:
            events = await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=45)
            print("POST-INTERRUPT EVENT TYPES:", [ev_type(e) for e in events][-8:])
            completes = [e for e in events if ev_type(e) == "message.complete"]
            if completes:
                print("FINAL COMPLETE:", short(completes[-1], 400))
        except TimeoutError:
            print("no message.complete within 45s after interrupt")

        status = await gw.rpc("session.usage", {"session_id": sid})
        print("USAGE AFTER:", short(status))

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p02-steering.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
