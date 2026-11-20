#!/usr/bin/env python3
"""Tochka Bank API client (stdlib-only, verified prod 2026-04-20).

Setup: `init` (personal JWT) or `init --oauth` (OAuth 2.0 + Consent).
Sandbox: TOCHKA_SANDBOX=1.

Token resolution (in `request()`):
  1. $TOCHKA_TOKEN env var
  2. OAuth access_token from Keychain (auto-refreshed near expiry, if auth_mode=oauth)
  3. OS credential store (service `tochka-bank-api-token`)  — personal JWT
  4. ~/.config/tochka-bank-api/token (chmod 600 fallback)

19 subcommands (`--help` on each for flags). State-changing ones are gated by
the repo hook `.claude/hooks/tochka-require-confirmation.sh` (Claude Code prompt).

All paths use v2.0 where the bank offers it; Invoice API mixes v1.0/v2.0,
closing docs are v1.0 only. Live ReDoc is the source of truth for shapes:
https://enter.tochka.com/doc/v2/redoc
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Optional


CONFIG_DIR = Path.home() / ".config" / "tochka-bank-api"
TOKEN_FILE = CONFIG_DIR / "token"
CONFIG_FILE = CONFIG_DIR / "config.json"
CERT_DIR = CONFIG_DIR / "oauth-certs"

# Keychain service names (different keys = different credentials)
KEYCHAIN_SERVICE = "tochka-bank-api-token"                  # personal JWT
KC_OAUTH_CLIENT_ID = "tochka-bank-api-oauth-client-id"
KC_OAUTH_CLIENT_SECRET = "tochka-bank-api-oauth-client-secret"
KC_OAUTH_REFRESH_TOKEN = "tochka-bank-api-oauth-refresh-token"
KC_OAUTH_ACCESS_TOKEN = "tochka-bank-api-oauth-access-token"

# OAuth endpoints
OAUTH_TOKEN_URL = "https://enter.tochka.com/connect/token"
OAUTH_AUTHORIZE_URL = "https://enter.tochka.com/connect/authorize"
# Canonical path per swagger v1.90.4-stable — /uapi/consent/v1.0/consents.
# Legacy /uapi/v1.0/consents still resolved on prod as of 2026-04-20 but
# the swagger-documented form is the safer target.
OAUTH_CONSENT_URL = "https://enter.tochka.com/uapi/consent/v1.0/consents"

# Default OAuth scopes and permissions (set once — reused each time).
DEFAULT_OAUTH_SCOPES = "accounts balances customers statements sbp payments acquiring"
# Full list of accepted permissions (verified against prod 2026-04-20 — Tochka's
# validation response enumerates exactly these values; any other is rejected):
#   ReadAccountsBasic, ReadAccountsDetail, ReadBalances, ReadStatements,
#   ReadTransactionsBasic, ReadTransactionsCredits, ReadTransactionsDebits,
#   ReadTransactionsDetail, ReadCustomerData, ReadSBPData, EditSBPData,
#   CreatePaymentForSign, CreatePaymentOrder, ReadAcquiringData,
#   MakeAcquiringOperation, ManageInvoiceData, ManageWebhookData,
#   MakeCustomer, ManageGuarantee.
# Note: no ReadInvoiceData — invoices are covered by ManageInvoiceData only.
DEFAULT_OAUTH_PERMISSIONS = [
    "ReadAccountsBasic", "ReadAccountsDetail",
    "ReadBalances",
    "ReadStatements",
    "ReadTransactionsBasic", "ReadTransactionsCredits",
    "ReadTransactionsDebits", "ReadTransactionsDetail",
    "ReadCustomerData",
    "ReadSBPData", "EditSBPData",
    "CreatePaymentForSign", "CreatePaymentOrder",
    "ReadAcquiringData", "MakeAcquiringOperation",
    "ManageInvoiceData",
    "ManageWebhookData",
    # Skipping MakeCustomer (partner banks) and ManageGuarantee (bank guarantees) —
    # outside typical single-company automation scope. Add if needed later.
]

# Closed whitelist for Positions[].unitCode (invoices and closing documents).
# Anything outside this set returns 400 Validation Error from the API. Notable
# absences: no monthly/yearly units — periodic subscriptions use "услуга." or
# "шт.", with the period encoded in the position name. Verified prod 2026-05-08.
VALID_UNIT_CODES = [
    "шт.", "тыс.шт.", "компл.", "пар.", "усл.ед.", "упак.", "услуга.",
    "пач.", "мин.", "ч.", "сут.", "г.", "кг.", "л.", "м.", "м2.", "м3.",
    "км.", "га.", "кВт.", "кВт.ч.",
]


def base_url() -> str:
    if os.environ.get("TOCHKA_SANDBOX") == "1":
        return "https://enter.tochka.com/sandbox/v2"
    return "https://enter.tochka.com/uapi"


def _is_wsl() -> bool:
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def _read_windows_credential(target: str) -> Optional[str]:
    import ctypes
    import ctypes.wintypes

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", ctypes.wintypes.DWORD),
            ("Type", ctypes.wintypes.DWORD),
            ("TargetName", ctypes.wintypes.LPWSTR),
            ("Comment", ctypes.wintypes.LPWSTR),
            ("LastWritten", ctypes.wintypes.FILETIME),
            ("CredentialBlobSize", ctypes.wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
            ("Persist", ctypes.wintypes.DWORD),
            ("AttributeCount", ctypes.wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", ctypes.wintypes.LPWSTR),
            ("UserName", ctypes.wintypes.LPWSTR),
        ]

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.CredReadW.restype = ctypes.wintypes.BOOL
    advapi32.CredReadW.argtypes = [
        ctypes.wintypes.LPCWSTR, ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL)),
    ]
    advapi32.CredFree.restype = None
    advapi32.CredFree.argtypes = [ctypes.c_void_p]

    cred_ptr = ctypes.POINTER(CREDENTIAL)()
    if not advapi32.CredReadW(target, 1, 0, ctypes.byref(cred_ptr)):
        return None
    try:
        cred = cred_ptr.contents
        if cred.CredentialBlobSize > 0 and cred.CredentialBlob:
            return bytes(cred.CredentialBlob[:cred.CredentialBlobSize]).decode("utf-16-le")
        return None
    finally:
        advapi32.CredFree(cred_ptr)


def _read_wsl_credential(target: str) -> Optional[str]:
    ps_script = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class CredReader {{
    [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool CredRead(string target, int type, int flags, out IntPtr cred);
    [DllImport("advapi32.dll")]
    static extern void CredFree(IntPtr cred);
    [StructLayout(LayoutKind.Sequential)]
    struct CREDENTIAL {{
        public int Flags; public int Type;
        [MarshalAs(UnmanagedType.LPWStr)] public string TargetName;
        [MarshalAs(UnmanagedType.LPWStr)] public string Comment;
        public long LastWritten; public int CredentialBlobSize;
        public IntPtr CredentialBlob; public int Persist;
        public int AttributeCount; public IntPtr Attributes;
        [MarshalAs(UnmanagedType.LPWStr)] public string TargetAlias;
        [MarshalAs(UnmanagedType.LPWStr)] public string UserName;
    }}
    public static string Read(string target) {{
        IntPtr ptr;
        if (!CredRead(target, 1, 0, out ptr)) return null;
        try {{
            var c = Marshal.PtrToStructure<CREDENTIAL>(ptr);
            if (c.CredentialBlobSize > 0)
                return Marshal.PtrToStringUni(c.CredentialBlob, c.CredentialBlobSize / 2);
            return null;
        }} finally {{ CredFree(ptr); }}
    }}
}}
'@
[CredReader]::Read('{target}')
"""
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (FileNotFoundError, Exception):
        pass
    return None


