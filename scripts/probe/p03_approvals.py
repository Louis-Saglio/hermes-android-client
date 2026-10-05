"""Probe 03 — approval flow (approvals.mode: manual): dangerous command triggers an
`approval` server→client request; answer once (runs), then deny (blocked). Also exercises
the approval.pending replay RPC while a request is open.
Captures to .probe/captures/p03-approvals.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p03_approvals.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=320):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def run_with_approval(gw: GW, sid: str, cmd_echo: str, choice: dict) -> None:
    await gw.rpc("prompt.submit", {
        "session_id": sid,
        "text": f"Use the terminal tool to run exactly: {cmd_echo}. Then reply with only the tool output.",
    })
    # Wait for the approval request OR an early turn end (model declining to use the tool).
    req_task = asyncio.ensure_future(gw.next_server_request(timeout=120))
    done_task = asyncio.ensure_future(gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=120))
    await asyncio.wait({req_task, done_task}, return_when=asyncio.FIRST_COMPLETED)
    if done_task.done() and not req_task.done():
        req_task.cancel()
        complete = [e for e in done_task.result() if ev_type(e) == "message.complete"][-1]
        print(f" NO APPROVAL — turn ended textually ({choice}):",
              repr((complete.get("params") or {}).get("payload", {}).get("text", "")[:140]))
        return
    done_task.cancel()
    req = req_task.result()
    print(f"APPROVAL REQUEST ({choice}):", short(req))
    # While it's open, exercise the replay RPC.
    pend = await gw.rpc("approval.pending", {"session_id": sid})
    print("APPROVAL.PENDING:", short(pend))
    await gw.answer_server_request(req, choice)
    events = await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=120)
    for e in events:
        t = ev_type(e)
        if t in ("tool.start", "tool.complete", "message.complete", "request.cancel"):
            print(" EV", t, short((e.get("params") or {}).get("payload", {}), 260))
    complete = [e for e in events if ev_type(e) == "message.complete"][-1]
    print(" FINAL:", repr((complete.get("params") or {}).get("payload", {}).get("text", "")[:160]))


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)
        await gw.rpc("client.capabilities", {"server_requests": True})
        created = await gw.rpc("session.create", {"title": "probe-approvals"})
        sid = (created.get("result") or {}).get("session_id")
        assert sid, f"no session id in {created}"
        info = (created.get("result") or {}).get("info", {})
        print("APPROVAL MODE:", info.get("approval_mode"), "| yolo:", info.get("yolo"))

        await run_with_approval(gw, sid, "rm -rf /tmp/probe-danger-a && echo CLEANED_A", {"choice": "once"})
        await run_with_approval(gw, sid, "rm -rf /tmp/probe-danger-b && echo CLEANED_B", {"choice": "deny"})

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p03-approvals.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
