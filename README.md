# TPMB Android - Enhanced Telegram Bot for Android

**Enhanced multi-instance Telegram bot optimized for Android devices with military-grade security, resilient time handling, and remote control capabilities.**

## 🚀 Features

### ✨ New in Android Version

- **🔒 Military-Grade Security**: PBKDF2 encryption with 600,000 iterations (OWASP 2024)
- **📱 Android Optimized**: Specially tuned for Samsung Galaxy XCover 7 and Android 15
- **⚡ Multi-Instance Support**: Run multiple independent bot instances simultaneously
- **🌐 TLS 1.3 Enforcement**: Ultra-secure HTTPS connections with certificate validation
- **⏰ Resilient Time Handling**: NTP synchronization with DST awareness
- **🎛️ Remote Control**: Full bot management via Telegram commands (like tpmb2)
- **🔄 Network Resilience**: Automatic recovery from connection interruptions
- **📊 Resource Monitoring**: Real-time instance monitoring and management

### 🛑 Security Enhancements (2024 Standards)

- Enhanced PBKDF2 with 600,000 iterations (OWASP 2024 recommendation)
- Advanced rate limiting for security operations
- Encrypted token storage with metadata and versioning
- Certificate pinning and validation
- Protection against timing attacks and suspicious patterns
- Secure random key generation with enhanced entropy
- Automatic token rotation alerts
- Network security validation
- Input sanitization and validation
- Secure error handling without information leakage

### 🕒 Time & Scheduling Improvements

- Multi-server NTP synchronization (Polish and European servers)
- DST (Daylight Saving Time) automatic handling
- Network interruption tolerance
- Mobile-friendly timeout configurations
- Automatic time drift correction
- Timezone-aware scheduling

## 📱 Android Installation (Termux)

### Prerequisites

- **Android Device**: Samsung Galaxy XCover 7 (Android 15) or compatible
- **Termux**: Install from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended)
- **Internet Connection**: For downloading dependencies
- **Storage**: At least 500MB free space

### Step 1: Install Termux

Download Termux from F-Droid (recommended) or GitHub releases.

**⚠️ Important**: Use F-Droid version for best compatibility.

### Step 2: Quick Installation

```bash
# Open Termux and run:
curl -sL https://raw.githubusercontent.com/pizdziaty-garfild/tpmb-android/main/install_android.sh | bash
```

### Step 3: Manual Installation (Alternative)

```bash
# Update packages
pkg update && pkg upgrade -y

# Install required system packages
pkg install -y python python-dev git openssl openssl-dev libffi libffi-dev clang make cmake

# Install additional build tools
pkg install -y binutils libc++ pkg-config rust

# Update pip
python -m pip install --upgrade pip setuptools wheel

# Clone the repository
git clone https://github.com/pizdziaty-garfild/tpmb-android.git
cd tpmb-android

# Install dependencies
pip install -r requirements.txt

# Run configuration helper
python setup_bot.py
```

### Step 4: Configure Your Bot

```bash
# Run the configuration helper
python setup_bot.py
```

The helper will guide you through:
1. **Bot Token**: Get from @BotFather on Telegram
2. **Admin ID**: Get from @userinfobot on Telegram  
3. **Default Message**: Set your bot's message

### Step 5: Run Your Bot

```bash
# Start your bot instance
python main.py --instance default

# Or run in background
nohup python main.py --instance default > bot.log 2>&1 &
```

## 🎛️ Remote Control Commands (Enhanced like tpmb2)

Once running, control your bot via Telegram:

### 🎛️ Bot Control
- `/start_bot` - Start message broadcasting
- `/stop_bot` - Stop message broadcasting  
- `/restart` - Restart bot messaging
- `/status` - Get bot status and statistics
- `/info` - Get detailed bot information
- `/help` - Show all available commands

### ⏱️ Timing Control
- `/set_interval [minutes]` - Change message interval (1-1440 minutes)

### 👥 Group Management
- `/add_group [group_id]` - Add target group
- `/remove_group [group_id]` - Remove target group
- `/list_groups` - List configured groups

### 💬 Message Management
- `/set_message [text]` - Set bot message (up to 4000 characters)
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
python main.py --instance default &
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

### Enhanced Security Features (2024)

- **PBKDF2 Encryption**: 600,000 iterations (OWASP 2024 standard)
- **Rate Limiting**: Protection against brute force attacks
- **Input Validation**: Comprehensive sanitization of all inputs
- **TLS 1.3**: Enforced with strongest cipher suites
- **Certificate Validation**: Strict certificate checking
- **Secure Storage**: Atomic file operations with proper permissions