def read_from_keychain(service: str = KEYCHAIN_SERVICE) -> Optional[str]:
    system = platform.system()
    try:
        if system == "Darwin":
            r = subprocess.run(
                ["security", "find-generic-password", "-a", os.getenv("USER", ""),
                 "-s", service, "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        elif system == "Linux":
            r = subprocess.run(
                ["secret-tool", "lookup", "service", service],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
            if _is_wsl():
                return _read_wsl_credential(service)
        elif system == "Windows":
            return _read_windows_credential(service)
    except Exception:
        pass
    return None


def store_in_keychain(value: str, service: str = KEYCHAIN_SERVICE, label: str = "Tochka Bank API") -> bool:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(
                ["security", "delete-generic-password", "-a", os.getenv("USER", ""),
                 "-s", service],
                capture_output=True, timeout=5,
            )
            r = subprocess.run(
                ["security", "add-generic-password", "-a", os.getenv("USER", ""),
                 "-s", service, "-w", value],
                capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0
        elif system == "Linux":
            if _is_wsl():
                r = subprocess.run(
                    ["cmd.exe", "/c", "cmdkey", f"/generic:{service}",
                     "/user:tochka", f"/pass:{value}"],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode == 0:
                    return True
            r = subprocess.run(
                ["secret-tool", "store", f"--label={label}",
                 "service", service],
                input=value, capture_output=True, text=True, timeout=10,
            )
            return r.returncode == 0
        elif system == "Windows":
            r = subprocess.run(
                ["cmdkey", f"/generic:{service}",
                 "/user:tochka", f"/pass:{value}"],
                capture_output=True, text=True, timeout=10,
            )
            return r.returncode == 0
    except (FileNotFoundError, Exception):
        return False
    return False


# Back-compat aliases (existing code references these).
def read_token_from_keychain() -> Optional[str]:
    return read_from_keychain(KEYCHAIN_SERVICE)


def store_token_in_keychain(value: str) -> bool:
    return store_in_keychain(value, KEYCHAIN_SERVICE, "Tochka Bank API JWT")


def auth_mode() -> str:
    """Return 'oauth' or 'jwt' based on config + available credentials."""
    cfg = load_config()
    if cfg.get("auth_mode") == "oauth":
        return "oauth"
    return "jwt"


def oauth_refresh_access_token() -> Optional[str]:
    """Exchange stored refresh_token for a new access_token. Returns access_token or None on failure."""
    client_id = read_from_keychain(KC_OAUTH_CLIENT_ID)
    client_secret = read_from_keychain(KC_OAUTH_CLIENT_SECRET)
    refresh_token = read_from_keychain(KC_OAUTH_REFRESH_TOKEN)
    if not (client_id and client_secret and refresh_token):
        return None

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode("utf-8")
    req = urllib.request.Request(OAUTH_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"[oauth] refresh failed: HTTP {e.code} {e.read().decode('utf-8','replace')[:300]}", file=sys.stderr)
        return None

    access = payload.get("access_token")
    new_refresh = payload.get("refresh_token")
    expires_in = int(payload.get("expires_in", 86400))
    if not access:
        return None

    store_in_keychain(access, KC_OAUTH_ACCESS_TOKEN, "Tochka OAuth access_token")
    if new_refresh:
        store_in_keychain(new_refresh, KC_OAUTH_REFRESH_TOKEN, "Tochka OAuth refresh_token")
    # Track expiry so we can skip pointless refresh attempts next time.
    cfg = load_config()
    cfg["oauth_access_expires_at"] = int(time.time()) + expires_in - 60  # 1-min safety margin
    _write_config(cfg)
    return access


def oauth_access_token(force_refresh: bool = False) -> Optional[str]:
    """Get a valid OAuth access_token — cached if fresh, refreshed otherwise."""
    cfg = load_config()
    expires_at = cfg.get("oauth_access_expires_at", 0)
    if not force_refresh and expires_at and int(time.time()) < expires_at:
        cached = read_from_keychain(KC_OAUTH_ACCESS_TOKEN)
        if cached:
            return cached
    return oauth_refresh_access_token()


def token() -> str:
    # Fast path: explicit env override.
    tok = os.environ.get("TOCHKA_TOKEN")
    if tok:
        return tok
    # OAuth mode.
    if auth_mode() == "oauth":
        tok = oauth_access_token()
        if tok:
            return tok
        sys.exit(
            "error: OAuth mode set but no valid access_token. "
            "Re-run `init --oauth` to reauthorize."
        )
    # Personal JWT mode.
    tok = read_token_from_keychain()
    if not tok and TOKEN_FILE.exists():
        tok = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not tok:
        sys.exit(
            "error: no token found. Set TOCHKA_TOKEN env var or run one of:\n"
            "  python3 scripts/tochka_client.py init           # personal JWT\n"
            "  python3 scripts/tochka_client.py init --oauth   # full OAuth flow"
        )
    return tok


def request(method: str, path: str, body: dict | None = None, _retry: bool = True) -> dict:
    url = base_url() + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    # OAuth mode additionally requires a CustomerCode header for company-scoped calls.
    if auth_mode() == "oauth":
        cc = load_config().get("customer_code")
        if cc:
            req.add_header("CustomerCode", cc)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        # On 401 in OAuth mode, try a one-shot refresh before giving up.
        if e.code == 401 and _retry and auth_mode() == "oauth":
            if oauth_refresh_access_token():
                return request(method, path, body, _retry=False)
        body_text = e.read().decode("utf-8", errors="replace")
        hint = ""
        if e.code == 501 and ("statements" in path or "bills" in path):
            hint = (
                "\n\nHINT: this endpoint needs OAuth+Consent, not a personal JWT. "
                "Full bank statements and the Invoice API are behind the OAuth 2.0 "
                "consent flow on prod. Run `init --oauth` to set that up."
            )
        sys.exit(f"HTTP {e.code} {e.reason}\n{body_text}{hint}")


def _write_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(CONFIG_FILE, 0o600)


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolve_customer_code(explicit: str | None) -> str:
    if explicit:
        return explicit
    cfg = load_config()
    code = cfg.get("customer_code")
    if not code:
        sys.exit("error: --customer-code is required (or run `init` to save it)")
    return code


def resolve_account_id(explicit: str | None) -> str:
    if explicit:
        return explicit
    cfg = load_config()
    aid = cfg.get("default_account_id")
    if not aid:
        sys.exit("error: --account-id is required (or run `init` to save it)")
    return aid


def cmd_list_accounts(_: argparse.Namespace) -> None:
    resp = request("GET", "/open-banking/v2.0/accounts")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_config(_: argparse.Namespace) -> None:
    cfg = load_config()
    if not cfg:
        print("(no config saved — run `init` first)")
        return
    print(json.dumps(cfg, indent=2, ensure_ascii=False))


def cmd_list_incoming(args: argparse.Namespace) -> None:
    code = resolve_customer_code(args.customer_code)
    params = {"customerCode": code}
    if args.status:
        params["status"] = args.status
    qs = urllib.parse.urlencode(params)
    resp = request("GET", f"/acquiring/v2.0/payments?{qs}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_list_for_sign(args: argparse.Namespace) -> None:
    code = resolve_customer_code(args.customer_code)
    params = {"customerCode": code}
    if args.status:
        params["status"] = args.status
    qs = urllib.parse.urlencode(params)
    resp = request("GET", f"/payment/v2.0/for-sign?{qs}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def _ensure_localhost_cert(hosts: list[str]) -> Optional[tuple[str, str]]:
    """Return (cert_file, key_file) covering all `hosts` (localhost + 127.0.0.1 by default).
    Uses mkcert when available, falls back to self-signed via openssl."""
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CERT_DIR, 0o700)
    # Cert file name keyed by hosts so re-init with a different Redirect URL regenerates.
    tag = "-".join(sorted(hosts)).replace(".", "_")
    cert_file = CERT_DIR / f"cert-{tag}.pem"
    key_file = CERT_DIR / f"cert-{tag}-key.pem"

    if cert_file.exists() and key_file.exists():
        return str(cert_file), str(key_file)

    mkcert = None
    for candidate in ("mkcert", "/opt/homebrew/bin/mkcert", "/usr/local/bin/mkcert"):
        if subprocess.run(["which", candidate], capture_output=True).returncode == 0 \
           or os.path.exists(candidate):
            mkcert = candidate
            break

    if mkcert:
        subprocess.run([mkcert, "-install"], capture_output=True, timeout=30)
        r = subprocess.run(
            [mkcert, "-cert-file", str(cert_file), "-key-file", str(key_file), *hosts],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0 and cert_file.exists():
            os.chmod(cert_file, 0o600)
            os.chmod(key_file, 0o600)
            print(f"  [cert] mkcert issued cert for {hosts} → {cert_file}")
            return str(cert_file), str(key_file)
        print(f"  [cert] mkcert failed: {r.stderr[:300]}", file=sys.stderr)

    print("  [cert] mkcert not available — generating self-signed cert (browser will warn once).")
    print("  To avoid the warning: brew install mkcert && mkcert -install")
    # Build subjectAltName covering DNS names and IP literals.
    sans = []
    for h in hosts:
        if all(c.isdigit() or c == '.' for c in h):
            sans.append(f"IP:{h}")
        else:
            sans.append(f"DNS:{h}")
    san_ext = "subjectAltName=" + ",".join(sans)
    r = subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-days", "30",
         "-keyout", str(key_file),
         "-out", str(cert_file),
         "-subj", f"/CN={hosts[0]}",
         "-addext", san_ext],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0 or not cert_file.exists():
        print(f"  [cert] openssl failed: {r.stderr[:300]}", file=sys.stderr)
        return None
    os.chmod(cert_file, 0o600)
    os.chmod(key_file, 0o600)
    return str(cert_file), str(key_file)


def _oauth_get_app_token(client_id: str, client_secret: str, scope: str) -> str:
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }).encode("utf-8")
    req = urllib.request.Request(OAUTH_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"client_credentials failed: HTTP {e.code}\n{body}")
    tok = payload.get("access_token")
    if not tok:
        sys.exit(f"client_credentials response missing access_token: {payload}")
    return tok


def _oauth_create_consent(app_token: str, permissions: list[str]) -> str:
    body = json.dumps({
        "Data": {
            "permissions": permissions,
        }
    }).encode("utf-8")
    req = urllib.request.Request(OAUTH_CONSENT_URL, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {app_token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        sys.exit(f"consent creation failed: HTTP {e.code}\n{body_text}")
    consent_id = payload.get("Data", {}).get("consentId") or payload.get("Data", {}).get("Consent", {}).get("consentId")
    if not consent_id:
        sys.exit(f"consent response missing consentId: {payload}")
    return consent_id


def _oauth_exchange_code(client_id: str, client_secret: str, code: str,
                         redirect_uri: str, scope: str) -> dict:
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": scope,
    }).encode("utf-8")
    req = urllib.request.Request(OAUTH_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"authorization_code exchange failed: HTTP {e.code}\n{body}")


def _run_oauth_callback_server(cert_file: str, key_file: str, host: str, port: int,
                               callback_path: str = "/callback") -> tuple[str, str]:
    """Start a local HTTPS server, wait for {callback_path}?code=..., return (code, state)."""
    import http.server
    import ssl
    import threading

    captured = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a, **kw):
            pass  # silence

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if parsed.path.rstrip("/") == callback_path.rstrip("/"):
                if "code" in qs:
                    captured["code"] = qs["code"][0]
                    captured["state"] = qs.get("state", [""])[0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write("""<!DOCTYPE html><meta charset=utf-8>
<title>Tochka OAuth</title>
<body style='font-family:sans-serif;max-width:480px;margin:60px auto;text-align:center'>
<h1 style='color:#18a957'>✓ Готово</h1>
<p>Можно закрывать эту вкладку и вернуться в терминал.</p></body>""".encode("utf-8"))
                elif "error" in qs:
                    captured["error"] = qs.get("error", [""])[0]
                    captured["error_description"] = qs.get("error_description", [""])[0]
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"<h1>OAuth error</h1><pre>{captured}</pre>".encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

    # Always bind to 127.0.0.1 regardless of the hostname in the URL (both
    # "localhost" and "127.0.0.1" resolve here, and binding to 0.0.0.0 would be unsafe).
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_file, key_file)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    # Wait up to 5 min for the callback
    deadline = time.time() + 300
    while time.time() < deadline and "code" not in captured and "error" not in captured:
        time.sleep(0.25)
    httpd.shutdown()

    if "error" in captured:
        sys.exit(f"OAuth callback error: {captured.get('error')} — {captured.get('error_description')}")
    if "code" not in captured:
        sys.exit("OAuth callback did not arrive within 5 minutes. Retry `init --oauth`.")
    return captured["code"], captured["state"]


def cmd_init_oauth(args: argparse.Namespace) -> None:
    if not sys.stdin.isatty():
        sys.exit(
            "error: init needs a real terminal (it reads the client_id / client_secret with "
            "getpass, which requires TTY). Ask the user to run the wizard directly in their shell:\n"
            "    ! python3 .claude/skills/tochka-bank-api/scripts/tochka_client.py init --oauth"
        )
    import secrets as _secrets
    redirect_uri = getattr(args, "redirect_url", None) or "https://127.0.0.1:8443/callback"

    # Parse the redirect URL to derive host+port+path (needed for cert & server).
    parsed = urllib.parse.urlsplit(redirect_uri)
    if parsed.scheme != "https":
        sys.exit(f"error: Redirect URL must use https (got {parsed.scheme})")
    host = parsed.hostname or "localhost"
    port = parsed.port or 8443
    callback_path = parsed.path or "/callback"
    # Cert must cover localhost AND 127.0.0.1 so either form works.
    cert_hosts = sorted(set(["localhost", "127.0.0.1", host]))

    print(f"""
======================================================
  Tochka Bank API — OAuth 2.0 setup
  Redirect URL: {redirect_uri}
======================================================

1. Убедитесь, что в ЛК Точки (https://i.tochka.com/bank/services/m/integration)
   приложение зарегистрировано с ТОЧНО этим Redirect URL (HTTPS, схема strict).
   Если регистрация ещё не сделана:
     https://i.tochka.com/bank/services/m/integration/new
     • Название: любое (например, "tochka-bank-api skill")
     • Redirect URL: {redirect_uri}
     • Компания: ваше ИП/ООО
     • Принять оферту

2. Сейчас wizard спросит client_id и client_secret (ввод скрыт),
   получит токены и сохранит их в Keychain.
""")
    input("Нажмите Enter когда приложение зарегистрировано...")
    print()

    try:
        client_id = getpass.getpass("client_id: ").strip()
        client_secret = getpass.getpass("client_secret (ввод скрыт): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nОтмена.")
        sys.exit(1)
    if not client_id or not client_secret:
        sys.exit("error: client_id и client_secret обязательны")

    # Cert first (so we fail fast before hitting the API).
    print(f"\n[1/6] Проверяю локальный HTTPS-сертификат для {cert_hosts}...")
    certs = _ensure_localhost_cert(cert_hosts)
    if not certs:
        sys.exit("Не удалось получить сертификат для localhost. Установите mkcert (brew install mkcert) и повторите.")
    cert_file, key_file = certs

    # App-level token.
    print("[2/6] Получаю app-level token через client_credentials...")
    app_token = _oauth_get_app_token(client_id, client_secret, DEFAULT_OAUTH_SCOPES)

    # Consent.
    print(f"[3/6] Создаю Consent с {len(DEFAULT_OAUTH_PERMISSIONS)} разрешениями...")
    consent_id = _oauth_create_consent(app_token, DEFAULT_OAUTH_PERMISSIONS)
    print(f"       consentId = {consent_id}")

    # Build authorize URL.
    state = _secrets.token_urlsafe(16)
    auth_url = OAUTH_AUTHORIZE_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "state": state,
        "redirect_uri": redirect_uri,
        "scope": DEFAULT_OAUTH_SCOPES,
        "consent_id": consent_id,
    })

    # Start local server before opening the browser (avoid race).
    print(f"[4/6] Запускаю локальный HTTPS-сервер на {redirect_uri}...")
    print("[5/6] Открываю браузер для авторизации — подтвердите доступ в ЛК Точки.")
    print(f"       Если браузер не открылся автоматически, откройте ссылку:\n       {auth_url}\n")
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", auth_url])
        elif platform.system() == "Linux":
            subprocess.Popen(["xdg-open", auth_url])
        elif platform.system() == "Windows":
            subprocess.Popen(["cmd", "/c", "start", auth_url])
    except Exception:
        pass

    code, returned_state = _run_oauth_callback_server(cert_file, key_file, host, port, callback_path)
    if returned_state != state:
        sys.exit(f"state mismatch: expected {state}, got {returned_state} — aborting")

    # Exchange.
    print("[6/6] Обмениваю code на access_token + refresh_token...")
    tokens = _oauth_exchange_code(client_id, client_secret, code, redirect_uri, DEFAULT_OAUTH_SCOPES)
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    expires_in = int(tokens.get("expires_in", 86400))
    if not (access and refresh):
        sys.exit(f"token response missing access/refresh: {tokens}")

    # Persist everything.
    store_in_keychain(client_id, KC_OAUTH_CLIENT_ID, "Tochka OAuth client_id")
    store_in_keychain(client_secret, KC_OAUTH_CLIENT_SECRET, "Tochka OAuth client_secret")
    store_in_keychain(refresh, KC_OAUTH_REFRESH_TOKEN, "Tochka OAuth refresh_token")
    store_in_keychain(access, KC_OAUTH_ACCESS_TOKEN, "Tochka OAuth access_token")

    # Verify by calling /accounts.
    cfg = load_config()
    cfg["auth_mode"] = "oauth"
    cfg["oauth_access_expires_at"] = int(time.time()) + expires_in - 60
    cfg["oauth_consent_id"] = consent_id
    _write_config(cfg)

    print("\nПроверяю токен через GET /accounts...")
    resp = request("GET", "/open-banking/v2.0/accounts")
    accounts = resp.get("Data", {}).get("Account", [])
    if not accounts:
        print("Внимание: счетов не найдено. Проверьте разрешения в Consent.")
        return

    print(f"\nOK — OAuth настроен. Найдено счетов: {len(accounts)}\n")
    for i, a in enumerate(accounts, 1):
        print(f"  [{i}] customerCode={a.get('customerCode')}  accountId={a.get('accountId')}  {a.get('currency')}  {a.get('status')}")

    # Save defaults to config.
    default = accounts[0]
    cfg["customer_code"] = default.get("customerCode")
    cfg["default_account_id"] = default.get("accountId")
    _write_config(cfg)

    print(f"""
Сохранено в {CONFIG_FILE}:
  auth_mode          = oauth
  customer_code      = {default.get("customerCode")}
  default_account_id = {default.get("accountId")}

Теперь доступно всё: list-statement, create-invoice, send-invoice и др.
access_token будет автоматически рефрешиться за клиента.
""")


def cmd_init(args: argparse.Namespace) -> None:
    if not sys.stdin.isatty():
        suffix = " --oauth" if getattr(args, "oauth", False) else ""
        sys.exit(
            "error: init needs a real terminal (it reads the JWT with getpass, which "
            "requires TTY). Ask the user to run the wizard directly in their shell:\n"
            f"    ! python3 .claude/skills/tochka-bank-api/scripts/tochka_client.py init{suffix}"
        )
    env_label = "SANDBOX" if os.environ.get("TOCHKA_SANDBOX") == "1" else "PRODUCTION"
    print(f"""
======================================================
  Tochka Bank API — первоначальная настройка ({env_label})
======================================================

Шаг 1. В интернет-банке получите JWT-токен.

  1) Откройте https://enter.tochka.com и войдите
  2) Раздел «Интеграции и API» → «Подключить»
  3) «Сгенерировать JWT-ключ»
  4) Укажите название и срок действия (TTL)
  5) Выберите ТОЛЬКО нужные разрешения (принцип минимальных прав):
       - ReadAccountsBasic, ReadBalances      — для баланса
       - ReadStatements                        — для выписки
       - ManageInvoiceData, ReadInvoiceData    — для счетов
       - CreatePaymentForSign                  — для платёжек
       - ReadSBPData, EditSBPData              — для СБП QR
  6) Подтвердите SMS-кодом
  7) Скопируйте JWT (показывается ОДИН раз) и client_id
""")
    input("Нажмите Enter когда будет готово...")
    print()

    try:
        jwt = getpass.getpass("Шаг 2. Вставьте JWT (ввод скрыт): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nОтмена.")
        sys.exit(1)

    if not jwt:
        sys.exit("error: токен пустой")

    # Verify BEFORE storing (never persist a broken/typo'd token).
    print("\nШаг 3. Проверка токена...")
    os.environ["TOCHKA_TOKEN"] = jwt
    try:
        resp = request("GET", "/open-banking/v2.0/accounts")
    except SystemExit:
        print("\nТокен НЕ работает, сохранение отменено.")
        raise
    accounts = resp.get("Data", {}).get("Account", [])

    # Decide storage backend.
    system = platform.system()
    store_names = {"Darwin": "macOS Keychain", "Linux": "secret-tool (GNOME Keyring / KWallet)",
                   "Windows": "Windows Credential Manager"}
    store_name = store_names.get(system, "OS credential store")

    print(f"\nШаг 4. Сохранение токена...")
    use_file = getattr(args, "storage", None) == "file"

    stored_in_keychain = False
    if not use_file:
        stored_in_keychain = store_token_in_keychain(jwt)
        if stored_in_keychain:
            print(f"  Сохранено в {store_name} (service={KEYCHAIN_SERVICE}).")
        else:
            print(f"  Не удалось сохранить в {store_name} — откатываюсь на файл.")

    if not stored_in_keychain:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(CONFIG_DIR, 0o700)
        TOKEN_FILE.write_text(jwt, encoding="utf-8")
        os.chmod(TOKEN_FILE, 0o600)
        print(f"  Сохранено в файл: {TOKEN_FILE} (chmod 600)")
        print(f"  (Это менее безопасно чем {store_name} — токен лежит открытым текстом.)")

    # Show accounts
    if not accounts:
        print("\nВнимание: счетов не найдено. Возможно, у токена нет разрешения ReadAccountsBasic.")
        return

    print(f"\nOK — токен работает. Найдено счетов: {len(accounts)}\n")
    for i, a in enumerate(accounts, 1):
        print(f"  [{i}] customerCode={a.get('customerCode')}  accountId={a.get('accountId')}")
        print(f"      currency={a.get('currency')}  status={a.get('status')}  type={a.get('accountType')}")

    default = accounts[0]
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)
    CONFIG_FILE.write_text(json.dumps({
        "customer_code": default.get("customerCode"),
        "default_account_id": default.get("accountId"),
    }, indent=2), encoding="utf-8")
    os.chmod(CONFIG_FILE, 0o600)

    print(f"""
Дефолты сохранены в {CONFIG_FILE}:
  customer_code        = {default.get("customerCode")}
  default_account_id   = {default.get("accountId")}

Готово. Теперь команды клиента работают без явного TOCHKA_TOKEN — токен
читается из {store_name if stored_in_keychain else TOKEN_FILE}.
""")


