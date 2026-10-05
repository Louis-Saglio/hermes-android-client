"""Diagnostic — what actually happens on a dangerous command under approvals.mode manual.
Prints approval_mode + every non-delta frame for 90s.

Run from repo root:  uv run --with websockets scripts/probe/diag_approval.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=300):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)
        await gw.rpc("client.capabilities", {"server_requests": True})
        created = await gw.rpc("session.create", {"title": "diag-approval"})
        r = created.get("result") or {}
        sid = r.get("session_id")
        print("INFO:", short(r.get("info", {}), 400))
        await gw.rpc("prompt.submit", {
            "session_id": sid,
            "text": "Use the terminal tool to run exactly: rm -rf /tmp/probe-diag-x && echo CLEANED_X. "
                    "Then reply with only the tool output.",
        })
        deadline = asyncio.get_running_loop().time() + 90
        while asyncio.get_running_loop().time() < deadline:
            try:
                ev = await asyncio.wait_for(gw._events.get(), timeout=8)
            except TimeoutError:
                try:
                    req = await gw.next_server_request(timeout=0.1)
                    print("!! SERVER REQUEST LATE:", short(req))
                except TimeoutError:
                    pass
                continue
            t = ev_type(ev)
            if "delta" not in t:
                print("EV", t, short((ev.get("params") or {}).get("payload", {}), 240))
        try:
            while True:
                req = await gw.next_server_request(timeout=0.5)
                print("SERVER REQUEST:", short(req))
        except TimeoutError:
            pass
        cap.dump_jsonl(ROOT / ".probe" / "captures" / "diag-approval.jsonl")
        print("capture frames:", len(cap.frames))


if __name__ == "__main__":
    asyncio.run(main())