### Admin Authorization

```bash
# Add your Telegram ID to admin list
echo "admin_ids=123456789,987654321" >> instances/default/config/settings.txt
```

**💡 Get your Telegram ID**: Message @userinfobot on Telegram

### Token Security

- Tokens are automatically encrypted using PBKDF2 with 600,000 iterations
- Original plaintext tokens are securely deleted after migration
- Encrypted storage uses AES-256 with secure random salts
- Automatic backup creation during migration

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

## 🛐 Troubleshooting

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

**Termux Widget Setup:**
```bash
# Install Termux:Widget from F-Droid
# Use shortcuts: ~/.shortcuts/tpmb-start and ~/.shortcuts/tpmb-status
```

## 🔄 Migration from Original TPMB

### Import Existing Configuration

```bash
# If you have existing TPMB config, copy files:
cp ../tpmb/config/bot_token.txt instances/default/config/
cp ../tpmb/config/groups.txt instances/default/config/
cp ../tpmb/config/messages.txt instances/default/config/

# The bot will automatically encrypt the token on first run
```

## 🏁 Performance Optimization for Android

### Battery Optimization

- Reduced NTP sync frequency (1 hour intervals)
- Mobile-friendly network timeouts
- Efficient resource usage monitoring
- Smart scheduling with coalesced jobs
- Android 15 battery optimization compatibility

### Network Optimization

- Exponential backoff on failures
- Connection pooling and reuse
- Compressed HTTP responses
- Multiple NTP server fallbacks
- Mobile network interruption handling

### Memory Management

- Limited concurrent instances (5 max)
- Automatic cleanup of orphaned processes
- Efficient log rotation
- Resource monitoring per instance

## 📝 Configuration Files

### Instance Structure

```
instances/
├── registry.json # Instance registry
├── default/
│   ├── config/
│   │   ├── bot_token.enc # Encrypted token (PBKDF2 600k iterations)
│   │   ├── groups.txt # Target groups
│   │   ├── messages.txt # Bot messages
│   │   └── settings.txt # Instance settings
│   └── logs/
│       └── bot_activity.log
```

### Settings Format

```
interval_minutes=5
admin_ids=123456789,987654321
auto_start=false
```

## ⚡ Quick Start Summary

```bash
# 1. Install Termux from F-Droid
# 2. Run the installation script
curl -sL https://raw.githubusercontent.com/pizdziaty-garfild/tpmb-android/main/install_android.sh | bash

# 3. Configure your bot
cd tpmb-android
python setup_bot.py

# 4. Start your bot
python main.py --instance default
```

## 🔮 Roadmap

- GUI interface for Android
- Push notification integration
- Webhook support for instant messaging
- Advanced scheduling patterns
- Cloud configuration sync
- Performance analytics dashboard
- Voice message support
- Media file broadcasting
- Integration with Android system notifications

## 📱 Samsung Galaxy XCover 7 Optimizations

- **Battery Life**: Optimized intervals and network usage
- **Rugged Design**: Enhanced error handling for outdoor use
- **Android 15**: Full compatibility with latest Android features
- **Performance**: Tuned for mid-range hardware specifications
- **Security**: Enhanced protection for business/industrial use

## 🔒 Security Standards (2024)

- **OWASP Compliance**: Following latest security guidelines
- **PBKDF2**: 600,000 iterations (2024 recommendation)
- **TLS 1.3**: Latest encryption standards
- **Input Validation**: Comprehensive sanitization
- **Rate Limiting**: Protection against abuse
- **Secure Storage**: Encrypted configuration files

---

**Made with ❤️ for the Android community**

*Compatible with Android 7.0+ via Termux*  
*Optimized for Samsung Galaxy XCover 7 (Android 15)*

## About

Telegram Bot for Android - Enhanced version with multi-instance support, improved security (2024 standards), time handling, and remote control capabilities similar to tpmb2.

### Key Improvements over Original TPMB

- **Enhanced Security**: 600,000 PBKDF2 iterations, rate limiting, input validation
- **Remote Control**: Full Telegram command interface like tpmb2
- **Multi-Instance**: Run multiple bots simultaneously
- **Android Optimization**: Battery efficient, mobile network friendly
- **Error Handling**: Robust error recovery and logging
- **No License System**: Completely removed license requirements

### Resources

- **Repository**: [GitHub](https://github.com/pizdziaty-garfild/tpmb-android)
- **Issues**: Report bugs and request features
- **Releases**: Download stable versions
- **Wiki**: Detailed documentation and guides

## Languages

- **Python**: 100.0% (Enhanced with security improvements)