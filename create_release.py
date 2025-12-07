#!/usr/bin/env python3
"""
Script to create a GitHub release with notes.
Requires: pip install requests
Usage: python create_release.py v1.0.0
"""

import sys
import os
import subprocess
import requests
import json

def get_github_token():
    """Extract GitHub token from git remote URL"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        # Extract token from URL like: https://token@github.com/user/repo.git
        if "@" in url and "github.com" in url:
            token = url.split("@")[0].replace("https://", "").replace("http://", "")
            if token and len(token) > 10:  # Basic validation
                return token
    except Exception as e:
        print(f"Could not extract token from git remote: {e}")
    return None

def get_repo_info():
    """Extract repo owner and name from git remote"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        # Extract from: https://token@github.com/owner/repo.git
        if "github.com" in url:
            parts = url.split("github.com/")[1].replace(".git", "").split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception as e:
        print(f"Could not extract repo info: {e}")
    return None, None

def read_release_notes():
    """Read RELEASE_NOTES.md"""
    if os.path.exists("RELEASE_NOTES.md"):
        with open("RELEASE_NOTES.md", "r", encoding="utf-8") as f:
            return f.read()
    return "Release v1.0.0"

def create_release(tag, token, owner, repo):
    """Create GitHub release via API"""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    notes = read_release_notes()
    
    data = {
        "tag_name": tag,
        "name": f"Release {tag}",
        "body": notes,
        "draft": False,
        "prerelease": False
    }
    
    print(f"Creating release {tag} for {owner}/{repo}...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        release_data = response.json()
        print(f"✅ Release created successfully!")
        print(f"   URL: {release_data['html_url']}")
        print(f"\n⚠️  Note: You still need to:")
        print(f"   1. Build the installers:")
        print(f"      - Windows: build_windows.bat")
        print(f"      - Linux: ./build_linux.sh")
        print(f"   2. Upload the files to the release:")
        print(f"      - yt_mp3_mp4_download-setup-1.0.0.exe")
        print(f"      - yt_mp3_mp4_download-1.0.0-x86_64.AppImage")
        return True
    else:
        print(f"❌ Failed to create release: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 422:
            print("\n   This might mean the release already exists.")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_release.py <tag>")
        print("Example: python create_release.py v1.0.0")
        sys.exit(1)
    
    tag = sys.argv[1]
    
    token = get_github_token()
    if not token:
        print("❌ Could not extract GitHub token from git remote.")
        print("   Please set GITHUB_TOKEN environment variable or create release manually.")
        sys.exit(1)
    
    owner, repo = get_repo_info()
    if not owner or not repo:
        print("❌ Could not extract repo info from git remote.")
        sys.exit(1)
    
    print(f"Repository: {owner}/{repo}")
    print(f"Tag: {tag}")
    
    if not create_release(tag, token, owner, repo):
        sys.exit(1)

if __name__ == "__main__":
    main()