def cmd_list_statement(args: argparse.Namespace) -> None:
    """Open Banking statement flow (OAuth-only on prod).

    Real flow (verified prod 2026-04-20):
      1. POST /open-banking/v2.0/statements with Data.Statement.{accountId, startDateTime, endDateTime}
         returns a statementId and status=Created
      2. GET /open-banking/v2.0/statements polls ALL statements on record — once ours
         reaches status=Ready, its Transaction[] is inlined (no separate /payments endpoint)
    """
    account_id = resolve_account_id(args.account_id)
    create_body = {
        "Data": {
            "Statement": {
                "accountId": account_id,
                "startDateTime": args.date_from,
                "endDateTime": args.date_to,
            }
        }
    }
    created = request("POST", "/open-banking/v2.0/statements", create_body)
    statement = created.get("Data", {}).get("Statement") or created.get("Data", {})
    statement_id = statement.get("statementId")
    if not statement_id:
        sys.exit(f"unexpected create-statement response: {json.dumps(created, ensure_ascii=False)}")

    # Poll: fetch the full statements list and find ours by statementId.
    for attempt in range(60):
        resp = request("GET", "/open-banking/v2.0/statements")
        stmts = resp.get("Data", {}).get("Statement", [])
        ours = next((s for s in stmts if s.get("statementId") == statement_id), None)
        if ours and ours.get("status") in ("Ready", "Completed", "Executed"):
            print(json.dumps(ours, indent=2, ensure_ascii=False))
            return
        time.sleep(1)
    sys.exit(f"statement {statement_id} not ready after 60s. Last list response: {json.dumps(resp, ensure_ascii=False)[:500]}")


