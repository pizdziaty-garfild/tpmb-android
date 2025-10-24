import asyncio
import logging
import random
import os
import json
import signal
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import colorama
from colorama import Fore, Style
from utils.time_handler import ResilientScheduler
from utils.security_manager import SecurityManager, SecureConfigManager, SecurityError
from utils.bot_controller import BotController
from utils.multi_instance_manager import MultiInstanceManager

# Initialize colors
colorama.init()

class AndroidTelegramBot:
    """
    Enhanced TPMB for Android with:
    - Multi-instance support for running multiple bots
    - Resilient time handling (NTP sync, DST tolerance) 
    - TLS/HTTPS encryption with certificate validation
    - Remote bot control via Telegram commands
    - Secure token management
    - Network error handling with retry logic
    - Enhanced security (2024 standards)
    """
    
    def __init__(self, instance_name: str = "default"):
        self.instance_name = instance_name
        self.config_dir = Path(f"instances/{instance_name}/config")
        self.logs_dir = Path(f"instances/{instance_name}/logs")
        self.start_time = datetime.now()
        
        # Create instance directories
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_logging()
        self.security_manager = SecurityManager()
        self.config_manager = SecureConfigManager(self.security_manager, self.config_dir)
        self.scheduler = ResilientScheduler()
        self.bot_controller = BotController(self)
        
        self.bot = None
        self.app = None
        self.is_running = False
        self.messaging_active = False
        
        # Android-compatible signal handling
        self._setup_signal_handlers()
        
        self.load_config()
        
    def setup_logging(self):
        """Setup instance-specific logging"""
        log_file = self.logs_dir / 'bot_activity.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{self.instance_name}] %(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Reduce telegram library verbosity 
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        
        self.logger = logging.getLogger(__name__)
        
    def _setup_signal_handlers(self):
        """Setup Android-compatible signal handlers"""
        try:
            # Standard signals
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Android-specific handling
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, self._signal_handler)
                
        except (AttributeError, OSError) as e:
            self.logger.warning(f"Some signal handlers not available on this platform: {e}")
        
    def load_config(self):
        """Load configuration with enhanced error handling"""
        try:
            # Migrate from plaintext if needed
            try:
                self.config_manager.migrate_plaintext_token()
            except SecurityError as e:
                self.logger.error(f"Token migration failed: {e}")
            
            # Load messages with validation
            messages_file = self.config_dir / 'messages.txt'
            if messages_file.exists():
                try:
                    with open(messages_file, 'r', encoding='utf-8') as f:
                        messages = [line.strip() for line in f if line.strip()]
                        # Sanitize messages
                        self.messages = [self._sanitize_message(msg) for msg in messages if msg]
                except Exception as e:
                    self.logger.error(f"Failed to load messages: {e}")
                    self.messages = ["Default message"]
            else:
                self.messages = ["Testowa wiadomość"]
                
            # Load groups with validation
            groups_file = self.config_dir / 'groups.txt'
            if groups_file.exists():
                try:
                    with open(groups_file, 'r', encoding='utf-8') as f:
                        groups = [line.strip() for line in f if line.strip()]
                        # Validate group IDs
                        self.groups = [group for group in groups if self._validate_group_id(group)]
                except Exception as e:
                    self.logger.error(f"Failed to load groups: {e}")
                    self.groups = []
            else:
                self.groups = []
                
            # Load settings with validation
            settings_file = self.config_dir / 'settings.txt'
            self.interval_minutes = 5  # Default safe interval
            self.admin_ids = []
            
            if settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                if key == 'interval_minutes':
                                    try:
                                        interval = int(value)
                                        if 1 <= interval <= 1440:  # 1 minute to 24 hours
                                            self.interval_minutes = interval
                                    except ValueError:
                                        self.logger.warning(f"Invalid interval value: {value}")
                                        
                                elif key == 'admin_ids':
                                    try:
                                        admin_ids = [int(x.strip()) for x in value.split(',') if x.strip().isdigit()]
                                        # Validate admin IDs (reasonable Telegram user ID range)
                                        self.admin_ids = [uid for uid in admin_ids if 1 <= uid <= 9999999999]
                                    except ValueError:
                                        self.logger.warning(f"Invalid admin IDs: {value}")
                except Exception as e:
                    self.logger.error(f"Failed to load settings: {e}")
                    
        except Exception as e:
            self.logger.error(f"Config loading failed: {e}")
            # Fallback values
            self.messages = ["Fallback message"]
            self.groups = []
            self.interval_minutes = 5
            self.admin_ids = []
            
    def _sanitize_message(self, message: str) -> str:
        """Sanitize message content for security"""
        if not message or len(message) > 4000:
            return "Invalid message"
            
        # Remove potentially dangerous characters but keep Telegram formatting
        # Allow basic Telegram HTML tags
        allowed_pattern = re.compile(r'[^<>&\n\r\t\x00-\x1f\x7f-\x9f]|</?[bi]>|</?code>|</?pre>', re.IGNORECASE)
        sanitized = ''.join(allowed_pattern.findall(message))
        
        return sanitized[:4000]  # Telegram limit
        
    def _validate_group_id(self, group_id: str) -> bool:
        """Validate Telegram group ID format"""
        if not group_id:
            return False
            
        # Telegram group IDs are negative numbers, often starting with -100
        if group_id.startswith('-') and group_id[1:].isdigit():
            try:
                gid = int(group_id)
                # Reasonable range for Telegram group IDs
                return -9999999999999 <= gid <= -1
            except ValueError:
                return False
        return False
            
    def save_config(self):
        """Save current configuration to files with error handling"""
        try:
            # Save messages
            with open(self.config_dir / 'messages.txt', 'w', encoding='utf-8') as f:
                for message in self.messages:
                    sanitized = self._sanitize_message(message)
                    f.write(sanitized + '\n')
                
            # Save groups
            with open(self.config_dir / 'groups.txt', 'w', encoding='utf-8') as f:
                for group in self.groups:
                    if self._validate_group_id(group):
                        f.write(group + '\n')
                
            # Save settings
            with open(self.config_dir / 'settings.txt', 'w', encoding='utf-8') as f:
                f.write(f"interval_minutes={self.interval_minutes}\n")
                f.write(f"admin_ids={','.join(map(str, self.admin_ids))}\n")
                
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            
    async def initialize(self):
        """Secure bot initialization with enhanced error handling"""
        try:
            # Setup secure directories
            self.config_manager.setup_secure_directories()
            
            # Create secure bot for messaging
            try:
                token = self.config_manager.get_token()
                self.bot = await self.security_manager.create_secure_bot(token)
            except SecurityError as e:
                self.logger.error(f"Failed to create secure bot: {e}")
                return False
            
            # Create application for command handling
            self.app = Application.builder().bot(self.bot).build()
            
            # Add command handlers
            await self._setup_command_handlers()
            
            # Verify connections
            if not await self.security_manager.verify_bot_connection(self.bot):
                self.logger.error("Bot connection verification failed")
                return False
                
            # Initialize scheduler
            await self.scheduler.initialize()
            
            self.is_running = True
            self.logger.info("Bot initialized successfully with enhanced security")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
            
    async def _setup_command_handlers(self):
        """Setup Telegram command handlers for remote control"""
        handlers = [
            CommandHandler("start_bot", self.bot_controller.start_command),
            CommandHandler("stop_bot", self.bot_controller.stop_command),
            CommandHandler("status", self.bot_controller.status_command),
            CommandHandler("set_interval", self.bot_controller.set_interval_command),
            CommandHandler("add_group", self.bot_controller.add_group_command),
            CommandHandler("remove_group", self.bot_controller.remove_group_command),
            CommandHandler("list_groups", self.bot_controller.list_groups_command),
            CommandHandler("set_message", self.bot_controller.set_message_command),
            CommandHandler("get_message", self.bot_controller.get_message_command),
            # Additional control commands
            CommandHandler("restart", self.bot_controller.restart_command),
            CommandHandler("help", self.bot_controller.help_command),
            CommandHandler("info", self.bot_controller.info_command),
        ]
        
        for handler in handlers:
            self.app.add_handler(handler)
            
    async def send_messages_with_retry(self, max_retries: int = 3):
        """Send messages with retry logic and error handling"""
        if not self.messages or not self.groups:
            self.logger.warning("No messages or groups configured")
            return
            
        message = random.choice(self.messages)
        successful_sends = 0
        
        for group_id in self.groups:
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    await self.bot.send_message(chat_id=group_id, text=message)
                    self.logger.info(f"Message sent to group {group_id}")
                    print(f"{Fore.GREEN}✓ Sent to: {group_id}{Style.RESET_ALL}")
                    successful_sends += 1
                    break
                    
                except Exception as e:
                    retry_count += 1
                    self.logger.warning(f"Send error to {group_id} (attempt {retry_count}): {e}")
                    
                    if retry_count < max_retries:
                        # Exponential backoff
                        wait_time = 2 ** retry_count
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.error(f"Final send error for group {group_id}: {e}")
                        print(f"{Fore.RED}✗ Failed {group_id}: {e}{Style.RESET_ALL}")
                        
        print(f"{Fore.CYAN}Batch complete: {successful_sends}/{len(self.groups)} sent{Style.RESET_ALL}")
        
    async def start_messaging(self):
        """Start scheduled messaging"""
        if self.messaging_active:
            return
            
        self.messaging_active = True
        
        # Add messaging job
        self.scheduler.add_job(
            self.send_messages_with_retry,
            'interval',
            minutes=self.interval_minutes,
            id=f'messaging_{self.instance_name}',
            replace_existing=True
        )
        
        await self.scheduler.start()
        self.logger.info(f"Messaging started with {self.interval_minutes}min interval")
        
    async def stop_messaging(self):
        """Stop scheduled messaging"""
        if not self.messaging_active:
            return
            
        self.messaging_active = False
        
        # Remove messaging job
        try:
            self.scheduler.remove_job(f'messaging_{self.instance_name}')
        except:
            pass
            
        self.logger.info("Messaging stopped")
        
    async def restart_messaging(self):
        """Restart messaging system"""
        was_active = self.messaging_active
        await self.stop_messaging()
        if was_active:
            await self.start_messaging()
            self.logger.info("Messaging restarted")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"{Fore.YELLOW}Received signal {signum}, shutting down...{Style.RESET_ALL}")
        asyncio.create_task(self.shutdown())
        
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Starting graceful shutdown...")
        
        try:
            # Stop messaging
            await self.stop_messaging()
            
            # Stop scheduler
            if self.scheduler:
                self.scheduler.shutdown()
                
            # Stop application
            if self.app:
                await self.app.stop()
                await self.app.shutdown()
                
            # Close bot session
            if self.bot and hasattr(self.bot, '_session'):
                await self.bot._session.close()
                
            self.is_running = False
            self.logger.info("Shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
            
    async def run(self):
        """Main run loop"""
        if not await self.initialize():
            print(f"{Fore.RED}Initialization failed for instance {self.instance_name}{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}=== TPMB ANDROID [{self.instance_name.upper()}] ==={Style.RESET_ALL}")
        print(f"📱 Android optimized: YES") 
        print(f"🔒 Security: ENHANCED (2024 standards)")
        print(f"⏰ Time sync: ACTIVE")
        print(f"🌐 TLS/HTTPS: ENFORCED")
        print(f"📊 Instance: {self.instance_name}")
        print(f"⏱️  Interval: {self.interval_minutes} min")
        print(f"👥 Groups: {len(self.groups)}")
        print(f"💬 Messages: {len(self.messages)}")
        print(f"🎛️  Remote control: ENABLED")
        print(f"{Fore.GREEN}Ready! Use Telegram commands to control the bot{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}")
        
        try:
            # Start application for command handling
            await self.app.initialize()
            await self.app.start()
            
            # Keep running
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            pass
        finally:
            await self.shutdown()

def main():
    """Main entry point with multi-instance support"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TPMB Android - Multi-instance Telegram Bot')
    parser.add_argument('--instance', '-i', default='default', help='Instance name (default: default)')
    parser.add_argument('--list-instances', action='store_true', help='List all instances')
    
    args = parser.parse_args()
    
    if args.list_instances:
        instances_dir = Path('instances')
        if instances_dir.exists():
            instances = [d.name for d in instances_dir.iterdir() if d.is_dir()]
            print(f"Available instances: {', '.join(instances) if instances else 'None'}")
        else:
            print("No instances directory found")
        return
        
    bot = AndroidTelegramBot(args.instance)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}Bot stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Bot crashed: {e}{Style.RESET_ALL}")
        
if __name__ == "__main__":
    main()