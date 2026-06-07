import sys
import os
import re
from datetime import datetime

def get_current_version():
    with open("setup.py", "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find version in setup.py")
    return match.group(1)

def increment_version(version_str):
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Version '{version_str}' is not in semver major.minor.patch format")
    parts[2] = str(int(parts[2]) + 1)
    return '.'.join(parts)

def update_file(filepath, old_version, new_version, today_str):
    if not os.path.exists(filepath):
        print(f"Skipping non-existent file: {filepath}")
        return
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace version strings
    updated_content = content
    
    # Special replacements for AGENTS.md headers/footers
    if "AGENTS.md" in filepath:
        # e.g., # Agent — gsheets-orm (v0.1.0) — 2026-06-06
        updated_content = re.sub(
            r'# Agent — gsheets-orm \(v' + re.escape(old_version) + r'\) — \d{4}-\d{2}-\d{2}',
            f'# Agent — gsheets-orm (v{new_version}) — {today_str}',
            updated_content
        )
        # e.g. *v0.1.0 — 2026-06-06*
        updated_content = re.sub(
            r'\*v' + re.escape(old_version) + r' — \d{4}-\d{2}-\d{2}\*',
            f'*v{new_version} — {today_str}*',
            updated_content
        )
    # Special replacement for docs/
    elif filepath.startswith("docs/"):
        # e.g. *v0.1.0 — 2026-06-06*
        updated_content = re.sub(
            r'\*v' + re.escape(old_version) + r' — \d{4}-\d{2}-\d{2}\*',
            f'*v{new_version} — {today_str}*',
            updated_content
        )
    # setup.py version replacement
    elif filepath == "setup.py":
        updated_content = re.sub(
            r'version\s*=\s*["\']' + re.escape(old_version) + r'["\']',
            f'version="{new_version}"',
            updated_content
        )
        
    if updated_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Updated: {filepath}")
    else:
        print(f"No version changes made to: {filepath}")

def main():
    try:
        current_version = get_current_version()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        new_version = sys.argv[1]
    else:
        new_version = increment_version(current_version)
        
    print(f"Bumping version: {current_version} -> {new_version}")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Files to update
    update_file("setup.py", current_version, new_version, today_str)
    update_file("AGENTS.md", current_version, new_version, today_str)
    
    docs_dir = "docs"
    if os.path.exists(docs_dir):
        for filename in os.listdir(docs_dir):
            if filename.endswith(".md"):
                update_file(os.path.join(docs_dir, filename), current_version, new_version, today_str)
                
    print("Version bump complete.")

if __name__ == "__main__":
    main()
