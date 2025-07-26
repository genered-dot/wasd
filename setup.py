#!/usr/bin/env python3
"""
Discord Verification System Setup Script
Helps users configure and set up the verification system
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🔐 Discord Verification System Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def create_directories():
    """Create necessary directories"""
    directories = ['bot', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'bot/requirements.txt'
        ])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    return True

def setup_environment():
    """Set up environment file"""
    env_path = Path('bot/.env')
    env_example_path = Path('bot/.env.example')
    
    if env_path.exists():
        print(f"⚠️  Environment file already exists: {env_path}")
        return True
    
    if env_example_path.exists():
        # Copy example file
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"📄 Created environment file: {env_path}")
        print("⚠️  Please edit bot/.env and add your Discord bot token")
        return True
    else:
        # Create basic env file
        content = "BOT_TOKEN=your_discord_bot_token_here\n"
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"📄 Created basic environment file: {env_path}")
        print("⚠️  Please edit bot/.env and add your Discord bot token")
        return True

def create_config_files():
    """Create initial configuration files"""
    
    # Bot config
    bot_config_path = Path('bot/bot_config.json')
    if not bot_config_path.exists():
        config = {
            "verification_channel": None,
            "verification_website": None,
            "verification_role": None,
            "unverified_role": None,
            "mute_role": None,
            "max_failed_attempts": 3,
            "auto_blacklist_enabled": True
        }
        
        with open(bot_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"⚙️  Created bot config file: {bot_config_path}")
    
    # Verification data
    data_path = Path('bot/verification_data.json')
    if not data_path.exists():
        data = {
            "verification_data": {},
            "blacklist": [],
            "whitelist": [],
            "failed_attempts": {},
            "last_updated": "never"
        }
        
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Created verification data file: {data_path}")

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print()
    print("1. 🔑 Configure your Discord bot:")
    print("   - Edit bot/.env and add your BOT_TOKEN")
    print("   - Invite your bot to your Discord server")
    print()
    print("2. 🌐 Set up GitHub Pages:")
    print("   - Push this repository to GitHub")
    print("   - Enable GitHub Pages in repository settings")
    print("   - Your website will be at: https://username.github.io/repo-name")
    print()
    print("3. 🤖 Start the Discord bot:")
    print("   cd bot")
    print("   python enhanced_bot.py")
    print()
    print("4. ⚙️  Configure the bot (use these commands in Discord):")
    print("   /config channel #verification-channel")
    print("   /config website https://username.github.io/repo-name")
    print("   /config role @Verified")
    print("   /config unverified @Unverified")
    print()
    print("5. 🔧 Required bot permissions:")
    print("   - Manage Roles")
    print("   - Send Messages")
    print("   - Use Slash Commands")
    print("   - Read Message History")
    print("   - Embed Links")
    print("   - Attach Files")
    print()
    print("📖 For detailed instructions, see README.md")
    print("🆘 For support, create an issue on GitHub")

def main():
    """Main setup function"""
    print_banner()
    
    # Check system requirements
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Set up environment
    setup_environment()
    
    # Create config files
    create_config_files()
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main()