def _invoice_get_pdf(customer_code: str, document_id: str, timeout: int = 90) -> bytes:
    """GET /invoice/v1.0/bills/{cc}/{id}/file — verified prod path, ~30s first render."""
    url = base_url() + f"/invoice/v1.0/bills/{customer_code}/{document_id}/file"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token()}")
    if auth_mode() == "oauth":
        req.add_header("CustomerCode", customer_code)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def cmd_create_invoice(args: argparse.Namespace) -> None:
    """Create invoice (OAuth-gated on prod). Auto-downloads PDF when --save-pdf set."""
    customer_code = resolve_customer_code(args.customer_code)
    body: dict[str, Any] = {
        "Data": {
            "customerCode": customer_code,
            "accountId": resolve_account_id(args.account_id),
            "documentDate": args.document_date,
            "documentNumber": args.document_number,
            "SecondSide": {
                "taxCode": args.buyer_inn,
                "type": "company" if args.buyer_kpp else "ip",
                "legalName": args.buyer_name,
            },
            "Content": {
                "Invoice": {
                    "number": args.document_number,
                    "totalAmount": args.amount,
                    "Positions": [
                        {
                            "name": args.purpose,
                            "price": args.amount,
                            "quantity": 1,
                            "totalAmount": args.amount,
                            "unitCode": args.unit_code,
                            "ndsKind": args.nds_kind,
                        }
                    ],
                }
            },
        }
    }
    if args.buyer_kpp:
        body["Data"]["SecondSide"]["KPP"] = args.buyer_kpp
    if args.due_date:
        body["Data"]["paymentExpirationDate"] = args.due_date

    resp = request("POST", "/invoice/v2.0/bills", body)
    document_id = resp.get("Data", {}).get("documentId")

    if args.format == "json":
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
        if args.format == "id" and document_id:
            print(document_id)

    if not document_id:
        return

    # Auto-download PDF if requested.
    if args.save_pdf:
        target_dir = Path(args.save_pdf).expanduser()
        target_dir.mkdir(parents=True, exist_ok=True)
        # Render date as DD.MM.YYYY from documentDate (YYYY-MM-DD).
        try:
            y, m, d = args.document_date.split("-")
            date_ru = f"{d}.{m}.{y}"
        except ValueError:
            date_ru = args.document_date
        filename = f"Счёт №{args.document_number} от {date_ru}.pdf"
        pdf_path = target_dir / filename
        print(f"\nDownloading PDF → {pdf_path} ...", file=sys.stderr)
        pdf_bytes = _invoice_get_pdf(customer_code, document_id)
        pdf_path.write_bytes(pdf_bytes)
        print(f"Saved {len(pdf_bytes)} bytes.", file=sys.stderr)
        meta_path = _save_meta(pdf_path, {
            "documentId": document_id,
            "kind": "invoice",
            "customerCode": customer_code,
            "documentNumber": args.document_number,
            "documentDate": args.document_date,
            "amount": args.amount,
            "ndsKind": args.nds_kind,
            "buyer": {
                "taxCode": args.buyer_inn,
                "kpp": args.buyer_kpp,
                "name": args.buyer_name,
            },
        })
        print(f"Saved meta → {meta_path}", file=sys.stderr)


