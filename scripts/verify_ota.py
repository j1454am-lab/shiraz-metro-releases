#!/usr/bin/env python3
"""Public, non-secret OTA admission gate. Trust anchor: device-tested 1.0.18 APK."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = "j1454am-lab/shiraz-metro-releases"
PACKAGE = "ir.sjsalimi.shirazmetro"
ANCHOR = "23852497d91e94d963a55e8b0519d3c7fe6fb9c66474570cf54f885990943472"
KEYS = {"schema", "package_name", "version_code", "version_name", "notes_fa", "sha256", "apk_url"}

def require(condition, message):
    if not condition:
        raise SystemExit(message)

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def manifest(path):
    f = json.loads(path.read_text(encoding="utf-8"))
    require(type(f) is dict and set(f) == KEYS, "Unexpected manifest fields")
    require(type(f["schema"]) is int and f["schema"] == 1 and f["package_name"] == PACKAGE, "Wrong schema/package")
    require(type(f["version_code"]) is int and 0 < f["version_code"] <= 2100000000, "Invalid version code")
    v = f["version_name"]
    require(isinstance(v,str) and re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)",v), "Invalid version name")
    require(isinstance(f["sha256"],str) and re.fullmatch(r"[0-9a-f]{64}",f["sha256"]), "Malformed SHA-256")
    require(isinstance(f["notes_fa"],str) and 0 < len(f["notes_fa"].strip()) <= 350 and not any(ord(c)<32 for c in f["notes_fa"]), "Invalid release notes")
    require(f["apk_url"] == f"https://github.com/{REPO}/releases/download/v{v}/shiraz-metro-{v}-signed.apk", "Noncanonical download URL")
    return f

def signer(executable, apk):
    report = subprocess.check_output([executable,"verify","--verbose","--print-certs",str(apk)], text=True)
    require("Verified using v2 scheme (APK Signature Scheme v2): true" in report, "Missing v2 APK signature")
    matches = re.findall(r"(?m)^Signer #\d+ certificate SHA-256 digest: ([0-9A-Fa-f:]+)\s*$", report)
    require(len(matches)==1, "APK must have exactly one verified signer")
    return matches[0].replace(":","").lower()

def verify(args):
    f = manifest(args.manifest)
    if args.previous:
        prior = manifest(args.previous)
        require(f["version_code"] > prior["version_code"], "Duplicate or downgrade")
        require(tuple(map(int,f["version_name"].split("."))) > tuple(map(int,prior["version_name"].split("."))), "Version name must advance")
    require(args.apk.is_file() and 1024 < args.apk.stat().st_size <= 50*1024*1024, "APK size invalid")
    require(sha(args.apk) == f["sha256"], "APK checksum mismatch")
    require(sha(args.anchor) == ANCHOR, "Trusted baseline APK checksum mismatch")
    require(signer(args.apksigner,args.apk) == signer(args.apksigner,args.anchor), "Signing certificate mismatch")
    report = subprocess.check_output([args.aapt,"dump","badging",str(args.apk)], text=True)
    expected = f"package: name='{PACKAGE}' versionCode='{f['version_code']}' versionName='{f['version_name']}'"
    require(report.splitlines()[0].startswith(expected+" "), "APK metadata mismatch")
    if args.sums:
        expected_sum = f"{f['sha256']}  shiraz-metro-{f['version_name']}-signed.apk\n"
        require(args.sums.read_text(encoding="ascii") == expected_sum, "Checksum asset mismatch")
    print(f"PUBLIC_GATE_PASS: {f['version_name']} / {f['version_code']}; verified checksum, metadata and trusted signer")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for flag in ("manifest","apk","anchor"):
        p.add_argument("--"+flag,type=Path,required=True)
    p.add_argument("--previous",type=Path)
    p.add_argument("--sums",type=Path)
    p.add_argument("--apksigner",required=True)
    p.add_argument("--aapt",required=True)
    verify(p.parse_args())
