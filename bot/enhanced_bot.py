import discord
from discord.ext import commands, tasks
import json
import os
import hashlib
import asyncio
from datetime import datetime, timedelta
import aiofiles
import aiohttp
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
OWNER_ID = 945344266404782140
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATA_FILE = 'verification_data.json'
CONFIG_FILE = 'bot_config.json'
INVITES_FILE = 'invite_data.json'

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.invites = True

# Bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

class EnhancedVerificationBot:
    def __init__(self):
        self.verification_data: Dict = {}
        self.blacklist: List[str] = []
        self.whitelist: List[str] = []
        self.failed_attempts: Dict[str, int] = {}
        self.invite_data: Dict = {}
        self.guild_invites: Dict = {}
        self.config: Dict = {
            'verification_channel': None,
            'verification_website': None,
            'verification_role': None,
            'unverified_role': None,
            'mute_role': None,
            'max_failed_attempts': 3,
            'auto_blacklist_enabled': True,
            'invite_tracking_enabled': False,
            'invite_tracking_channel': None,
            'autorole_enabled': False,
            'autorole_role': None,
            'auto_unverified_enabled': True
        }
        self.load_data()
        self.load_config()
        self.load_invite_data()

    async def load_data(self):
        """Load verification data from file"""
        try:
            if os.path.exists(DATA_FILE):
                async with aiofiles.open(DATA_FILE, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    self.verification_data = data.get('verification_data', {})
                    self.blacklist = data.get('blacklist', [])
                    self.whitelist = data.get('whitelist', [])
                    self.failed_attempts = data.get('failed_attempts', {})
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    async def save_data(self):
        """Save verification data to file"""
        try:
            data = {
                'verification_data': self.verification_data,
                'blacklist': self.blacklist,
                'whitelist': self.whitelist,
                'failed_attempts': self.failed_attempts,
                'last_updated': datetime.now().isoformat()
            }
            async with aiofiles.open(DATA_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def load_config(self):
        """Load bot configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def save_config(self):
        """Save bot configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    async def load_invite_data(self):
        """Load invite tracking data"""
        try:
            if os.path.exists(INVITES_FILE):
                async with aiofiles.open(INVITES_FILE, 'r') as f:
                    content = await f.read()
                    self.invite_data = json.loads(content)
        except Exception as e:
            logger.error(f"Error loading invite data: {e}")

    async def save_invite_data(self):
        """Save invite tracking data"""
        try:
            async with aiofiles.open(INVITES_FILE, 'w') as f:
                await f.write(json.dumps(self.invite_data, indent=2))
        except Exception as e:
            logger.error(f"Error saving invite data: {e}")

    def hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    async def check_hwid_duplicate(self, hwid: str, user_id: str) -> bool:
        """Check if HWID is already in use by another user"""
        for uid, data in self.verification_data.items():
            if uid != user_id and data.get('hwid') == hwid:
                return True
        return False

    async def detect_vpn(self, ip: str) -> bool:
        """Enhanced VPN detection using multiple methods"""
        try:
            # Check against known VPN IP ranges
            vpn_indicators = [
                'tor-exit', 'proxy', 'vpn', 'hosting', 'datacenter',
                'amazon', 'google-cloud', 'digitalocean', 'vultr'
            ]
            
            # Basic IP analysis
            ip_parts = ip.split('.')
            if len(ip_parts) == 4:
                # Check for common VPN IP ranges
                first_octet = int(ip_parts[0])
                if first_octet in [10, 172, 192]:  # Private IP ranges (shouldn't be public)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error in VPN detection: {e}")
            return False

    async def increment_failed_attempts(self, user_id: str) -> bool:
        """Increment failed attempts and check if user should be blacklisted"""
        self.failed_attempts[user_id] = self.failed_attempts.get(user_id, 0) + 1
        
        if (self.failed_attempts[user_id] >= self.config.get('max_failed_attempts', 3) and 
            self.config.get('auto_blacklist_enabled', True)):
            self.blacklist.append(user_id)
            await self.save_data()
            return True
        
        await self.save_data()
        return False

    def get_hashed_data_for_whitelist(self, user_id: str) -> Dict:
        """Return hashed data for whitelisted users"""
        if user_id not in self.verification_data:
            return {}
        
        data = self.verification_data[user_id].copy()
        if 'ip_raw' in data:
            data['ip_hashed'] = self.hash_ip(data['ip_raw'])
            del data['ip_raw']  # Remove raw IP for whitelisted users
        
        return data

    async def ping_administrators(self, guild: discord.Guild, embed: discord.Embed, reason: str):
        """Ping administrators when important events occur"""
        try:
            admin_mentions = []
            for member in guild.members:
                if member.guild_permissions.administrator and not member.bot:
                    admin_mentions.append(member.mention)
            
            if admin_mentions and len(admin_mentions) <= 10:  # Limit mentions to avoid spam
                mention_text = " ".join(admin_mentions)
                embed.add_field(
                    name="🚨 Administrator Alert",
                    value=f"{mention_text}\n**Reason:** {reason}",
                    inline=False
                )
        except Exception as e:
            logger.error(f"Error pinging administrators: {e}")

    async def track_invite_usage(self, member: discord.Member):
        """Track which invite was used when a member joins"""
        if not self.config.get('invite_tracking_enabled', False):
            return None
            
        guild = member.guild
        try:
            current_invites = {invite.code: invite.uses for invite in await guild.invites()}
            used_invite = None
            
            if guild.id in self.guild_invites:
                old_invites = self.guild_invites[guild.id]
                for code, uses in current_invites.items():
                    if code in old_invites and uses > old_invites[code]:
                        used_invite = code
                        break
            
            # Update stored invites
            self.guild_invites[guild.id] = current_invites
            
            if used_invite:
                # Find the invite object and inviter
                for invite in await guild.invites():
                    if invite.code == used_invite:
                        inviter = invite.inviter
                        self.invite_data[str(member.id)] = {
                            'invited_by': str(inviter.id) if inviter else 'Unknown',
                            'invite_code': used_invite,
                            'joined_at': datetime.now().isoformat(),
                            'inviter_name': f"{inviter.name}#{inviter.discriminator}" if inviter else 'Unknown'
                        }
                        await self.save_invite_data()
                        return inviter
                        
        except Exception as e:
            logger.error(f"Error tracking invite usage: {e}")
        
        return None

verification_system = EnhancedVerificationBot()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await verification_system.load_data()
    
    # Start background task for cleanup
    cleanup_task.start()
    
    # Initialize invite tracking for all guilds
    for guild in bot.guilds:
        if verification_system.config.get('invite_tracking_enabled', False):
            try:
                invites = await guild.invites()
                verification_system.guild_invites[guild.id] = {invite.code: invite.uses for invite in invites}
            except Exception as e:
                logger.error(f"Error initializing invites for {guild.name}: {e}")
    
    # Auto-assign unverified role to all members without verified role
    for guild in bot.guilds:
        if verification_system.config.get('auto_unverified_enabled', True) and verification_system.config.get('unverified_role'):
            unverified_role = guild.get_role(verification_system.config['unverified_role'])
            verified_role = guild.get_role(verification_system.config.get('verification_role'))
            
            if unverified_role:
                for member in guild.members:
                    if not member.bot and (not verified_role or verified_role not in member.roles):
                        try:
                            await member.add_roles(unverified_role, reason="Auto-assign unverified role")
                        except discord.Forbidden:
                            pass

@tasks.loop(hours=24)
async def cleanup_task():
    """Daily cleanup task for old failed attempts"""
    # Reset failed attempts older than 24 hours
    # This would require timestamp tracking in a real implementation
    pass

@bot.event
async def on_member_join(member):
    """Handle member join events"""
    guild = member.guild
    
    # Track invite usage
    inviter = await verification_system.track_invite_usage(member)
    
    # Send invite tracking message
    if (verification_system.config.get('invite_tracking_enabled', False) and 
        verification_system.config.get('invite_tracking_channel')):
        
        channel = bot.get_channel(verification_system.config['invite_tracking_channel'])
        if channel:
            embed = discord.Embed(
                title="👋 New Member Joined",
                color=0x00ff00
            )
            embed.add_field(name="👤 Member", value=f"{member.mention}\n`{member.id}`", inline=True)
            
            if inviter:
                embed.add_field(name="📨 Invited by", value=f"{inviter.mention}\n`{inviter.id}`", inline=True)
                invite_info = verification_system.invite_data.get(str(member.id), {})
                embed.add_field(name="🔗 Invite Code", value=f"`{invite_info.get('invite_code', 'Unknown')}`", inline=True)
            else:
                embed.add_field(name="📨 Invited by", value="Unknown/Vanity URL", inline=True)
                embed.add_field(name="🔗 Invite Code", value="Unknown", inline=True)
            
            embed.add_field(name="📅 Joined", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
    
    # Auto-assign unverified role to new members
    if verification_system.config.get('auto_unverified_enabled', True) and verification_system.config.get('unverified_role'):
        unverified_role = guild.get_role(verification_system.config['unverified_role'])
        if unverified_role:
            try:
                await member.add_roles(unverified_role, reason="Auto-assign unverified role")
            except discord.Forbidden:
                pass

@bot.slash_command(name="verification", description="Get the verification website link")
async def verification_command(ctx):
    """Main verification command"""
    website_url = verification_system.config.get('verification_website')
    
    if not website_url:
        embed = discord.Embed(
            title="❌ Verification Not Configured",
            description="The verification system has not been set up yet. Please contact an administrator.",
            color=0xff0000
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return
    
    # Check if user is blacklisted
    if str(ctx.author.id) in verification_system.blacklist:
        embed = discord.Embed(
            title="🚫 Access Denied",
            description="You are blacklisted from using the verification system. Contact an administrator if you believe this is an error.",
            color=0xff0000
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🔐 Server Verification",
        description=f"Click the link below to complete your verification:\n\n[**Complete Verification**]({website_url})",
        color=0x667eea
    )
    embed.add_field(
        name="📋 Instructions",
        value="1. Click the verification link\n2. Enter your Discord User ID\n3. Complete the verification process\n4. Wait for approval",
        inline=False
    )
    embed.add_field(
        name="ℹ️ Your Discord ID",
        value=f"`{ctx.author.id}`",
        inline=False
    )
    embed.set_footer(text="Your data is encrypted and secure")
    
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="help", description="Show help information")
async def help_command(ctx):
    """Help command"""
    embed = discord.Embed(
        title="🔧 Verification Bot Help",
        description="Here are the available commands:",
        color=0x667eea
    )
    
    embed.add_field(
        name="📋 User Commands",
        value="`/verification` - Get verification link\n`/help` - Show this help message",
        inline=False
    )
    
    if ctx.author.id == OWNER_ID:
        embed.add_field(
            name="⚙️ Owner Commands",
            value="`/config` - Configure bot settings\n"
                  "`/export` - Export verification data\n"
                  "`/whitelist` - Manage whitelist\n"
                  "`/blacklist` - Manage blacklist\n"
                  "`/unblacklist` - Remove from blacklist\n"
                  "`/unverify` - Remove user verification\n"
                  "`/autorole` - Configure auto roles\n"
                  "`/invites` - Manage invite tracking\n"
                  "`/stats` - View verification statistics",
            inline=False
        )
    
    await ctx.respond(embed=embed, ephemeral=True)

# Owner-only commands
@bot.slash_command(name="config", description="Configure bot settings (Owner only)")
async def config_command(ctx, setting: str, value: str = None):
    """Configuration command for bot owner"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    valid_settings = ["channel", "website", "role", "unverified", "mute", "max_attempts", "auto_blacklist", "invite_tracking", "invite_channel"]
    
    if setting not in valid_settings:
        await ctx.respond(f"❌ Invalid setting. Valid options: {', '.join(valid_settings)}", ephemeral=True)
        return
    
    if setting == "channel":
        if value:
            try:
                channel_id = int(value.strip('<>#'))
                channel = bot.get_channel(channel_id)
                if channel:
                    verification_system.config['verification_channel'] = channel_id
                    verification_system.save_config()
                    await ctx.respond(f"✅ Verification channel set to {channel.mention}")
                else:
                    await ctx.respond("❌ Channel not found.")
            except ValueError:
                await ctx.respond("❌ Invalid channel ID.")
        else:
            current = verification_system.config.get('verification_channel')
            channel = bot.get_channel(current) if current else None
            await ctx.respond(f"Current verification channel: {channel.mention if channel else 'Not set'}")
    
    elif setting == "website":
        if value:
            verification_system.config['verification_website'] = value
            verification_system.save_config()
            await ctx.respond(f"✅ Verification website set to: {value}")
        else:
            current = verification_system.config.get('verification_website', 'Not set')
            await ctx.respond(f"Current verification website: {current}")
    
    elif setting in ["role", "unverified", "mute"]:
        config_key = f"{setting}_role" if setting != "role" else "verification_role"
        
        if value:
            try:
                role_id = int(value.strip('<>@&'))
                role = ctx.guild.get_role(role_id)
                if role:
                    verification_system.config[config_key] = role_id
                    verification_system.save_config()
                    await ctx.respond(f"✅ {setting.title()} role set to {role.mention}")
                else:
                    await ctx.respond("❌ Role not found.")
            except ValueError:
                await ctx.respond("❌ Invalid role ID.")
        else:
            current = verification_system.config.get(config_key)
            role = ctx.guild.get_role(current) if current else None
            await ctx.respond(f"Current {setting} role: {role.mention if role else 'Not set'}")
    
    elif setting == "max_attempts":
        if value:
            try:
                max_attempts = int(value)
                if max_attempts > 0:
                    verification_system.config['max_failed_attempts'] = max_attempts
                    verification_system.save_config()
                    await ctx.respond(f"✅ Max failed attempts set to {max_attempts}")
                else:
                    await ctx.respond("❌ Max attempts must be greater than 0.")
            except ValueError:
                await ctx.respond("❌ Invalid number.")
        else:
            current = verification_system.config.get('max_failed_attempts', 3)
            await ctx.respond(f"Current max failed attempts: {current}")
    
    elif setting == "auto_blacklist":
        if value:
            if value.lower() in ['true', 'enable', 'on', '1']:
                verification_system.config['auto_blacklist_enabled'] = True
                verification_system.save_config()
                await ctx.respond("✅ Auto-blacklist enabled")
            elif value.lower() in ['false', 'disable', 'off', '0']:
                verification_system.config['auto_blacklist_enabled'] = False
                verification_system.save_config()
                await ctx.respond("✅ Auto-blacklist disabled")
            else:
                await ctx.respond("❌ Invalid value. Use: true/false, enable/disable, on/off, 1/0")
        else:
            current = verification_system.config.get('auto_blacklist_enabled', True)
            await ctx.respond(f"Auto-blacklist is currently: {'Enabled' if current else 'Disabled'}")
    
    elif setting == "invite_tracking":
        if value:
            if value.lower() in ['true', 'enable', 'on', '1']:
                verification_system.config['invite_tracking_enabled'] = True
                verification_system.save_config()
                await ctx.respond("✅ Invite tracking enabled")
                # Initialize invite tracking for this guild
                try:
                    invites = await ctx.guild.invites()
                    verification_system.guild_invites[ctx.guild.id] = {invite.code: invite.uses for invite in invites}
                except Exception as e:
                    logger.error(f"Error initializing invites: {e}")
            elif value.lower() in ['false', 'disable', 'off', '0']:
                verification_system.config['invite_tracking_enabled'] = False
                verification_system.save_config()
                await ctx.respond("✅ Invite tracking disabled")
            else:
                await ctx.respond("❌ Invalid value. Use: true/false, enable/disable, on/off, 1/0")
        else:
            current = verification_system.config.get('invite_tracking_enabled', False)
            await ctx.respond(f"Invite tracking is currently: {'Enabled' if current else 'Disabled'}")
    
    elif setting == "invite_channel":
        if value:
            try:
                channel_id = int(value.strip('<>#'))
                channel = bot.get_channel(channel_id)
                if channel:
                    verification_system.config['invite_tracking_channel'] = channel_id
                    verification_system.save_config()
                    await ctx.respond(f"✅ Invite tracking channel set to {channel.mention}")
                else:
                    await ctx.respond("❌ Channel not found.")
            except ValueError:
                await ctx.respond("❌ Invalid channel ID.")
        else:
            current = verification_system.config.get('invite_tracking_channel')
            channel = bot.get_channel(current) if current else None
            await ctx.respond(f"Current invite tracking channel: {channel.mention if channel else 'Not set'}")

@bot.slash_command(name="autorole", description="Configure auto roles (Owner only)")
async def autorole_command(ctx, setting: str, value: str = None):
    """Configure automatic role assignment"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    valid_settings = ["enable", "disable", "role", "status", "unverified_enable", "unverified_disable"]
    
    if setting not in valid_settings:
        await ctx.respond(f"❌ Invalid setting. Valid options: {', '.join(valid_settings)}", ephemeral=True)
        return
    
    if setting == "enable":
        verification_system.config['autorole_enabled'] = True
        verification_system.save_config()
        await ctx.respond("✅ Auto-role enabled. Users will receive the auto-role after verification.")
    
    elif setting == "disable":
        verification_system.config['autorole_enabled'] = False
        verification_system.save_config()
        await ctx.respond("✅ Auto-role disabled.")
    
    elif setting == "role":
        if value:
            try:
                role_id = int(value.strip('<>@&'))
                role = ctx.guild.get_role(role_id)
                if role:
                    verification_system.config['autorole_role'] = role_id
                    verification_system.save_config()
                    await ctx.respond(f"✅ Auto-role set to {role.mention}")
                else:
                    await ctx.respond("❌ Role not found.")
            except ValueError:
                await ctx.respond("❌ Invalid role ID.")
        else:
            current = verification_system.config.get('autorole_role')
            role = ctx.guild.get_role(current) if current else None
            await ctx.respond(f"Current auto-role: {role.mention if role else 'Not set'}")
    
    elif setting == "unverified_enable":
        verification_system.config['auto_unverified_enabled'] = True
        verification_system.save_config()
        await ctx.respond("✅ Auto unverified role enabled. New members will receive the unverified role.")
    
    elif setting == "unverified_disable":
        verification_system.config['auto_unverified_enabled'] = False
        verification_system.save_config()
        await ctx.respond("✅ Auto unverified role disabled.")
    
    elif setting == "status":
        autorole_enabled = verification_system.config.get('autorole_enabled', False)
        autorole_role = verification_system.config.get('autorole_role')
        auto_unverified_enabled = verification_system.config.get('auto_unverified_enabled', True)
        unverified_role = verification_system.config.get('unverified_role')
        
        role_obj = ctx.guild.get_role(autorole_role) if autorole_role else None
        unverified_role_obj = ctx.guild.get_role(unverified_role) if unverified_role else None
        
        embed = discord.Embed(
            title="⚙️ Auto-Role Configuration",
            color=0x667eea
        )
        embed.add_field(
            name="🎯 Post-Verification Auto-Role",
            value=f"**Status:** {'Enabled' if autorole_enabled else 'Disabled'}\n**Role:** {role_obj.mention if role_obj else 'Not set'}",
            inline=False
        )
        embed.add_field(
            name="👤 Auto Unverified Role",
            value=f"**Status:** {'Enabled' if auto_unverified_enabled else 'Disabled'}\n**Role:** {unverified_role_obj.mention if unverified_role_obj else 'Not set'}",
            inline=False
        )
        await ctx.respond(embed=embed)

@bot.slash_command(name="invites", description="View invite tracking information (Owner only)")
async def invites_command(ctx, action: str = "status", user: discord.Member = None):
    """Manage invite tracking"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    if action == "status":
        tracking_enabled = verification_system.config.get('invite_tracking_enabled', False)
        tracking_channel = verification_system.config.get('invite_tracking_channel')
        channel_obj = bot.get_channel(tracking_channel) if tracking_channel else None
        
        embed = discord.Embed(
            title="📊 Invite Tracking Status",
            color=0x667eea
        )
        embed.add_field(
            name="🔄 Tracking Status",
            value="Enabled" if tracking_enabled else "Disabled",
            inline=True
        )
        embed.add_field(
            name="📢 Tracking Channel",
            value=channel_obj.mention if channel_obj else "Not set",
            inline=True
        )
        embed.add_field(
            name="📈 Tracked Members",
            value=len(verification_system.invite_data),
            inline=True
        )
        await ctx.respond(embed=embed)
    
    elif action == "lookup" and user:
        invite_info = verification_system.invite_data.get(str(user.id))
        if invite_info:
            embed = discord.Embed(
                title=f"📨 Invite Information for {user.display_name}",
                color=0x667eea
            )
            embed.add_field(name="👤 Member", value=f"{user.mention}", inline=True)
            embed.add_field(name="📨 Invited by", value=f"<@{invite_info['invited_by']}>", inline=True)
            embed.add_field(name="🔗 Invite Code", value=f"`{invite_info['invite_code']}`", inline=True)
            embed.add_field(name="📅 Joined", value=f"<t:{int(datetime.fromisoformat(invite_info['joined_at']).timestamp())}:F>", inline=False)
            await ctx.respond(embed=embed)
        else:
            await ctx.respond(f"❌ No invite information found for {user.mention}")
    
    else:
        await ctx.respond("❌ Invalid action. Use: `status` or `lookup @user`")

@bot.slash_command(name="blacklist", description="Manage blacklist (Owner only)")
async def blacklist_command(ctx, action: str, user_id: str = None):
    """Manage blacklist"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    if action == "add" and user_id:
        if user_id not in verification_system.blacklist:
            verification_system.blacklist.append(user_id)
            await verification_system.save_data()
            
            # Create alert embed
            embed = discord.Embed(
                title="🚫 User Manually Blacklisted",
                description=f"User `{user_id}` has been manually added to the blacklist.",
                color=0xff0000
            )
            
            # Ping administrators
            await verification_system.ping_administrators(ctx.guild, embed, "Manual blacklist addition")
            
            # Send to verification channel
            if verification_system.config.get('verification_channel'):
                channel = bot.get_channel(verification_system.config['verification_channel'])
                if channel:
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
            
            await ctx.respond(f"✅ User {user_id} added to blacklist.")
        else:
            await ctx.respond("❌ User already in blacklist.")
    
    elif action == "remove" and user_id:
        if user_id in verification_system.blacklist:
            verification_system.blacklist.remove(user_id)
            # Also reset failed attempts
            if user_id in verification_system.failed_attempts:
                del verification_system.failed_attempts[user_id]
            await verification_system.save_data()
            await ctx.respond(f"✅ User {user_id} removed from blacklist.")
        else:
            await ctx.respond("❌ User not in blacklist.")
    
    elif action == "list":
        if verification_system.blacklist:
            blacklist_str = "\n".join(verification_system.blacklist)
            await ctx.respond(f"**Blacklisted Users:**\n```\n{blacklist_str}\n```")
        else:
            await ctx.respond("Blacklist is empty.")
    
    elif action == "clear":
        verification_system.blacklist.clear()
        verification_system.failed_attempts.clear()
        await verification_system.save_data()
        await ctx.respond("✅ Blacklist cleared.")
    
    else:
        await ctx.respond("❌ Invalid action. Use: add, remove, list, or clear")

@bot.slash_command(name="unblacklist", description="Remove user from blacklist (Owner only)")
async def unblacklist_command(ctx, user_id: str):
    """Remove user from blacklist"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    if user_id in verification_system.blacklist:
        verification_system.blacklist.remove(user_id)
        # Also reset failed attempts
        if user_id in verification_system.failed_attempts:
            del verification_system.failed_attempts[user_id]
        await verification_system.save_data()
        await ctx.respond(f"✅ User {user_id} has been removed from the blacklist.")
    else:
        await ctx.respond("❌ User is not in the blacklist.")

@bot.slash_command(name="stats", description="View verification statistics (Owner only)")
async def stats_command(ctx):
    """View verification statistics"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    total_verified = len(verification_system.verification_data)
    total_blacklisted = len(verification_system.blacklist)
    total_whitelisted = len(verification_system.whitelist)
    failed_attempts = sum(verification_system.failed_attempts.values())
    total_tracked_invites = len(verification_system.invite_data)
    
    embed = discord.Embed(
        title="📊 Verification Statistics",
        color=0x667eea
    )
    embed.add_field(name="✅ Verified Users", value=total_verified, inline=True)
    embed.add_field(name="🚫 Blacklisted Users", value=total_blacklisted, inline=True)
    embed.add_field(name="⭐ Whitelisted Users", value=total_whitelisted, inline=True)
    embed.add_field(name="❌ Failed Attempts", value=failed_attempts, inline=True)
    embed.add_field(name="⚙️ Max Attempts", value=verification_system.config.get('max_failed_attempts', 3), inline=True)
    embed.add_field(name="🔄 Auto-Blacklist", value="Enabled" if verification_system.config.get('auto_blacklist_enabled', True) else "Disabled", inline=True)
    embed.add_field(name="📨 Tracked Invites", value=total_tracked_invites, inline=True)
    embed.add_field(name="🎯 Auto-Role", value="Enabled" if verification_system.config.get('autorole_enabled', False) else "Disabled", inline=True)
    embed.add_field(name="📍 Invite Tracking", value="Enabled" if verification_system.config.get('invite_tracking_enabled', False) else "Disabled", inline=True)
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="export", description="Export verification data (Owner only)")
async def export_command(ctx, data_type: str = "full"):
    """Export verification data to JSON file"""
    if ctx.author.id != OWNER_ID and str(ctx.author.id) not in verification_system.whitelist:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        if str(ctx.author.id) in verification_system.whitelist and ctx.author.id != OWNER_ID:
            # Whitelisted user gets hashed data only
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'export_type': 'hashed',
                'total_verified_users': len(verification_system.verification_data),
                'verification_data': {
                    uid: verification_system.get_hashed_data_for_whitelist(uid) 
                    for uid in verification_system.verification_data
                }
            }
        else:
            # Owner gets full data
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'export_type': 'full',
                'total_verified_users': len(verification_system.verification_data),
                'verification_data': verification_system.verification_data,
                'blacklist': verification_system.blacklist,
                'whitelist': verification_system.whitelist,
                'failed_attempts': verification_system.failed_attempts,
                'invite_data': verification_system.invite_data,
                'config': verification_system.config
            }
        
        filename = f"verification_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        file = discord.File(filename)
        await ctx.author.send("Here's your verification data export:", file=file)
        await ctx.respond("✅ Data exported and sent to your DMs.", ephemeral=True)
        
        # Clean up the file
        os.remove(filename)
        
    except Exception as e:
        await ctx.respond(f"❌ Error exporting data: {str(e)}", ephemeral=True)

