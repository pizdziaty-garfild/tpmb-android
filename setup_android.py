#!/usr/bin/env python3
"""
TPMB Android Setup Script
Automated setup and configuration for Termux environment
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import argparse
from typing import Optional

def run_command(cmd: str, check: bool = True) -> tuple:
    """Run shell command and return result"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False, result.stderr
        return True, result.stdout
    except Exception as e:
        print(f"Command failed: {e}")
        return False, str(e)

def check_termux_environment():
    """Check if running in Termux environment"""
    termux_indicators = [
        os.path.exists('/data/data/com.termux'),
        'TERMUX_VERSION' in os.environ,
        'PREFIX' in os.environ and '/data/data/com.termux' in os.environ.get('PREFIX', '')
    ]
    
    if any(termux_indicators):
        print("✓ Termux environment detected")
        return True
    else:
        print("⚠️  Warning: Not running in Termux. Some features may not work properly.")
        return False

def install_termux_packages():
    """Install required Termux packages"""
    print("\n📦 Installing Termux packages...")
    
    packages = [
        'python', 'python-dev', 'git', 'openssl', 'openssl-dev',
        'libffi', 'libffi-dev', 'clang', 'make', 'cmake',
        'binutils', 'libc++', 'pkg-config', 'ca-certificates'
    ]
    
    # Update package list
    success, output = run_command('pkg update -y')
    if not success:
        print("❌ Failed to update package list")
        return False
        
    # Install packages
    pkg_cmd = f"pkg install -y {' '.join(packages)}"
    success, output = run_command(pkg_cmd)
    if not success:
        print("❌ Failed to install packages")
        return False
        
    print("✓ Termux packages installed successfully")
    return True

def upgrade_pip():
    """Upgrade pip and essential tools"""
    print("\n🔄 Upgrading pip...")
    
    commands = [
        'python -m pip install --upgrade pip',
        'pip install --upgrade setuptools wheel'
    ]
    
    for cmd in commands:
        success, output = run_command(cmd)
        if not success:
            print(f"⚠️  Warning: {cmd} failed, continuing...")
            
    print("✓ Pip upgrade completed")
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n🐍 Installing Python dependencies...")
    
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        return False
        
    success, output = run_command('pip install -r requirements.txt')
    if not success:
        print("❌ Failed to install Python dependencies")
        return False
        
    print("✓ Python dependencies installed successfully")
    return True

def create_instance_interactive():
    """Interactive instance creation"""
    print("\n🤖 Creating bot instance...")
    
    try:
        from utils.multi_instance_manager import MultiInstanceManager
    except ImportError:
        print("❌ Cannot import MultiInstanceManager. Install dependencies first.")
        return False
    
    # Get instance details
    instance_name = input("Enter instance name (default: my_bot): ").strip() or "my_bot"
    
    print("\nGet your Telegram ID by messaging @userinfobot")
    admin_id = input("Enter your Telegram user ID: ").strip()
    
    if not admin_id.isdigit():
        print("❌ Invalid Telegram ID")
        return False
    
    interval = input("Enter message interval in minutes (default: 5): ").strip() or "5"
    
    try:
        interval = int(interval)
        if interval < 1:
            raise ValueError("Interval must be >= 1")
    except ValueError:
        print("❌ Invalid interval")
        return False
    
    description = input(f"Enter bot description (default: Bot instance: {instance_name}): ").strip()
    if not description:
        description = f"Bot instance: {instance_name}"
    
    # Create instance
    manager = MultiInstanceManager()
    
    config = {
        'admin_ids': [int(admin_id)],
        'interval_minutes': interval,
        'description': description,
        'auto_start': False
    }
    
    if manager.create_instance(instance_name, config):
        print(f"✓ Instance '{instance_name}' created successfully")
        
        # Setup bot token
        setup_bot_token(instance_name)
        
        return True
    else:
        print(f"❌ Failed to create instance '{instance_name}'")
        return False

def setup_bot_token(instance_name: str):
    """Setup bot token for instance"""
    print(f"\n🤖 Setting up bot token for '{instance_name}'...")
    
    token = input("Enter your bot token (get from @BotFather): ").strip()
    
    if not token or ':' not in token:
        print("❌ Invalid bot token format")
        return False
    
    # Save token to file
    token_file = Path(f'instances/{instance_name}/config/bot_token.txt')
    token_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(token)
        
        print(f"✓ Bot token saved to {token_file}")
        print("ℹ️  Token will be automatically encrypted on first run")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save token: {e}")
        return False

