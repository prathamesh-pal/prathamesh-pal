#!/usr/bin/env python3
"""Check the profile README before you push it.

    python tools/check_readme.py

Verifies, ignoring anything inside HTML comments:
  * every local image / <picture> source exists
  * every web link answers (HTTP < 400)
  * mailto addresses are well formed
  * the GitHub username is spelled the same everywhere
  * lists the TODO markers still to fill in
Standard library only. Exits non-zero if something is broken.
"""
import pathlib
import re
import sys
import urllib.error
import urllib.request

USER = "prathamesh-pal"
README = pathlib.Path(__file__).resolve().parent.parent / "README.md"
ROOT = README.parent


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "readme-check"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # offline, DNS, blocked
        return f"unreachable ({type(e).__name__})"


def main():
    raw = README.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", raw, flags=re.S)  # live content only
    failures = 0

    refs = set(re.findall(r'(?:src|srcset|href)="([^"]+)"', text))
    refs |= set(re.findall(r"\]\(([^)\s]+)\)", text))

    for ref in sorted(refs):
        if ref.startswith("mailto:"):
            ok = re.fullmatch(r"mailto:[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", ref)
            print(f"{'ok  ' if ok else 'FAIL'} {ref}")
            failures += not ok
        elif ref.startswith(("http://", "https://")):
            status = fetch(ref)
            ok = isinstance(status, int) and status < 400
            print(f"{'ok  ' if ok else 'FAIL'} {status}  {ref}")
            failures += not ok
        else:
            ok = (ROOT / ref).is_file()
            print(f"{'ok  ' if ok else 'FAIL'} file  {ref}")
            failures += not ok

    wrong = re.findall(r"github\.com/(?!%s\b)[\w.-]+" % re.escape(USER), text)
    wrong = [w for w in wrong if "raw.githubusercontent" not in w]
    if wrong or "prathameshpal" in text.replace("TODO-your-email", ""):
        print("FAIL username spelled differently somewhere:", wrong)
        failures += 1
    else:
        print(f"ok   username is '{USER}' everywhere")

    todos = [(i, l.strip()) for i, l in enumerate(text.splitlines(), 1)
             if "TODO" in l]
    print(f"\n{len(todos)} TODO marker(s) to resolve:")
    for i, l in todos:
        print(f"  line {i}: {l[:110]}")

    print("\nFAILED" if failures else "\nAll references resolve.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
