# TPMB Android - Enhanced Telegram Bot for Android

**Enhanced multi-instance Telegram bot optimized for Android devices with military-grade security, resilient time handling, and remote control capabilities.**

## 🚀 Features

### ✨ New in Android Version
- **🔒 Military-Grade Security**: PBKDF2 encryption with 480,000 iterations
- **📱 Android Optimized**: Specially tuned for mobile networks and battery efficiency  
- **⚡ Multi-Instance Support**: Run multiple independent bot instances simultaneously
- **🌐 TLS 1.3 Enforcement**: Ultra-secure HTTPS connections with certificate validation
- **⏰ Resilient Time Handling**: NTP synchronization with DST awareness
- **🎛️ Remote Control**: Full bot management via Telegram commands
- **🔄 Network Resilience**: Automatic recovery from connection interruptions
- **📊 Resource Monitoring**: Real-time instance monitoring and management

### 🛡️ Security Enhancements
- Encrypted token storage with metadata
- Certificate pinning and validation
- Protection against timing attacks
- Secure random key generation
- Automatic token rotation alerts
- Network security validation

### 🕒 Time & Scheduling Improvements  
- Multi-server NTP synchronization (Polish and European servers)
- DST (Daylight Saving Time) automatic handling
- Network interruption tolerance
- Mobile-friendly timeout configurations
- Automatic time drift correction
- Timezone-aware scheduling

## 📱 Android Installation (Termux)

