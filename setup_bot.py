#!/usr/bin/env python3
"""
TPMB Android Configuration Helper
Samsung Galaxy XCover 7 Optimized
"""

import os
import sys
from pathlib import Path

def main():
    print("🤖 TPMB Android Configuration Helper")
    print("📱 Samsung Galaxy XCover 7 Edition")
    print("=" * 40)
    
    # Get bot token
    print("\n📋 Step 1: Bot Token Configuration")
    print("💡 Get your bot token from @BotFather on Telegram")
    token = input("🔑 Enter your bot token: ").strip()
    
    if not token or ':' not in token:
        print("❌ Invalid token format")
        return
    
    # Save token
    config_dir = Path("instances/default/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_dir / "bot_token.txt", "w") as f:
        f.write(token)
    
    print("✅ Token saved successfully")
    
    # Get admin ID  
    print("\n👤 Step 2: Admin Configuration")
    print("💡 Get your Telegram user ID from @userinfobot")
    admin_id = input("🆔 Enter your Telegram user ID: ").strip()
    
    if admin_id.isdigit():
        with open(config_dir / "settings.txt", "w") as f:
            f.write(f"interval_minutes=5\n")
            f.write(f"admin_ids={admin_id}\n")
        print("✅ Admin ID configured successfully")
    
    # Set default message
    print("\n💬 Step 3: Default Message")
    message = input("📝 Enter default message (or press Enter for default): ").strip()
    if not message:
        # Neutral, non-promotional test text as requested
        message = "test"
    
    with open(config_dir / "messages.txt", "w") as f:
        f.write(message)
    
    print("✅ Default message set")
    
    # Create empty groups file
    with open(config_dir / "groups.txt", "w") as f:
        f.write("")
    
    print("\n🎉 Configuration completed!")
    print("\n📋 Next steps:")
    print("1. Add target groups using: /add_group [group_id]")
    print("2. Start the bot: python main.py")
    print("3. Control via Telegram commands: /help")

if __name__ == "__main__":
    main()
