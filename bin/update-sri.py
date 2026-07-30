#!/usr/bin/env python3
"""
Regenerate the Subresource Integrity (SRI) hashes in lib/Configuration.php
from the actual files on disk.

Run this whenever you edit any bundled asset (anything in js/). If the SRI
hash in the config doesn't match the served file, the browser silently
refuses to execute the script and the app hangs on "Loading...".

Usage:
    python3 bin/update-sri.py          # rewrite hashes in place
    python3 bin/update-sri.py --check  # report mismatches, change nothing
                                        # (exit 1 if any are stale — good for CI)
"""
import base64
import hashlib
import os
import re
import sys

# Run from the repo root regardless of where it's invoked from.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "lib", "Configuration.php")

# Matches:  'js/privatebin.js'       => 'sha512-....',
ENTRY = re.compile(r"('(?:js|css)/[^']+'\s*=>\s*')sha512-[A-Za-z0-9+/=]+(')")


def sri_for(path):
    with open(path, "rb") as fh:
        digest = hashlib.sha512(fh.read()).digest()
    return "sha512-" + base64.b64encode(digest).decode()


def main():
    check_only = "--check" in sys.argv
    src = open(CONFIG, encoding="utf-8").read()

    changed, missing, stale = [], [], []

    def replace(m):
        prefix, suffix = m.group(1), m.group(2)
        rel = prefix.split("'")[1]            # e.g. js/privatebin.js
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            missing.append(rel)
            return m.group(0)                 # leave untouched
        correct = sri_for(path)
        if m.group(0) == prefix + correct + suffix:
            return m.group(0)                 # already correct
        (stale if check_only else changed).append(rel)
        return prefix + correct + suffix

    new = ENTRY.sub(replace, src)

    for rel in missing:
        print(f"  skip (file not present): {rel}")

    if check_only:
        for rel in stale:
            print(f"  STALE: {rel}")
        if stale:
            print(f"\n{len(stale)} stale SRI hash(es). Run: python3 bin/update-sri.py")
            return 1
        print("All SRI hashes are up to date.")
        return 0

    if changed:
        with open(CONFIG, "w", encoding="utf-8") as fh:
            fh.write(new)
        for rel in changed:
            print(f"  updated: {rel}")
        print(f"\nUpdated {len(changed)} SRI hash(es) in lib/Configuration.php.")
    else:
        print("All SRI hashes already up to date — nothing to change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