### Step 1: Install Termux
Download Termux from [F-Droid](https://f-droid.org/en/packages/com.termux/) (recommended) or GitHub releases.

### Step 2: Setup Termux Environment
```bash
# Update packages
pkg update && pkg upgrade -y

# Install required system packages
pkg install -y python python-dev git openssl openssl-dev libffi libffi-dev clang make cmake

# Install additional build tools
pkg install -y binutils libc++ pkg-config

# Update pip
python -m pip install --upgrade pip setuptools wheel
```

### Step 3: Clone and Install TPMB Android
```bash
# Clone the repository
git clone https://github.com/pizdziaty-garfild/tpmb-android.git
cd tpmb-android

# Install dependencies
pip install -r requirements.txt

# Create your first bot instance
python -c "
from utils.multi_instance_manager import MultiInstanceManager
manager = MultiInstanceManager()
manager.create_instance('my_bot', {
    'admin_ids': [YOUR_TELEGRAM_ID],
    'interval_minutes': 5,
    'description': 'My first Android bot'
})
print('Instance created successfully!')
"
```

### Step 4: Configure Your Bot
```bash
# Set up bot token (get from @BotFather on Telegram)
mkdir -p instances/my_bot/config
echo "YOUR_BOT_TOKEN" > instances/my_bot/config/bot_token.txt

# Configure groups (add your group chat IDs)
echo "-1001234567890" >> instances/my_bot/config/groups.txt

# Set custom messages
echo "Hello from my Android bot!" > instances/my_bot/config/messages.txt

# Update settings
cat > instances/my_bot/config/settings.txt << EOF
interval_minutes=5
admin_ids=YOUR_TELEGRAM_ID
EOF
```

### Step 5: Run Your Bot
```bash
# Start your bot instance
python main.py --instance my_bot

# Or run in background
nohup python main.py --instance my_bot > bot.log 2>&1 &
```

## 🎛️ Remote Control Commands

Once running, control your bot via Telegram:

- `/start_bot` - Start message broadcasting
- `/stop_bot` - Stop message broadcasting  
- `/status` - Get bot status and statistics
- `/set_interval [minutes]` - Change message interval
- `/add_group [group_id]` - Add target group
- `/remove_group [group_id]` - Remove target group
- `/list_groups` - List configured groups
- `/set_message [text]` - Set bot message
- `/get_message` - Get current message

## 🔧 Multi-Instance Management

### Create Additional Instances
```bash
# Create a second bot instance
python -c "
from utils.multi_instance_manager import MultiInstanceManager
manager = MultiInstanceManager()
manager.create_instance('second_bot', {
    'admin_ids': [YOUR_TELEGRAM_ID],
    'interval_minutes': 10
})
"

# Run multiple instances
python main.py --instance my_bot &
python main.py --instance second_bot &
```

### Instance Management Commands
```bash
# List all instances
python main.py --list-instances

# Check instance status
python -c "
from utils.multi_instance_manager import MultiInstanceManager
manager = MultiInstanceManager()
print(manager.get_summary())
"
```

## 🔒 Security Configuration

### Enable Admin Authorization
Add your Telegram user ID to admin list for remote control:
```bash
# Get your Telegram ID by messaging @userinfobot
echo "admin_ids=123456789,987654321" >> instances/my_bot/config/settings.txt
```

### Token Security
- Tokens are automatically encrypted using PBKDF2 with 480,000 iterations
- Original plaintext tokens are securely deleted after migration
- Encrypted storage uses AES-256 with secure random salts

## 📊 Monitoring & Logs

### Log Files
- `instances/[name]/logs/bot_activity.log` - Main activity log
- Instance-specific logging with timestamps
- Automatic log rotation (when available)

### Performance Monitoring
```bash
# Check instance resources
python -c "
from utils.multi_instance_manager import MultiInstanceManager
manager = MultiInstanceManager()
instances = manager.list_instances()
for instance in instances:
    print(f'{instance["name"]}: {instance.get("resources", "N/A")}')
"
```

## 🛠️ Troubleshooting

### Common Android/Termux Issues

**Permission Denied Errors:**
```bash
# Fix permissions
chmod +x main.py
chmod -R 755 instances/
```

**Network/SSL Errors:**
```bash
# Update certificates
pkg install ca-certificates
pip install --upgrade certifi
```

**Memory Issues:**
```bash
# Reduce concurrent instances
# Edit utils/multi_instance_manager.py
# Set max_concurrent_instances = 3
```

**Time Sync Issues:**
```bash
# Force NTP sync
python -c "
import asyncio
from utils.time_handler import ResilientTimeHandler
handler = ResilientTimeHandler()
asyncio.run(handler.sync_time())
print('Time synced manually')
"
```

## 🔄 Migration from Original TPMB

### Import Existing Configuration
```bash
# If you have existing TPMB config, copy files:
cp ../tpmb/config/bot_token.txt instances/my_bot/config/
cp ../tpmb/config/groups.txt instances/my_bot/config/
cp ../tpmb/config/messages.txt instances/my_bot/config/

# The bot will automatically encrypt the token on first run
```

## 🎯 Performance Optimization for Android

### Battery Optimization
- Reduced NTP sync frequency (1 hour intervals)
- Mobile-friendly network timeouts
- Efficient resource usage monitoring
- Smart scheduling with coalesced jobs

### Network Optimization  
- Exponential backoff on failures
- Connection pooling and reuse
- Compressed HTTP responses
- Multiple NTP server fallbacks

### Memory Management
- Limited concurrent instances (5 max)
- Automatic cleanup of orphaned processes
- Efficient log rotation
- Resource monitoring per instance

## 📝 Configuration Files

### Instance Structure
```
instances/
├── registry.json          # Instance registry
├── my_bot/
│   ├── config/
│   │   ├── bot_token.enc  # Encrypted token
│   │   ├── groups.txt     # Target groups
│   │   ├── messages.txt   # Bot messages
│   │   └── settings.txt   # Instance settings
│   └── logs/
│       └── bot_activity.log
```

### Settings Format
```ini
interval_minutes=5
admin_ids=123456789,987654321
auto_start=false
```

## ⚡ Quick Start Summary

```bash
# 1. Install Termux and setup environment
pkg update && pkg upgrade -y
pkg install -y python git openssl libffi clang

# 2. Clone and install
git clone https://github.com/pizdziaty-garfild/tpmb-android.git
cd tpmb-android
pip install -r requirements.txt

# 3. Create bot instance and configure
# Replace YOUR_TELEGRAM_ID and YOUR_BOT_TOKEN with actual values

# 4. Run your bot
python main.py --instance my_bot
```

## 🔮 Roadmap

- [ ] GUI interface for Android
- [ ] Push notification integration  
- [ ] Webhook support for instant messaging
- [ ] Advanced scheduling patterns
- [ ] Cloud configuration sync
- [ ] Performance analytics dashboard
- [ ] Voice message support
- [ ] Media file broadcasting

---

**Made with ❤️ for the Android community**

*Compatible with Android 7.0+ via Termux*