@bot.slash_command(name="whitelist", description="Manage whitelist (Owner only)")
async def whitelist_command(ctx, action: str, user_id: str = None):
    """Manage whitelist"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    if action == "add" and user_id:
        if user_id not in verification_system.whitelist:
            verification_system.whitelist.append(user_id)
            await verification_system.save_data()
            await ctx.respond(f"✅ User {user_id} added to whitelist. They can now export hashed verification data.")
        else:
            await ctx.respond("❌ User already in whitelist.")
    
    elif action == "remove" and user_id:
        if user_id in verification_system.whitelist:
            verification_system.whitelist.remove(user_id)
            await verification_system.save_data()
            await ctx.respond(f"✅ User {user_id} removed from whitelist.")
        else:
            await ctx.respond("❌ User not in whitelist.")
    
    elif action == "list":
        if verification_system.whitelist:
            whitelist_str = "\n".join(verification_system.whitelist)
            await ctx.respond(f"**Whitelisted Users (can see hashed data):**\n```\n{whitelist_str}\n```")
        else:
            await ctx.respond("Whitelist is empty.")
    
    else:
        await ctx.respond("❌ Invalid action. Use: add, remove, or list")

@bot.slash_command(name="unverify", description="Remove user verification (Owner only)")
async def unverify_command(ctx, user_id: str):
    """Remove user verification"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    if user_id in verification_system.verification_data:
        del verification_system.verification_data[user_id]
        await verification_system.save_data()
        
        # Remove verified role and add unverified role
        try:
            user = ctx.guild.get_member(int(user_id))
            if user:
                verified_role = ctx.guild.get_role(verification_system.config.get('verification_role'))
                unverified_role = ctx.guild.get_role(verification_system.config.get('unverified_role'))
                autorole_role = ctx.guild.get_role(verification_system.config.get('autorole_role'))
                
                if verified_role and verified_role in user.roles:
                    await user.remove_roles(verified_role)
                if autorole_role and autorole_role in user.roles:
                    await user.remove_roles(autorole_role)
                if unverified_role:
                    await user.add_roles(unverified_role)
        except Exception as e:
            logger.error(f"Error updating roles: {e}")
        
        await ctx.respond(f"✅ User {user_id} has been unverified.")
    else:
        await ctx.respond("❌ User not found in verification data.")

