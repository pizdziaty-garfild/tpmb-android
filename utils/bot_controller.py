from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import AndroidTelegramBot

class BotController:
    """
    Remote control interface for Android TPMB via Telegram commands
    """
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.logger = logging.getLogger(__name__)
        
    def _is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to control bot"""
        return user_id in self.bot.admin_ids
        
    async def _deny_access(self, update: Update):
        """Deny access to unauthorized users"""
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "You are not authorized to control this bot.\n"
            "Contact the bot owner to get access.",
            parse_mode=ParseMode.HTML
        )
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start bot messaging"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if self.bot.messaging_active:
            await update.message.reply_text(
                "✅ <b>Already Running</b>\n\n"
                f"Bot is already sending messages every {self.bot.interval_minutes} minutes.",
                parse_mode=ParseMode.HTML
            )
            return
            
        await self.bot.start_messaging()
        await update.message.reply_text(
            "🚀 <b>Bot Started</b>\n\n"
            f"✅ Messaging activated\n"
            f"⏱️ Interval: {self.bot.interval_minutes} minutes\n"
            f"👥 Groups: {len(self.bot.groups)}\n"
            f"💬 Messages: {len(self.bot.messages)}",
            parse_mode=ParseMode.HTML
        )
        
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop bot messaging"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not self.bot.messaging_active:
            await update.message.reply_text(
                "⏹️ <b>Already Stopped</b>\n\n"
                "Bot messaging is not currently active.",
                parse_mode=ParseMode.HTML
            )
            return
            
        await self.bot.stop_messaging()
        await update.message.reply_text(
            "⏹️ <b>Bot Stopped</b>\n\n"
            "✅ Messaging deactivated\n"
            "ℹ️ Use /start_bot to resume",
            parse_mode=ParseMode.HTML
        )
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get bot status"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        status_emoji = "🟢" if self.bot.messaging_active else "🔴"
        status_text = "ACTIVE" if self.bot.messaging_active else "STOPPED"
        
        # Get last message time if available
        last_msg_info = ""
        if hasattr(self.bot.scheduler, 'get_job'):
            try:
                job = self.bot.scheduler.get_job(f'messaging_{self.bot.instance_name}')
                if job and job.next_run_time:
                    last_msg_info = f"🕐 Next message: {job.next_run_time.strftime('%H:%M:%S')}\n"
            except:
                pass
                
        await update.message.reply_text(
            f"📊 <b>Bot Status - {self.bot.instance_name.upper()}</b>\n\n"
            f"{status_emoji} Status: <b>{status_text}</b>\n"
            f"⏱️ Interval: {self.bot.interval_minutes} minutes\n"
            f"👥 Groups: {len(self.bot.groups)}\n" 
            f"💬 Messages: {len(self.bot.messages)}\n"
            f"{last_msg_info}"
            f"🔒 Security: ENABLED\n"
            f"📱 Platform: Android\n"
            f"🌐 TLS: ENFORCED",
            parse_mode=ParseMode.HTML
        )
        
    async def set_interval_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set message interval"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not context.args:
            await update.message.reply_text(
                "⏱️ <b>Set Interval</b>\n\n"
                f"Current interval: <b>{self.bot.interval_minutes} minutes</b>\n\n"
                "Usage: <code>/set_interval [minutes]</code>\n"
                "Example: <code>/set_interval 5</code>",
                parse_mode=ParseMode.HTML
            )
            return
            
        try:
            minutes = int(context.args[0])
            if minutes < 1:
                raise ValueError("Interval must be at least 1 minute")
                
            old_interval = self.bot.interval_minutes
            self.bot.interval_minutes = minutes
            
            # Update running job if active
            if self.bot.messaging_active:
                await self.bot.stop_messaging()
                await self.bot.start_messaging()
                
            # Save configuration
            self.bot.save_config()
            
            await update.message.reply_text(
                f"✅ <b>Interval Updated</b>\n\n"
                f"Previous: {old_interval} minutes\n"
                f"New: <b>{minutes} minutes</b>\n\n"
                f"{'🔄 Messaging restarted with new interval' if self.bot.messaging_active else 'ℹ️ Changes will apply when messaging starts'}",
                parse_mode=ParseMode.HTML
            )
            
        except ValueError as e:
            await update.message.reply_text(
                f"❌ <b>Invalid Interval</b>\n\n"
                f"Error: {str(e)}\n\n"
                "Please provide a number ≥ 1",
                parse_mode=ParseMode.HTML
            )
            
    async def add_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add group to messaging list"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not context.args:
            await update.message.reply_text(
                "👥 <b>Add Group</b>\n\n"
                "Usage: <code>/add_group [group_id]</code>\n"
                "Example: <code>/add_group -1001234567890</code>\n\n"
                "💡 Tip: Forward a message from the target group to get its ID",
                parse_mode=ParseMode.HTML
            )
            return
            
        try:
            group_id = context.args[0]
            
            # Validate it's a negative number (group ID format)
            if not (group_id.startswith('-') and group_id[1:].isdigit()):
                raise ValueError("Group ID must be negative number")
                
            if group_id in self.bot.groups:
                await update.message.reply_text(
                    f"⚠️ <b>Group Already Added</b>\n\n"
                    f"Group <code>{group_id}</code> is already in the list",
                    parse_mode=ParseMode.HTML
                )
                return
                
            self.bot.groups.append(group_id)
            self.bot.save_config()
            
            await update.message.reply_text(
                f"✅ <b>Group Added</b>\n\n"
                f"Group ID: <code>{group_id}</code>\n"
                f"Total groups: {len(self.bot.groups)}",
                parse_mode=ParseMode.HTML
            )
            
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ <b>Invalid Group ID</b>\n\n"
                "Please provide a valid group ID (negative number)\n"
                "Example: <code>-1001234567890</code>",
                parse_mode=ParseMode.HTML
            )
            
    async def remove_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove group from messaging list"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not context.args:
            if not self.bot.groups:
                await update.message.reply_text(
                    "📭 <b>No Groups Configured</b>\n\n"
                    "No groups to remove. Use /add_group to add some.",
                    parse_mode=ParseMode.HTML
                )
                return
                
            groups_list = "\n".join([f"• <code>{g}</code>" for g in self.bot.groups])
            await update.message.reply_text(
                f"👥 <b>Remove Group</b>\n\n"
                f"Current groups:\n{groups_list}\n\n"
                f"Usage: <code>/remove_group [group_id]</code>",
                parse_mode=ParseMode.HTML
            )
            return
            
        try:
            group_id = context.args[0]
            
            if group_id not in self.bot.groups:
                await update.message.reply_text(
                    f"❌ <b>Group Not Found</b>\n\n"
                    f"Group <code>{group_id}</code> is not in the list",
                    parse_mode=ParseMode.HTML
                )
                return
                
            self.bot.groups.remove(group_id)
            self.bot.save_config()
            
            await update.message.reply_text(
                f"✅ <b>Group Removed</b>\n\n"
                f"Group ID: <code>{group_id}</code>\n"
                f"Remaining groups: {len(self.bot.groups)}",
                parse_mode=ParseMode.HTML
            )
            
        except IndexError:
            await update.message.reply_text(
                "❌ <b>Missing Group ID</b>\n\n"
                "Please specify which group to remove",
                parse_mode=ParseMode.HTML
            )
            
    async def list_groups_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all configured groups"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not self.bot.groups:
            await update.message.reply_text(
                "📭 <b>No Groups Configured</b>\n\n"
                "Use /add_group to add target groups for messaging.",
                parse_mode=ParseMode.HTML
            )
            return
            
        groups_list = "\n".join([f"{i+1}. <code>{group}</code>" for i, group in enumerate(self.bot.groups)])
        
        await update.message.reply_text(
            f"👥 <b>Configured Groups ({len(self.bot.groups)})</b>\n\n"
            f"{groups_list}\n\n"
            f"💡 Use /remove_group to remove groups",
            parse_mode=ParseMode.HTML
        )
        
    async def set_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set bot message"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not context.args:
            await update.message.reply_text(
                "💬 <b>Set Message</b>\n\n"
                "Usage: <code>/set_message [your message]</code>\n"
                "Example: <code>/set_message Hello everyone!</code>\n\n"
                "💡 The message will replace current messages",
                parse_mode=ParseMode.HTML
            )
            return
            
        new_message = ' '.join(context.args)
        
        if len(new_message) > 4000:  # Telegram limit
            await update.message.reply_text(
                "❌ <b>Message Too Long</b>\n\n"
                f"Message length: {len(new_message)} characters\n"
                "Maximum allowed: 4000 characters",
                parse_mode=ParseMode.HTML
            )
            return
            
        self.bot.messages = [new_message]
        self.bot.save_config()
        
        preview = new_message[:100] + "..." if len(new_message) > 100 else new_message
        
        await update.message.reply_text(
            f"✅ <b>Message Updated</b>\n\n"
            f"Preview: <i>{preview}</i>\n\n"
            f"Length: {len(new_message)} characters",
            parse_mode=ParseMode.HTML
        )
        
    async def get_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get current bot message"""
        if not self._is_authorized(update.effective_user.id):
            return await self._deny_access(update)
            
        if not self.bot.messages:
            await update.message.reply_text(
                "📭 <b>No Messages Configured</b>\n\n"
                "Use /set_message to configure a message.",
                parse_mode=ParseMode.HTML
            )
            return
            
        current_message = self.bot.messages[0] if len(self.bot.messages) == 1 else "Multiple messages configured"
        
        await update.message.reply_text(
            f"💬 <b>Current Message</b>\n\n"
            f"<code>{current_message}</code>\n\n"
            f"Length: {len(current_message)} characters",
            parse_mode=ParseMode.HTML
        )
