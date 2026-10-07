"""Probe 07 — session lifecycle: title set, compress, branch, archive, delete, most_recent.
Captures to .probe/captures/p07-lifecycle.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p07_lifecycle.py
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


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)
        await gw.rpc("client.capabilities", {"server_requests": True})
        created = await gw.rpc("session.create", {"title": "probe-lifecycle"})
        r = created.get("result") or {}
        sid, stored = r.get("session_id"), r.get("stored_session_id")
        print("live:", sid, "| stored:", stored)

        # give the session some history to compress
        await gw.rpc("prompt.submit", {"session_id": sid, "text": "Name three colors, just the words."})
        await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=90)

        for method, params in (
            ("session.title", {"session_id": sid, "title": "RENAMED_BY_PROBE"}),
            ("session.compress", {"session_id": sid}),
            ("session.branch", {"session_id": sid}),
            ("session.most_recent", {}),
        ):
            try:
                resp = await gw.rpc(method, params, timeout=120)
                print(f"{method.upper()}:", short(resp))
            except Exception as exc:
                print(f"{method.upper()} FAILED: {exc}")

        lst = await gw.rpc("session.list", {})
        for s in (lst.get("result") or {}).get("sessions", []):
            print("LIST ROW:", short(s, 200))

        # archive + delete the branch offspring and the original
        for target in (stored,):
            print("ARCHIVE:", short(await gw.rpc("session.archive", {"session_id": target})))
        print("SESSION.CLOSE:", short(await gw.rpc("session.close", {"session_id": sid})))
        print("DELETE:", short(await gw.rpc("session.delete", {"session_id": stored})))

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p07-lifecycle.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