def cmd_send_invoice(args: argparse.Namespace) -> None:
    # Swagger v1.90.4-stable documents the path as `/invoice/v1.0/.../email`.
    # The earlier v2.0 `/send-to-email` suffix was inferred and returns 404.
    customer_code = resolve_customer_code(getattr(args, "customer_code", None))
    resp = request(
        "POST",
        f"/invoice/v1.0/bills/{customer_code}/{args.document_id}/email",
        {"Data": {"email": args.email}},
    )
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def _pdf_get(path: str, customer_code: str, timeout: int = 90) -> bytes:
    """Fetch a binary (PDF) from an authenticated endpoint. Used for invoice + closing-doc files."""
    url = base_url() + path
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token()}")
    if auth_mode() == "oauth":
        req.add_header("CustomerCode", customer_code)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _save_pdf(pdf_bytes: bytes, target_dir: str, doc_kind: str, number: str, date_iso: str) -> Path:
    """Write PDF with a Russian-style filename: '<doc_kind> №<n> от DD.MM.YYYY.pdf'."""
    out_dir = Path(target_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        y, m, d = date_iso.split("-")
        date_ru = f"{d}.{m}.{y}"
    except ValueError:
        date_ru = date_iso
    filename = f"{doc_kind} №{number} от {date_ru}.pdf"
    p = out_dir / filename
    p.write_bytes(pdf_bytes)
    return p


def _save_meta(pdf_path: Path, payload: dict[str, Any]) -> Path:
    """Write a JSON sidecar next to PDF — same basename, .json extension.

    Tochka has no GET-list endpoint for invoices/closing-docs, so we cache the
    `documentId` (and minimal context) on disk at creation time. Without this
    sidecar, finding a document later requires manually opening it in ЛК Точки
    to copy the UUID from the URL.
    """
    payload = {**payload, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    meta_path = pdf_path.with_suffix(".json")
    meta_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return meta_path


def _closing_doc_content(args: argparse.Namespace) -> dict:
    """Build the Content union object based on --kind."""
    position = {
        "name": args.purpose,
        "price": args.amount,
        "quantity": 1,
        "totalAmount": args.amount,
        "unitCode": args.unit_code,
        "ndsKind": args.nds_kind,
    }
    block = {
        "date": args.document_date,
        "number": args.document_number,
        "totalAmount": args.amount,
        "Positions": [position],
    }
    # Discriminator — one of Act / PackingList / Invoicef / Upd.
    key_map = {
        "act": "Act",
        "packing-list": "PackingList",
        "invoicef": "Invoicef",
        "upd": "Upd",
    }
    return {key_map[args.kind]: block}


def cmd_create_closing_doc(args: argparse.Namespace) -> None:
    """Create a closing document (act/УПД/ТОРГ-12/счёт-фактура) via /invoice/v1.0/closing-documents.
    SecondSide uses v1.0 lowercase field names (kpp, secondSideName) — NOT the v2.0 invoice shape
    (KPP, legalName). Otherwise Tochka silently drops the fields → buyer KPP missing → ЭДО signing
    fails with "Проверьте ИНН или КПП контрагента". Optional --parent-invoice-id links to an invoice."""
    customer_code = resolve_customer_code(args.customer_code)
    body: dict[str, Any] = {
        "Data": {
            "customerCode": customer_code,
            "accountId": resolve_account_id(args.account_id),
            "SecondSide": {
                "taxCode": args.buyer_inn,
                "type": "company" if args.buyer_kpp else "ip",
                "secondSideName": args.buyer_name,
            },
            "Content": _closing_doc_content(args),
        }
    }
    if args.buyer_kpp:
        body["Data"]["SecondSide"]["kpp"] = args.buyer_kpp
    if args.parent_invoice_id:
        body["Data"]["documentId"] = args.parent_invoice_id

    resp = request("POST", "/invoice/v1.0/closing-documents", body)
    document_id = resp.get("Data", {}).get("documentId")

    if args.format == "json":
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
        if args.format == "id" and document_id:
            print(document_id)

    if document_id and args.save_pdf:
        kind_label = {
            "act": "Акт",
            "packing-list": "Накладная",
            "invoicef": "Счёт-фактура",
            "upd": "УПД",
        }[args.kind]
        pdf_bytes = _pdf_get(
            f"/invoice/v1.0/closing-documents/{customer_code}/{document_id}/file",
            customer_code,
        )
        p = _save_pdf(pdf_bytes, args.save_pdf, kind_label, args.document_number, args.document_date)
        print(f"Saved PDF → {p} ({len(pdf_bytes)} bytes)", file=sys.stderr)
        meta_path = _save_meta(p, {
            "documentId": document_id,
            "kind": args.kind,
            "customerCode": customer_code,
            "documentNumber": args.document_number,
            "documentDate": args.document_date,
            "amount": args.amount,
            "ndsKind": args.nds_kind,
            "parentInvoiceId": args.parent_invoice_id,
            "buyer": {
                "taxCode": args.buyer_inn,
                "kpp": args.buyer_kpp,
                "name": args.buyer_name,
            },
        })
        print(f"Saved meta → {meta_path}", file=sys.stderr)


def cmd_get_closing_doc(args: argparse.Namespace) -> None:
    """Download a closing-doc PDF by documentId."""
    customer_code = resolve_customer_code(args.customer_code)
    pdf_bytes = _pdf_get(
        f"/invoice/v1.0/closing-documents/{customer_code}/{args.document_id}/file",
        customer_code,
    )
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pdf_bytes)
    print(f"Saved {len(pdf_bytes)} bytes → {out}", file=sys.stderr)


def cmd_send_closing_doc(args: argparse.Namespace) -> None:
    customer_code = resolve_customer_code(args.customer_code)
    resp = request(
        "POST",
        f"/invoice/v1.0/closing-documents/{customer_code}/{args.document_id}/email",
        {"Data": {"email": args.email}},
    )
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_delete_closing_doc(args: argparse.Namespace) -> None:
    customer_code = resolve_customer_code(args.customer_code)
    resp = request(
        "DELETE",
        f"/invoice/v1.0/closing-documents/{customer_code}/{args.document_id}",
    )
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_get_balance(args: argparse.Namespace) -> None:
    """Current balance. No --account-id → all accounts; with id → one account."""
    if args.account_id:
        encoded = urllib.parse.quote(args.account_id, safe="")
        resp = request("GET", f"/open-banking/v1.0/accounts/{encoded}/balances")
    else:
        resp = request("GET", "/open-banking/v1.0/balances")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_list_registry(args: argparse.Namespace) -> None:
    """Daily acquiring settlement registry."""
    params = {
        "customerCode": resolve_customer_code(args.customer_code),
        "date": args.date,
    }
    if args.merchant_id:
        params["merchantId"] = args.merchant_id
    if args.payment_id:
        params["paymentId"] = args.payment_id
    resp = request("GET", f"/acquiring/v1.0/registry?{urllib.parse.urlencode(params)}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_list_consents(_: argparse.Namespace) -> None:
    """List all OAuth consents visible to the current token (OAuth-only)."""
    resp = request("GET", "/consent/v1.0/consents")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_get_consent(args: argparse.Namespace) -> None:
    resp = request("GET", f"/consent/v1.0/consents/{args.consent_id}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def _resolve_client_id(explicit: str | None) -> str:
    if explicit:
        return explicit
    # OAuth mode: client_id saved in keychain during init --oauth.
    cid = read_from_keychain(KC_OAUTH_CLIENT_ID)
    if cid:
        return cid
    # Personal JWT: user has to provide it explicitly (shown once in ЛК).
    cfg = load_config()
    cid = cfg.get("jwt_client_id")
    if cid:
        return cid
    sys.exit(
        "error: --client-id required. For OAuth it's stored automatically after `init --oauth`. "
        "For personal JWT pass --client-id or save it to config manually."
    )


WEBHOOK_TYPES = [
    "incomingPayment",
    "outgoingPayment",
    "incomingSbpPayment",
    "acquiringInternetPayment",
    "incomingSbpB2BPayment",
]


def cmd_register_webhook(args: argparse.Namespace) -> None:
    """PUT /webhook/v1.0/{client_id} — register or replace webhook config."""
    client_id = _resolve_client_id(args.oauth_client_id)
    events = args.events or WEBHOOK_TYPES
    body = {"webhooksList": events, "url": args.url}
    resp = request("PUT", f"/webhook/v1.0/{client_id}", body)
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_list_webhooks(args: argparse.Namespace) -> None:
    client_id = _resolve_client_id(args.oauth_client_id)
    resp = request("GET", f"/webhook/v1.0/{client_id}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_delete_webhook(args: argparse.Namespace) -> None:
    client_id = _resolve_client_id(args.oauth_client_id)
    resp = request("DELETE", f"/webhook/v1.0/{client_id}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_test_webhook(args: argparse.Namespace) -> None:
    """Ask Tochka to fire a synthetic webhook event to the registered URL."""
    client_id = _resolve_client_id(args.oauth_client_id)
    body = {"webhookType": args.event} if args.event else {}
    resp = request("POST", f"/webhook/v1.0/{client_id}/test_send", body or None)
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_create_payment_link(args: argparse.Namespace) -> None:
    """Create an internet-acquiring payment link. `amount` is in rubles (float, unlike SBP QR)."""
    body: dict[str, Any] = {
        "Data": {
            "customerCode": resolve_customer_code(args.customer_code),
            "amount": args.amount,
            "purpose": args.purpose,
            "paymentMode": args.payment_mode,
        }
    }
    if args.merchant_id:
        body["Data"]["merchantId"] = args.merchant_id
    if args.redirect_url:
        body["Data"]["redirectUrl"] = args.redirect_url
    if args.fail_redirect_url:
        body["Data"]["failRedirectUrl"] = args.fail_redirect_url
    if args.ttl is not None:
        body["Data"]["ttl"] = args.ttl
    if args.pre_authorization:
        body["Data"]["preAuthorization"] = True
    if args.save_card:
        body["Data"]["saveCard"] = True
    if args.payment_link_id:
        body["Data"]["paymentLinkId"] = args.payment_link_id
    resp = request("POST", "/acquiring/v1.0/payments", body)

    if args.format == "json":
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
        operation = resp.get("Data", {}).get("Operation", {})
        if args.format == "id":
            op_id = operation.get("operationId")
            if op_id:
                print(op_id)
        elif args.format == "url":
            url = operation.get("paymentLink")
            if url:
                print(url)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Interactive first-time setup (save JWT, validate, show accounts)")
    p_init.add_argument(
        "--oauth",
        action="store_true",
        help="Запустить OAuth 2.0 flow (регистрация приложения + локальный HTTPS-callback) вместо JWT",
    )
    p_init.add_argument(
        "--redirect-url",
        default="https://127.0.0.1:8443/callback",
        help="Redirect URL ровно как зарегистрирован в ЛК Точки. Дефолт https://127.0.0.1:8443/callback (Точка отвергает 'localhost' — только IP или полноценный домен).",
    )
    p_init.add_argument(
        "--storage",
        choices=["keychain", "file"],
        default="keychain",
        help="Где хранить JWT-токен. keychain (default) — OS credential store; file — ~/.config/tochka-bank-api/token (менее безопасно). Игнорируется при --oauth (всегда keychain).",
    )

    def _dispatch_init(a):
        if getattr(a, "oauth", False):
            cmd_init_oauth(a)
        else:
            cmd_init(a)
    p_init.set_defaults(func=_dispatch_init)
    sub.add_parser("list-accounts", help="List accounts").set_defaults(func=cmd_list_accounts)
    sub.add_parser("config", help="Show saved defaults (customer_code, default_account_id)").set_defaults(func=cmd_config)

    p_inc = sub.add_parser("list-incoming", help="Incoming acquiring/SBP payments (works with personal JWT)")
    p_inc.add_argument("--customer-code", default=None, help="Defaults to value saved by `init`")
    p_inc.add_argument("--status", default=None, help="Filter by status, e.g. APPROVED, REJECTED")
    p_inc.set_defaults(func=cmd_list_incoming)

    p_fs = sub.add_parser("list-for-sign", help="Outgoing payment orders currently in 'На подпись'")
    p_fs.add_argument("--customer-code", default=None, help="Defaults to value saved by `init`")
    p_fs.add_argument("--status", default=None, help="Filter by status")
    p_fs.set_defaults(func=cmd_list_for_sign)

    p_stmt = sub.add_parser("list-statement", help="Full bank statement via Open Banking (prod: OAuth-only, 501 with personal JWT)")
    p_stmt.add_argument("--account-id", default=None, help="Defaults to value saved by `init`")
    p_stmt.add_argument("--from", dest="date_from", required=True, help="YYYY-MM-DD")
    p_stmt.add_argument("--to", dest="date_to", required=True, help="YYYY-MM-DD")
    p_stmt.set_defaults(func=cmd_list_statement)

    p_inv = sub.add_parser("create-invoice", help="Create a new invoice (prod: OAuth-only, 501 with personal JWT)")
    p_inv.add_argument("--customer-code", default=None, help="Defaults to value saved by `init`")
    p_inv.add_argument("--account-id", default=None, help="Defaults to value saved by `init`")
    p_inv.add_argument("--amount", type=float, required=True)
    p_inv.add_argument("--purpose", required=True, help="Item / service description")
    p_inv.add_argument("--buyer-inn", required=True)
    p_inv.add_argument("--buyer-name", required=True)
    p_inv.add_argument("--buyer-kpp", default=None, help="Required for legal entities (type=company); omit for ИП (type=ip, taxCode=12-digit ИНН)")
    p_inv.add_argument("--document-date", default=time.strftime("%Y-%m-%d"))
    p_inv.add_argument("--document-number", required=True,
                       help="Per-customer sequential number. Look up the highest N in "
                            "ru/customers/<slug>/payments/ and pass N+1. No auto-default — "
                            "choosing the number is a deliberate ledger decision.")
    p_inv.add_argument("--due-date", default=None, help="YYYY-MM-DD payment deadline")
    p_inv.add_argument(
        "--nds-kind",
        default="without_nds",
        choices=["without_nds", "nds_0", "nds_5", "nds_7", "nds_10", "nds_22"],
        help="НДС (ставки 2026: 22%% заменил 20%%)",
    )
    p_inv.add_argument(
        "--unit-code",
        default="шт.",
        choices=VALID_UNIT_CODES,
        metavar="UNIT",
        help="Единица измерения. Закрытый whitelist Точки (нет 'мес.' / 'год.' — "
             "для подписок используй 'услуга.' или 'шт.'). Допустимо: "
             + ", ".join(VALID_UNIT_CODES),
    )
    p_inv.add_argument(
        "--save-pdf",
        default=None,
        metavar="DIR",
        help="Сразу после создания скачать PDF в папку DIR. Имя файла: 'Счёт N<номер> от DD.MM.YYYY.pdf'",
    )
    p_inv.add_argument(
        "--format",
        choices=["json", "id"],
        default="json",
        help="json (default) prints the full envelope on stdout; id prints only documentId on stdout and the envelope on stderr.",
    )
    p_inv.set_defaults(func=cmd_create_invoice)

    p_send = sub.add_parser("send-invoice", help="Email an invoice (POST /invoice/v1.0/bills/{cc}/{id}/email)")
    p_send.add_argument("--document-id", required=True, help="documentId from create-invoice response")
    p_send.add_argument("--email", required=True)
    p_send.add_argument("--customer-code", default=None)
    p_send.set_defaults(func=cmd_send_invoice)

    # --- Closing documents (акты / УПД / накладные / счета-фактуры) ---
    p_cd = sub.add_parser("create-closing-doc", help="Create a closing document (act/УПД/ТОРГ-12/счёт-фактура)")
    p_cd.add_argument("--kind", required=True, choices=["act", "packing-list", "invoicef", "upd"],
                      help="Тип закрывающего документа")
    p_cd.add_argument("--customer-code", default=None)
    p_cd.add_argument("--account-id", default=None)
    p_cd.add_argument("--amount", type=float, required=True)
    p_cd.add_argument("--purpose", required=True, help="Наименование позиции")
    p_cd.add_argument("--buyer-inn", required=True)
    p_cd.add_argument("--buyer-name", required=True)
    p_cd.add_argument("--buyer-kpp", default=None, help="Для юр-лица (type=company)")
    p_cd.add_argument("--document-date", default=time.strftime("%Y-%m-%d"))
    p_cd.add_argument("--document-number", required=True)
    p_cd.add_argument("--parent-invoice-id", default=None,
                      help="documentId родительского счёта-оферты (опц.) — свяжет документы в ЛК")
    p_cd.add_argument("--nds-kind", default="without_nds",
                      choices=["without_nds", "nds_0", "nds_5", "nds_7", "nds_10", "nds_22"])
    p_cd.add_argument("--unit-code", default="шт.", choices=VALID_UNIT_CODES, metavar="UNIT",
                      help="Единица измерения. Закрытый whitelist Точки (нет 'мес.' / 'год.' — "
                           "для подписок используй 'услуга.' или 'шт.'). Допустимо: "
                           + ", ".join(VALID_UNIT_CODES))
    p_cd.add_argument("--save-pdf", default=None, metavar="DIR",
                      help="Сразу скачать PDF в папку DIR. Имя: '<Тип> №<номер> от DD.MM.YYYY.pdf'")
    p_cd.add_argument(
        "--format",
        choices=["json", "id"],
        default="json",
        help="json (default) prints the full envelope on stdout; id prints only documentId on stdout and the envelope on stderr.",
    )
    p_cd.set_defaults(func=cmd_create_closing_doc)

    p_cd_get = sub.add_parser("get-closing-doc", help="Download closing-doc PDF by documentId")
    p_cd_get.add_argument("--customer-code", default=None)
    p_cd_get.add_argument("--document-id", required=True)
    p_cd_get.add_argument("--out", required=True, help="Path for the PDF file")
    p_cd_get.set_defaults(func=cmd_get_closing_doc)

    p_cd_send = sub.add_parser("send-closing-doc", help="Email a closing document")
    p_cd_send.add_argument("--customer-code", default=None)
    p_cd_send.add_argument("--document-id", required=True)
    p_cd_send.add_argument("--email", required=True)
    p_cd_send.set_defaults(func=cmd_send_closing_doc)

    p_cd_del = sub.add_parser("delete-closing-doc", help="Delete a closing document")
    p_cd_del.add_argument("--customer-code", default=None)
    p_cd_del.add_argument("--document-id", required=True)
    p_cd_del.set_defaults(func=cmd_delete_closing_doc)

    # --- Balance ---
    p_bal = sub.add_parser("get-balance", help="Account balance (works with personal JWT + ReadBalances)")
    p_bal.add_argument("--account-id", default=None,
                       help="Omit to list all accounts' balances in one call")
    p_bal.set_defaults(func=cmd_get_balance)

    # --- Acquiring daily registry ---
    p_reg = sub.add_parser("list-registry", help="Acquiring daily settlement registry (reconciliation)")
    p_reg.add_argument("--customer-code", default=None)
    p_reg.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_reg.add_argument("--merchant-id", default=None)
    p_reg.add_argument("--payment-id", default=None, help="Drill-down to a single payment")
    p_reg.set_defaults(func=cmd_list_registry)

    # --- Consents (OAuth introspection) ---
    p_cons = sub.add_parser("list-consents", help="List OAuth consents (diagnose 403 / scope issues)")
    p_cons.set_defaults(func=cmd_list_consents)

    p_cons_get = sub.add_parser("get-consent", help="Details of a single consent by consentId")
    p_cons_get.add_argument("--consent-id", required=True, dest="consent_id")
    p_cons_get.set_defaults(func=cmd_get_consent)

    # --- Webhooks ---
    p_wh_reg = sub.add_parser("register-webhook",
                              help="Register/replace webhook URL + subscribed events (PUT /webhook/v1.0/{client_id})")
    p_wh_reg.add_argument("--oauth-client-id", default=None,
                          help="OAuth app client_id (not to be confused with customerCode/customer-code). Auto-resolved if init --oauth ran; JWT users pass their ЛК client_id here.")
    p_wh_reg.add_argument("--url", required=True, help="HTTPS endpoint that Tochka will call")
    p_wh_reg.add_argument("--events", nargs="+", choices=WEBHOOK_TYPES, default=None,
                          help=f"Subset of events to subscribe to. Default: all ({', '.join(WEBHOOK_TYPES)})")
    p_wh_reg.set_defaults(func=cmd_register_webhook)

    p_wh_list = sub.add_parser("list-webhooks", help="Get current webhook config")
    p_wh_list.add_argument("--oauth-client-id", default=None,
                           help="OAuth app client_id (not to be confused with customerCode/customer-code).")
    p_wh_list.set_defaults(func=cmd_list_webhooks)

    p_wh_del = sub.add_parser("delete-webhook", help="Delete webhook config")
    p_wh_del.add_argument("--oauth-client-id", default=None,
                          help="OAuth app client_id (not to be confused with customerCode/customer-code).")
    p_wh_del.set_defaults(func=cmd_delete_webhook)

    p_wh_test = sub.add_parser("test-webhook", help="Ask Tochka to fire a synthetic webhook event")
    p_wh_test.add_argument("--oauth-client-id", default=None,
                           help="OAuth app client_id (not to be confused with customerCode/customer-code).")
    p_wh_test.add_argument("--event", choices=WEBHOOK_TYPES, default=None,
                           help="Which event type to simulate; omit to let server choose")
    p_wh_test.set_defaults(func=cmd_test_webhook)

    # --- Payment links (internet acquiring) ---
    p_pl = sub.add_parser("create-payment-link",
                          help="Create a payment link (POST /acquiring/v1.0/payments). Requires MakeAcquiringOperation + existing merchantId")
    p_pl.add_argument("--customer-code", default=None)
    p_pl.add_argument("--amount", type=float, required=True, help="In rubles (unlike SBP QR where amount is in kopecks)")
    p_pl.add_argument("--purpose", required=True)
    p_pl.add_argument("--payment-mode", nargs="+", default=["sbp", "card"],
                      help="Allowed payment methods. Default: sbp card")
    p_pl.add_argument("--merchant-id", default=None)
    p_pl.add_argument("--redirect-url", default=None)
    p_pl.add_argument("--fail-redirect-url", default=None)
    p_pl.add_argument("--ttl", type=int, default=None, help="Lifetime in minutes (1–44640; default 10080 = 7 days)")
    p_pl.add_argument("--pre-authorization", action="store_true",
                      help="Two-stage: funds held, requires /capture to settle")
    p_pl.add_argument("--save-card", action="store_true", help="Save card for later (subscriptions)")
    p_pl.add_argument("--payment-link-id", default=None, help="Your external reference ID")
    p_pl.add_argument(
        "--format",
        choices=["json", "id", "url"],
        default="json",
        help="json (default) prints the full envelope on stdout; id prints only Data.Operation.operationId; url prints only Data.Operation.paymentLink. id/url send the envelope to stderr.",
    )
    p_pl.set_defaults(func=cmd_create_payment_link)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
