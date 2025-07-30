#!/usr/bin/env python3
"""
GitHub Repository Setup Script
This script helps initialize the Git repository and prepare it for GitHub.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        return None

def check_git_installed():
    """Check if Git is installed"""
    return run_command("git --version", check=False) is not None

def initialize_git_repo():
    """Initialize Git repository"""
    if not check_git_installed():
        print("❌ Git is not installed. Please install Git first.")
        return False
    
    # Check if already a Git repository
    if Path(".git").exists():
        print("ℹ️  Git repository already exists")
        return True
    
    # Initialize Git repository
    print("🔧 Initializing Git repository...")
    if run_command("git init") is None:
        return False
    
    print("✅ Git repository initialized")
    return True

def create_initial_commit():
    """Create initial commit"""
    print("📝 Creating initial commit...")
    
    # Add all files
    if run_command("git add .") is None:
        return False
    
    # Create commit
    commit_message = """feat: initial commit

PayPal Merchant Troubleshooting Application

- FastAPI backend with Elasticsearch integration
- Real-time merchant issue detection and analysis
- AI-powered troubleshooting with risk scoring
- Modern web dashboard with interactive charts
- Docker support for easy deployment
- Comprehensive documentation and demo guide

Features:
- Conversion rate analysis and monitoring
- Location data validation and compliance
- Error rate tracking and correlation
- Month-to-month performance comparisons
- Automated issue detection and recommendations"""
    
    if run_command(f'git commit -m "{commit_message}"') is None:
        return False
    
    print("✅ Initial commit created")
    return True

def setup_remote_repo():
    """Set up remote repository"""
    print("\n🌐 GitHub Repository Setup")
    print("=" * 50)
    
    repo_name = input("Enter GitHub repository name (e.g., pp-merchantai): ").strip()
    if not repo_name:
        print("❌ Repository name is required")
        return False
    
    username = input("Enter your GitHub username: ").strip()
    if not username:
        print("❌ GitHub username is required")
        return False
    
    # Add remote origin
    remote_url = f"https://github.com/{username}/{repo_name}.git"
    print(f"🔗 Adding remote origin: {remote_url}")
    
    if run_command(f"git remote add origin {remote_url}") is None:
        return False
    
    # Push to GitHub
    print("🚀 Pushing to GitHub...")
    if run_command("git branch -M main") is None:
        return False
    
    if run_command("git push -u origin main") is None:
        return False
    
    print(f"✅ Repository pushed to GitHub: https://github.com/{username}/{repo_name}")
    return True

def create_github_repo_instructions():
    """Print instructions for creating GitHub repository"""
    print("\n📋 GitHub Repository Creation Instructions")
    print("=" * 50)
    print("1. Go to https://github.com/new")
    print("2. Repository name: pp-merchantai (or your preferred name)")
    print("3. Description: PayPal Merchant Troubleshooting Application")
    print("4. Make it Public or Private (your choice)")
    print("5. Do NOT initialize with README, .gitignore, or license (we already have them)")
    print("6. Click 'Create repository'")
    print("7. Come back here and run this script again")
    print()

def main():
    """Main setup function"""
    print("🚀 PayPal Merchant Troubleshooting - GitHub Setup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Initialize Git repository
    if not initialize_git_repo():
        sys.exit(1)
    
    # Create initial commit
    if not create_initial_commit():
        sys.exit(1)
    
    # Check if remote already exists
    remote_exists = run_command("git remote get-url origin", check=False)
    
    if remote_exists:
        print(f"ℹ️  Remote origin already exists: {remote_exists}")
        push_choice = input("Do you want to push to the existing remote? (y/n): ").lower()
        if push_choice == 'y':
            if run_command("git push -u origin main") is None:
                sys.exit(1)
            print("✅ Code pushed to existing repository")
    else:
        # Check if GitHub CLI is available
        if run_command("gh --version", check=False) is not None:
            print("🔧 GitHub CLI detected")
            create_repo = input("Do you want to create a GitHub repository using GitHub CLI? (y/n): ").lower()
            if create_repo == 'y':
                repo_name = input("Enter repository name (e.g., pp-merchantai): ").strip()
                if repo_name:
                    print(f"🔧 Creating GitHub repository: {repo_name}")
                    if run_command(f"gh repo create {repo_name} --public --source=. --remote=origin --push") is None:
                        print("❌ Failed to create repository with GitHub CLI")
                        create_github_repo_instructions()
                    else:
                        print(f"✅ Repository created and pushed to GitHub")
                        return
        else:
            create_github_repo_instructions()
            setup_remote_repo()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Visit your GitHub repository")
    print("2. Set up GitHub Actions secrets if needed (DOCKER_USERNAME, DOCKER_PASSWORD)")
    print("3. Run the demo: python scripts/run_demo.py")
    print("4. Share the repository with your team!")

if __name__ == "__main__":
    main() 