#!/usr/bin/env python3
"""Preflight checks. Run before every deploy. Exit 1 on any failure."""
import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ERRORS: list[str] = []
WARNINGS: list[str] = []

# Load .env before any env var checks
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def fail(msg: str) -> None:
    ERRORS.append(f"  FAIL  {msg}")


def warn(msg: str) -> None:
    WARNINGS.append(f"  WARN  {msg}")


def ok(msg: str) -> None:
    print(f"  OK    {msg}")


# ── 1. Syntax check all .py files ──────────────────────────────────────────
print("\n[1] Syntax check")
for path in ROOT.rglob("*.py"):
    if any(p in path.parts for p in (".venv", "venv", "__pycache__")):
        continue
    try:
        ast.parse(path.read_text())
        ok(str(path.relative_to(ROOT)))
    except SyntaxError as e:
        fail(f"{path.relative_to(ROOT)}: {e}")

# ── 2. Dependency conflict check ───────────────────────────────────────────
print("\n[2] Dependency conflict check")
result = subprocess.run(
    [sys.executable, "-m", "pip", "check"],
    capture_output=True, text=True,
)
if result.returncode == 0:
    ok("No dependency conflicts")
else:
    fail(f"pip check failed:\n{result.stdout}{result.stderr}")

# ── 3. Key imports resolve ─────────────────────────────────────────────────
print("\n[3] Key imports")
KEY_IMPORTS = [
    "google.adk.agents",
    "google.adk.runners",
    "google.adk.sessions",
    "google.genai.types",
    "google.cloud.discoveryengine_v1",
]
for mod in KEY_IMPORTS:
    try:
        importlib.import_module(mod)
        ok(mod)
    except ImportError as e:
        fail(f"{mod}: {e}")

# ── 4. Config module loads without error ───────────────────────────────────
print("\n[4] Config load")
try:
    import config as _cfg
    ok("config.py loaded")
except Exception as e:
    fail(f"config.py: {e}")

# ── 5. Required env vars ───────────────────────────────────────────────────
print("\n[5] Required env vars")
try:
    import config as _cfg
    for var in _cfg.REQUIRED_ENV_VARS:
        val = os.environ.get(var, "")
        if val:
            ok(f"{var} = {'*' * min(len(val), 4)}...")
        else:
            fail(f"{var} is not set or empty")
except Exception:
    fail("Could not load config.REQUIRED_ENV_VARS")

# ── 6. No deprecated model names ──────────────────────────────────────────
print("\n[6] Model name staleness check")
DEPRECATED_MODELS = [
    "gemini-pro",         # deprecated in favor of gemini-1.5-pro
    "gemini-ultra",
    "text-bison",
    "chat-bison",
    "codechat-bison",
    "gemini-1.0-pro",
]
py_and_yaml = list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.yaml")) + list(ROOT.rglob("*.yml"))
for path in py_and_yaml:
    if any(p in path.parts for p in (".venv", "venv", "__pycache__")):
        continue
    if path.name == "preflight.py":  # skip self — DEPRECATED_MODELS list would self-match
        continue
    content = path.read_text(errors="ignore")
    for model in DEPRECATED_MODELS:
        if model in content:
            fail(f"{path.relative_to(ROOT)}: contains deprecated model '{model}'")
ok("No deprecated model names found") if not ERRORS else None

# ── 7. No clients instantiated at import time ─────────────────────────────
print("\n[7] Lazy-init check (no top-level client instantiation)")
BANNED_PATTERNS = [
    "SearchServiceClient()",
    "Runner(",
    "InMemorySessionService()",
    "aiplatform.init(",
]
for path in ROOT.rglob("*.py"):
    if any(p in path.parts for p in (".venv", "venv", "__pycache__", "preflight")):
        continue
    lines = path.read_text(errors="ignore").splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Only flag if at module level (no indentation = not inside a function/class)
        if not line.startswith(" ") and not line.startswith("\t"):
            for pat in BANNED_PATTERNS:
                if pat in line:
                    fail(f"{path.relative_to(ROOT)}:{i} — top-level instantiation: {stripped[:80]}")
ok("No top-level client instantiation detected")

# ── 8. Ignore files exist and cover heavyweight artifacts ─────────────────
print("\n[8] Ignore files")
for fname in [".gcloudignore", ".dockerignore"]:
    fpath = ROOT / fname
    if not fpath.exists():
        fail(f"{fname} missing")
        continue
    content = fpath.read_text()
    for pattern in [".venv", "__pycache__", ".env", "*.json"]:
        if pattern not in content:
            warn(f"{fname} does not exclude '{pattern}'")
    ok(f"{fname} present")

# ── 9. Live env var check (optional — skipped if ADK not installed) ────────
print("\n[9] Live GCP connectivity (best-effort)")
try:
    import google.auth
    creds, project = google.auth.default()
    if project:
        ok(f"google.auth.default() resolved project: {project}")
    else:
        warn("google.auth.default() returned no project — check ADC setup")
except Exception as e:
    warn(f"Could not verify GCP credentials: {e}")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if WARNINGS:
    print("WARNINGS:")
    for w in WARNINGS:
        print(w)

if ERRORS:
    print("\nPREFLIGHT FAILED:")
    for e in ERRORS:
        print(e)
    print("\nDo NOT deploy. Fix all failures above.\n")
    sys.exit(1)
else:
    print("PREFLIGHT PASSED. Safe to deploy.\n")
    sys.exit(0)
