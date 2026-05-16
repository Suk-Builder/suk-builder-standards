#!/usr/bin/env python3
"""
Suk-Builder GitHub 生态审计脚本 v1.0
季度自动化审计：README、LICENSE、Topics、描述格式
"""

import os
import sys
import re
import subprocess
import json
from datetime import datetime, timezone

REPOS = [
    "Builder-System", "BaiHua-Memory", "BaiHua-Wiki",
    "builder-agent", "ai-workshop", "docmind", "sparkle-theater",
    "psych-detect", "brick-game", "bdi-validation-framework", "baihua-workshop",
    "sukcommerce",
    "sukaczev", "sukaczev-app", "sukaczev-web",
    "clash-verge-rev", "qq-chat-exporter",
    "Fracture-Workshop-Alliance", "Sukaczev-Builder-System", "Unarchived"
]
ORG = "Suk-Builder"

def run_git(args, cwd=None):
    result = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd, timeout=300)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def check_readme(repo_dir):
    readme_path = os.path.join(repo_dir, "README.md")
    if not os.path.exists(readme_path):
        return {"status": "FATAL", "size": 0, "issues": ["README.md does not exist"]}
    size = os.path.getsize(readme_path)
    with open(readme_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    issues = []
    if size == 0:
        status = "FATAL"
        issues.append("README.md is empty")
    elif size < 50:
        status = "CRITICAL"
        issues.append(f"README.md too small ({size} bytes)")
    elif size < 1000:
        status = "WEAK"
        issues.append(f"README.md minimal ({size} bytes)")
    elif size < 5000:
        status = "OK"
    else:
        status = "GOOD"
    title_match = re.search(r"^# (.+?)[ \t]*[\u00b7\u2014-]", content, re.MULTILINE)
    if not title_match:
        issues.append("Title format invalid: missing separator")
    has_bs = "builder-system" in content.lower() or "Builder-System" in content
    if not has_bs and size > 1000:
        issues.append("Missing Builder-System association")
    return {"status": status, "size": size, "issues": issues}

def check_license(repo_dir):
    for lf in ["LICENSE", "LICENSE.md", "LICENSE.txt"]:
        if os.path.exists(os.path.join(repo_dir, lf)):
            return {"status": "OK", "file": lf}
    return {"status": "MISSING", "issues": ["No LICENSE file"]}

def audit_repo(repo):
    repo_dir = f"/tmp/audit-repos/{repo}"
    os.makedirs("/tmp/audit-repos", exist_ok=True)
    if not os.path.exists(repo_dir):
        stdout, stderr, rc = run_git(["clone", "--depth", "1",
            f"https://github.com/{ORG}/{repo}.git", repo_dir])
        if rc != 0:
            return {"repo": repo, "fetch_ok": False, "error": stderr[:100]}
    else:
        run_git(["pull", "origin", "HEAD"], cwd=repo_dir)
    return {
        "repo": repo, "fetch_ok": True,
        "readme": check_readme(repo_dir),
        "license": check_license(repo_dir),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def main():
    print("=" * 60)
    print("Suk-Builder GitHub Ecosystem Audit")
    print("=" * 60)
    results = []
    for repo in REPOS:
        r = audit_repo(repo)
        results.append(r)
        rs = r.get("readme", {})
        ls = r.get("license", {})
        issues = rs.get("issues", []) + ls.get("issues", [])
        marker = "OK" if not issues and rs.get("status") in ("OK", "GOOD") else "!"
        print(f" {marker} {repo:30s} README:{rs.get('status', '?'):8s} {rs.get('size', 0):5d}B  LIC:{ls.get('status', '?')}")
        for issue in issues[:2]:
            print(f"    {issue}")
    fatal = sum(1 for r in results if r.get("readme", {}).get("status") == "FATAL")
    weak = sum(1 for r in results if r.get("readme", {}).get("status") == "WEAK")
    no_lic = sum(1 for r in results if r.get("license", {}).get("status") == "MISSING")
    print(f"\nFATAL:{fatal}  WEAK:{weak}  NO-LICENSE:{no_lic}")
    os.makedirs("/tmp/audit-reports", exist_ok=True)
    with open(f"/tmp/audit-reports/audit-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json", "w") as f:
        json.dump(results, f, indent=2)
    sys.exit(1 if fatal > 0 or no_lic > 0 else 0)

if __name__ == "__main__":
    main()
