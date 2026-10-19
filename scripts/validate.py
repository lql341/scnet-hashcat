#!/usr/bin/env python3
"""Validate packaging invariants without dependencies or network access."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
failures = []
version = (ROOT / "VERSION").read_text().strip()
if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
    failures.append("invalid VERSION")
for name in ("README.md", "README_CN.md", "CHANGELOG.md"):
    if version not in (ROOT / name).read_text(encoding="utf-8"):
        failures.append(name + " does not include the release version")
for path in ROOT.rglob("*.md"):
    if ".git" in path.parts:
        continue
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if "://" not in target and not target.startswith("#"):
            if not (path.parent / target.split("#")[0]).exists():
                failures.append(str(path.relative_to(ROOT)) + ": broken link " + target)
for path in (ROOT / "scripts").rglob("*.py"):
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path), feature_version=(3, 8))
for path in list((ROOT / "scripts").rglob("*.sh")) + [ROOT / "scripts/hc"]:
    if b"\r" in path.read_bytes():
        failures.append(str(path.relative_to(ROOT)) + ": CRLF is unsafe for remote Bash")
manifest = json.loads((ROOT / "scripts/vendor-manifest.json").read_text())
for name, info in manifest["files"].items():
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != info["sha256"]:
        failures.append("vendored helper drift: " + name)
profile = (ROOT / "clusters/kseshell.conf").read_text(encoding="utf-8")
if 'HASHCAT_MODULE="hashcat/7.1.2-dtk"' in profile:
    failures.append("R1 profile still uses the pre-signature hashcat module name")
match = re.search(r'^STACK_PROFILE="([^"]+)"$', profile, re.MULTILINE)
if not match:
    failures.append("cluster profile must select a stack profile")
else:
    stack_path = ROOT / "stacks" / (match.group(1) + ".json")
    try:
        stack = json.loads(stack_path.read_text(encoding="utf-8"))
        signature = stack["signature"]
        if (stack["module"] != "hashcat/7.1.2-dtk26.04-z100"
                or signature["backend"]["version"] != "26.04"
                or signature["backend"]["target"] != "hygon-z100"):
            failures.append("R1 stack profile does not describe DTK 26.04 / Z100")
    except (OSError, ValueError, KeyError, TypeError):
        failures.append("R1 stack profile is missing or malformed")
print("\n".join(failures) if failures else "packaging validation: all passed")
sys.exit(bool(failures))
