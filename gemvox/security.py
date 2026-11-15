"""
Security & Encrypted Credential Storage for Gemvox.

Uses Windows Data Protection API (DPAPI) via CryptProtectData / CryptUnprotectData
to bind stored API keys to the current Windows user account and machine.
"""

import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys

# Application-specific DPAPI entropy
_DPAPI_ENTROPY = b"Gemvox-DPAPI-Credentials-v1"
_CRYPTPROTECT_UI_FORBIDDEN = 0x01

# Honeypot decoy key written into config.json so exported/shared configs or
# casual inspection of config.json never expose the real credential.
DECOY_API_KEY = "AIzaSyD9xK2mP7qR4tV8wZ1cF5hJ3nL6pQ0sU9x"
_KNOWN_DECOYS = frozenset({DECOY_API_KEY})


def is_decoy_api_key(value: str) -> bool:
    """Return True if value is a known honeypot decoy placeholder."""
    return (value or "").strip() in _KNOWN_DECOYS


if sys.platform == "win32":
    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]


    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32


    def _make_blob(data: bytes) -> tuple[_DATA_BLOB, ctypes.Array]:
        buf = ctypes.create_string_buffer(data, len(data))
        blob = _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        return blob, buf


    def _dpapi_protect(plaintext_bytes: bytes) -> bytes:
        in_blob, _in_buf = _make_blob(plaintext_bytes)
        ent_blob, _ent_buf = _make_blob(_DPAPI_ENTROPY)
        out_blob = _DATA_BLOB()

        ok = _crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            "Gemvox API Key",
            ctypes.byref(ent_blob),
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(out_blob),
        )
        if not ok:
            raise OSError(f"CryptProtectData failed with error {ctypes.GetLastError()}")
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            _kernel32.LocalFree(out_blob.pbData)


    def _dpapi_unprotect(cipher_bytes: bytes) -> bytes:
        in_blob, _in_buf = _make_blob(cipher_bytes)
        ent_blob, _ent_buf = _make_blob(_DPAPI_ENTROPY)
        out_blob = _DATA_BLOB()

        ok = _crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            ctypes.byref(ent_blob),
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(out_blob),
        )
        if not ok:
            raise OSError(f"CryptUnprotectData failed with error {ctypes.GetLastError()}")
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            _kernel32.LocalFree(out_blob.pbData)
else:
    def _dpapi_protect(plaintext_bytes: bytes) -> bytes:
        # Non-Windows fallback: XOR-obfuscate with entropy (DPAPI is Windows-only)
        key = _DPAPI_ENTROPY
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext_bytes))


    def _dpapi_unprotect(cipher_bytes: bytes) -> bytes:
        key = _DPAPI_ENTROPY
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(cipher_bytes))


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a plaintext secret string and return a base64-encoded payload."""
    clean = (plaintext or "").strip()
    if not clean:
        return ""
    protected = _dpapi_protect(clean.encode("utf-8"))
    return base64.b64encode(protected).decode("ascii")


def decrypt_secret(payload_b64: str) -> str:
    """Decrypt a base64-encoded DPAPI payload back into plaintext."""
    clean = (payload_b64 or "").strip()
    if not clean:
        return ""
    raw = base64.b64decode(clean.encode("ascii"))
    plain_bytes = _dpapi_unprotect(raw)
    return plain_bytes.decode("utf-8").strip()


def save_encrypted_api_key(secrets_file: Path, api_key: str) -> bool:
    """Encrypt and atomically persist the API key into a separate secrets file."""
    clean = (api_key or "").strip()
    if not clean or is_decoy_api_key(clean):
        return clear_encrypted_api_key(secrets_file)

    try:
        secrets_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "protection": "dpapi" if sys.platform == "win32" else "obfuscated",
            "gemini_api_key": encrypt_secret(clean),
        }
        tmp_file = secrets_file.with_suffix(".dat.tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_file, secrets_file)
        return True
    except Exception:
        return False


def load_encrypted_api_key(secrets_file: Path) -> str:
    """Load and decrypt the API key from the separate secrets file."""
    if not secrets_file.is_file():
        return ""
    try:
        raw_text = secrets_file.read_bytes().decode("utf-8", errors="replace")
        payload = json.loads(raw_text)
        if not isinstance(payload, dict):
            return ""
        enc = str(payload.get("gemini_api_key", "")).strip()
        if not enc:
            return ""
        return decrypt_secret(enc)
    except Exception:
        return ""


def clear_encrypted_api_key(secrets_file: Path) -> bool:
    """Remove any stored encrypted API key from disk."""
    try:
        if secrets_file.is_file():
            secrets_file.unlink()
        return True
    except Exception:
        return False