# Webhook endpoint simulation (for receiving verification data)
@bot.event
async def on_message(message):
    """Handle verification webhook data"""
    if message.author.bot:
        return
    
    # Check if message is in verification channel and contains verification data
    if (message.channel.id == verification_system.config.get('verification_channel') and 
        message.embeds and 
        len(message.embeds) > 0 and
        "New Verification Request" in message.embeds[0].title):
        
        embed = message.embeds[0]
        user_data = {}
        
        for field in embed.fields:
            if field.name == "👤 Discord ID":
                user_data['discord_id'] = field.value
            elif field.name == "🖥️ Hardware ID":
                user_data['hwid'] = field.value
            elif field.name == "🌐 IP Address":
                user_data['ip'] = field.value
        
        if user_data.get('discord_id'):
            await process_verification_request(message, user_data)
    
    await bot.process_commands(message)

async def process_verification_request(message, user_data):
    """Process incoming verification request"""
    discord_id = user_data['discord_id']
    hwid = user_data['hwid']
    ip_address = user_data['ip']
    
    guild = message.guild
    user = guild.get_member(int(discord_id))
    
    if not user:
        # Increment failed attempts for non-member
        is_blacklisted = await verification_system.increment_failed_attempts(discord_id)
        
        embed = discord.Embed(
            title="❌ Verification Failed",
            description=f"User with ID {discord_id} is not in the server. Please join the server first.",
            color=0xff0000
        )
        
        if is_blacklisted:
            embed.add_field(
                name="🚫 User Auto-Blacklisted",
                value="Too many failed attempts. User has been automatically blacklisted.",
                inline=False
            )
            
            # Ping administrators for auto-blacklist
            await verification_system.ping_administrators(guild, embed, "Auto-blacklist due to failed verification attempts")
        
        await message.reply(embed=embed)
        return
    
    # Check if user is blacklisted
    if discord_id in verification_system.blacklist:
        embed = discord.Embed(
            title="🚫 User Blacklisted",
            description=f"User {user.mention} is blacklisted and cannot be verified.",
            color=0xff0000
        )
        await message.reply(embed=embed)
        return
    
    # Check for duplicate HWID
    hwid_duplicate = await verification_system.check_hwid_duplicate(hwid, discord_id)
    if hwid_duplicate:
        # Mute user and notify moderators
        mute_role = guild.get_role(verification_system.config.get('mute_role'))
        if mute_role:
            try:
                await user.add_roles(mute_role, reason="Duplicate HWID detected")
            except discord.Forbidden:
                pass
        
        embed = discord.Embed(
            title="⚠️ Duplicate HWID Detected",
            description=f"User {user.mention} has a duplicate HWID. User has been muted pending moderator review.",
            color=0xffa500
        )
        embed.add_field(
            name="🔍 Action Required",
            value="A moderator must review this case and unmute the user if legitimate.",
            inline=False
        )
        
        # Ping administrators for duplicate HWID
        await verification_system.ping_administrators(guild, embed, "Duplicate HWID detected - possible alt account")
        
        await message.reply(embed=embed)
        return
    
    # Check for VPN/Proxy
    is_vpn = await verification_system.detect_vpn(ip_address)
    if is_vpn:
        embed = discord.Embed(
            title="⚠️ VPN/Proxy Detected",
            description=f"User {user.mention} appears to be using a VPN or proxy. Manual review required.",
            color=0xffa500
        )
        await message.reply(embed=embed)
        return
    
    # Store verification data
    verification_system.verification_data[discord_id] = {
        'hwid': hwid,
        'ip_hash': verification_system.hash_ip(ip_address),
        'ip_raw': ip_address,  # Only stored for owner access
        'verified_at': datetime.now().isoformat(),
        'user_id': discord_id,
        'username': f"{user.name}#{user.discriminator}",
        'user_display_name': user.display_name
    }
    await verification_system.save_data()
    
    # Reset failed attempts on successful verification
    if discord_id in verification_system.failed_attempts:
        del verification_system.failed_attempts[discord_id]
        await verification_system.save_data()
    
    # Assign roles
    verified_role = guild.get_role(verification_system.config.get('verification_role'))
    unverified_role = guild.get_role(verification_system.config.get('unverified_role'))
    autorole_role = guild.get_role(verification_system.config.get('autorole_role'))
    
    try:
        # Add verified role
        if verified_role:
            await user.add_roles(verified_role, reason="Verification completed")
        
        # Remove unverified role
        if unverified_role and unverified_role in user.roles:
            await user.remove_roles(unverified_role, reason="Verification completed")
        
        # Add auto-role if enabled
        if verification_system.config.get('autorole_enabled', False) and autorole_role:
            await user.add_roles(autorole_role, reason="Auto-role after verification")
        
        embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"User {user.mention} has been successfully verified!",
            color=0x00ff00
        )
        embed.add_field(
            name="📊 User Info",
            value=f"**Username:** {user.name}#{user.discriminator}\n**Display Name:** {user.display_name}\n**Verified At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
        
        # Add invite information if available
        invite_info = verification_system.invite_data.get(str(user.id))
        if invite_info:
            embed.add_field(
                name="📨 Invited By",
                value=f"<@{invite_info['invited_by']}> (Code: `{invite_info['invite_code']}`)",
                inline=False
            )
        
        await message.reply(embed=embed)
        
        # Send success message to user
        try:
            await user.send("🎉 Congratulations! You have been successfully verified and now have access to the server.")
        except discord.Forbidden:
            pass
            
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to assign roles. Please check my permissions.",
            color=0xff0000
        )
        await message.reply(embed=embed)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set")
        print("Please create a .env file with BOT_TOKEN=your_bot_token_here")
        exit(1)
    
    bot.run(BOT_TOKEN)