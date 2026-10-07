"""Probe 08 — gated auth (basic-auth provider) + RFC 8252 native sign-in end-to-end:
status advertisement, negatives (no credential, legacy session token, wrong password),
PKCE chain authorize → password-login → native/token → WS with Bearer access token,
refresh rotation + old-refresh rejection, REST Bearer identity probe.
Captures to .probe/captures/p08-gated-auth.json (HTTP transcript summary).

Requires the probe gateway launched with:
  HERMES_DASHBOARD_BASIC_AUTH_USERNAME=probe
  HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=probe-pass-123
  HERMES_DASHBOARD_BASIC_AUTH_SECRET=<any 32+ random>

Run from repo root:  uv run --with websockets --with httpx scripts/probe/p08_gated_auth.py
"""

import asyncio
import base64
import hashlib
import json
import pathlib
import secrets
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import httpx

from gw import GW, load_base_url  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
HTTP_BASE = "http://127.0.0.1:9877"
USERNAME, PASSWORD = "probe", "probe-pass-123"
transcript: list[dict] = []


def note(label, obj, n=300):
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)
    print(f"{label}: {s if len(s) <= n else s[:n] + '…'}")
    transcript.append({"label": label, "value": s})


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


async def ws_check(label: str, token: str, expect_ok: bool) -> None:
    await ws_check_qs(label, f"token={token}", expect_ok)


async def ws_check_qs(label: str, query: str, expect_ok: bool) -> None:
    url = f"{load_base_url(ROOT)}?{query}"
    try:
        async with GW(url, token=None) as gw:  # type: ignore[arg-type]
            ev = await gw.next_event(timeout=10)
            ok = (ev.get("params") or {}).get("type") == "gateway.ready"
            note(f"WS {label}", f"CONNECTED ready={ok} (expected {'ok' if expect_ok else 'rejection'})")
    except Exception as exc:
        note(f"WS {label}", f"REJECTED {type(exc).__name__}: {str(exc)[:120]}")


async def main() -> None:
    async with httpx.AsyncClient(base_url=HTTP_BASE, follow_redirects=False, timeout=10) as http:
        # 1. status advertisement
        status = (await http.get("/api/status")).json()
        note("STATUS auth", {k: status.get(k) for k in ("auth_required", "auth_providers", "auth_flows")})

        # 2. negatives
        me = await http.get("/api/auth/me")
        note("ME without auth → HTTP", me.status_code)
        await ws_check("no credential", token="", expect_ok=False)
        legacy = (ROOT / ".probe" / "token").read_text().strip()
        await ws_check("legacy HERMES_DASHBOARD_SESSION_TOKEN", token=legacy, expect_ok=False)
        bad_login = await http.post("/auth/password-login",
                                    json={"provider": "basic", "username": USERNAME, "password": "WRONG", "next": ""})
        note("PASSWORD-LOGIN wrong password → HTTP", f"{bad_login.status_code} {bad_login.text[:120]}")

        # 3. PKCE chain
        verifier, challenge = pkce_pair()
        state = secrets.token_urlsafe(16)
        redirect_uri = "http://127.0.0.1:9/cb"  # no real listener: the code rides the JSON `next`, never fetched
        authz = await http.get("/auth/native/authorize", params={
            "provider": "basic", "code_challenge": challenge,
            "code_challenge_method": "S256", "redirect_uri": redirect_uri, "state": state})
        note("AUTHORIZE → HTTP", f"{authz.status_code} Location: {authz.headers.get('location')} "
                                 f"Set-Cookie: {authz.headers.get('set-cookie', '')[:80]}")

        login = await http.post("/auth/password-login",
                                json={"provider": "basic", "username": USERNAME, "password": PASSWORD, "next": ""})
        body = login.json()
        note("PASSWORD-LOGIN ok → ", f"HTTP {login.status_code} next={body.get('next')}")
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(body["next"]).query)
        code, ret_state = qs.get("code", [""])[0], qs.get("state", [""])[0]
        note("LOOPBACK CODE", f"code={code[:12]}… state_ok={ret_state == state}")

        tok = await http.post("/auth/native/token", json={"code": code, "code_verifier": verifier})
        tokens = tok.json()
        note("NATIVE TOKEN →", {k: (v[:16] + "…" if isinstance(v, str) and len(v) > 20 else v)
                                for k, v in tokens.items()})
        access, refresh = tokens["access_token"], tokens["refresh_token"]

        # code reuse must fail (single-use)
        reuse = await http.post("/auth/native/token", json={"code": code, "code_verifier": verifier})
        note("NATIVE TOKEN code reuse → HTTP", f"{reuse.status_code} {reuse.text[:100]}")

        # 4. use the access token: REST identity + WS
        me2 = await http.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
        note("ME with Bearer →", f"HTTP {me2.status_code} {me2.text[:160]}")

    await ws_check("access token", token=access, expect_ok=True)

    # browser ticket path: mint a 30s single-use ticket with Bearer, WS upgrade with ?ticket=
    async with httpx.AsyncClient(base_url=HTTP_BASE, follow_redirects=False, timeout=10) as http:
        tick = await http.post("/api/auth/ws-ticket", headers={"Authorization": f"Bearer {access}"})
        note("WS-TICKET mint →", f"HTTP {tick.status_code} {tick.text[:100]}")
        ticket = tick.json().get("ticket", "")
    await ws_check_qs("30s ticket", f"ticket={ticket}", expect_ok=True)
    await ws_check_qs("ticket reuse", f"ticket={ticket}", expect_ok=False)

    # full RPC over the token-authenticated socket
    async with GW(load_base_url(ROOT), access) as gw:
        await gw.next_event(timeout=10)
        await gw.rpc("client.capabilities", {"server_requests": True})
        lst = await gw.rpc("session.list", {})
        note("RPC session.list over Bearer", f"{len((lst.get('result') or {}).get('sessions', []))} sessions")

    # 5. refresh rotation + old-refresh rejection
    async with httpx.AsyncClient(base_url=HTTP_BASE, follow_redirects=False, timeout=10) as http:
        ref = await http.post("/auth/native/refresh", json={"refresh_token": refresh})
        new_tokens = ref.json()
        note("REFRESH →", f"HTTP {ref.status_code} " + json.dumps(
            {k: (v[:16] + "…" if isinstance(v, str) and len(v) > 20 else v) for k, v in new_tokens.items()}))
        stale = await http.post("/auth/native/refresh", json={"refresh_token": refresh})
        note("REFRESH old token reuse →", f"HTTP {stale.status_code} {stale.text[:120]}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        out = ROOT / ".probe" / "captures" / "p08-gated-auth.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(transcript, ensure_ascii=False, indent=1))
        print("TRANSCRIPT WRITTEN")