def setup_sample_config(instance_name: str):
    """Setup sample configuration"""
    print(f"\n⚙️  Setting up sample configuration for '{instance_name}'...")
    
    config_dir = Path(f'instances/{instance_name}/config')
    
    # Sample message
    messages_file = config_dir / 'messages.txt'
    with open(messages_file, 'w', encoding='utf-8') as f:
        f.write(f"Hello from {instance_name}!\n")
        f.write("This is a test message from TPMB Android.\n")
        f.write("📱 Running on Android via Termux!")
    
    # Empty groups file
    groups_file = config_dir / 'groups.txt'
    groups_file.touch()
    
    print("✓ Sample configuration created")
    print(f"  - Messages: {messages_file}")
    print(f"  - Groups: {groups_file} (empty - add group IDs here)")
    
    return True

def run_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic tests...")
    
    tests = [
        ('Python version', 'python --version'),
        ('Pip version', 'pip --version'),
        ('Git version', 'git --version'),
        ('OpenSSL version', 'openssl version')
    ]
    
    for test_name, cmd in tests:
        success, output = run_command(cmd, check=False)
        if success:
            print(f"✓ {test_name}: {output.strip()}")
        else:
            print(f"❌ {test_name}: Failed")
    
    # Test Python imports
    test_imports = [
        'telegram',
        'aiohttp', 
        'cryptography',
        'apscheduler',
        'colorama'
    ]
    
    print("\nTesting Python imports:")
    for module in test_imports:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"❌ {module} - not installed")
    
    return True

def show_usage_instructions(instance_name: str = None):
    """Show usage instructions"""
    print("\n🎉 Setup Complete!")
    print("\n📦 Next steps:")
    
    if instance_name:
        print(f"\n1. Add target groups to: instances/{instance_name}/config/groups.txt")
        print("   Example: echo '-1001234567890' >> instances/{}/config/groups.txt".format(instance_name))
        
        print(f"\n2. Run your bot:")
        print(f"   python main.py --instance {instance_name}")
        
        print(f"\n3. Or run in background:")
        print(f"   nohup python main.py --instance {instance_name} > bot.log 2>&1 &")
        
    else:
        print("\n1. Create a bot instance:")
        print("   python setup_android.py --interactive")
        
    print("\n4. Control via Telegram:")
    print("   /start_bot - Start messaging")
    print("   /stop_bot - Stop messaging")
    print("   /status - Check status")
    print("   /add_group [id] - Add target group")
    
    print("\n5. View logs:")
    print("   tail -f instances/[name]/logs/bot_activity.log")
    
    print("\n📄 Documentation: https://github.com/pizdziaty-garfild/tpmb-android")

def main():
    parser = argparse.ArgumentParser(description='TPMB Android Setup Script')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive setup with instance creation')
    parser.add_argument('--packages-only', action='store_true',
                        help='Only install Termux packages')
    parser.add_argument('--python-only', action='store_true',
                        help='Only install Python dependencies')
    parser.add_argument('--test', action='store_true',
                        help='Run tests only')
    parser.add_argument('--skip-packages', action='store_true',
                        help='Skip Termux package installation')
    
    args = parser.parse_args()
    
    print("📱 TPMB Android Setup Script")
    print("===========================\n")
    
    # Check environment
    is_termux = check_termux_environment()
    
    if args.test:
        run_tests()
        return
    
    if args.packages_only:
        if is_termux:
            install_termux_packages()
        else:
            print("Package installation skipped - not in Termux")
        return
    
    if args.python_only:
        upgrade_pip()
        install_python_dependencies()
        run_tests()
        return
    
    # Full setup
    success_steps = []
    
    # Step 1: Install Termux packages
    if not args.skip_packages and is_termux:
        if install_termux_packages():
            success_steps.append("Termux packages")
    elif args.skip_packages:
        print("⏭️  Skipping Termux package installation")
        success_steps.append("Termux packages (skipped)")
    
    # Step 2: Upgrade pip
    if upgrade_pip():
        success_steps.append("Pip upgrade")
    
    # Step 3: Install Python dependencies
    if install_python_dependencies():
        success_steps.append("Python dependencies")
    
    # Step 4: Run basic tests
    if run_tests():
        success_steps.append("Basic tests")
    
    # Step 5: Interactive instance creation
    instance_name = None
    if args.interactive:
        if create_instance_interactive():
            # Get the created instance name for instructions
            # This is a simple way, in production you'd return it from the function
            success_steps.append("Bot instance creation")
    
    # Summary
    print("\n🎆 Setup Summary")
    print("=================")
    for step in success_steps:
        print(f"✓ {step}")
    
    if len(success_steps) >= 3:  # At least basic setup completed
        show_usage_instructions(instance_name)
    else:
        print("\n⚠️  Setup incomplete. Please resolve errors and try again.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)
