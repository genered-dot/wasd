import discord
from discord.ext import commands, tasks
import json
import os
import hashlib
import asyncio
import ipaddress
from datetime import datetime, timedelta
import aiofiles
import aiohttp
from typing import Dict, List, Optional, Union
import logging
import traceback
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
OWNER_ID = 945344266404782140
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATA_FILE = 'verification_data.json'
CONFIG_FILE = 'bot_config.json'
INVITES_FILE = 'invite_data.json'
IP_BANS_FILE = 'ip_bans.json'
USER_PROFILES_FILE = 'user_profiles.json'

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.invites = True
intents.bans = True

# Bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

class AdvancedVerificationBot:
    def __init__(self):
        self.verification_data: Dict = {}
        self.blacklist: List[str] = []
        self.whitelist: List[str] = []
        self.failed_attempts: Dict[str, int] = {}
        self.invite_data: Dict = {}
        self.guild_invites: Dict = {}
        self.ip_bans: Dict = {}
        self.user_profiles: Dict = {}
        self.config: Dict = {
            # Basic settings
            'verification_channel': None,
            'verification_website': None,
            'verification_role': None,
            'unverified_role': None,
            'mute_role': None,
            'log_channel': None,
            'staff_role': None,
            
            # Security settings
            'max_failed_attempts': 3,
            'auto_blacklist_enabled': True,
            'vpn_detection_enabled': True,
            'auto_ban_vpn': False,
            'duplicate_hwid_action': 'mute',  # mute, ban, notify
            'strict_mode': False,
            
            # Invite tracking
            'invite_tracking_enabled': False,
            'invite_tracking_channel': None,
            'invite_logs_enabled': True,
            
            # Auto-role system
            'autorole_enabled': False,
            'autorole_role': None,
            'auto_unverified_enabled': True,
            'role_stacking_enabled': False,
            
            # Moderation settings
            'ban_threshold': 5,
            'mute_duration': 24,  # hours
            'auto_mod_enabled': True,
            'moderator_ping_enabled': True,
            'admin_ping_enabled': True,
            
            # Data retention
            'data_retention_days': 90,
            'auto_cleanup_enabled': True,
            'backup_enabled': True,
            
            # Advanced features
            'advanced_fingerprinting': False,
            'keystroke_analysis': False,
            'geolocation_tracking': False,
            'behavioral_analysis': True
        }
        self.load_data()
        self.load_config()
        self.load_invite_data()
        self.load_ip_bans()
        self.load_user_profiles()

    async def load_data(self):
        """Load verification data with error handling"""
        try:
            if os.path.exists(DATA_FILE):
                async with aiofiles.open(DATA_FILE, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    self.verification_data = data.get('verification_data', {})
                    self.blacklist = data.get('blacklist', [])
                    self.whitelist = data.get('whitelist', [])
                    self.failed_attempts = data.get('failed_attempts', {})
                    logger.info(f"Loaded {len(self.verification_data)} verification records")
        except Exception as e:
            logger.error(f"Error loading verification data: {e}")
            await self.create_backup_files()

    async def save_data(self):
        """Save verification data with error handling and backup"""
        try:
            # Create backup before saving
            if os.path.exists(DATA_FILE):
                backup_file = f"{DATA_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(DATA_FILE, backup_file)
            
            data = {
                'verification_data': self.verification_data,
                'blacklist': self.blacklist,
                'whitelist': self.whitelist,
                'failed_attempts': self.failed_attempts,
                'last_updated': datetime.now().isoformat(),
                'version': '2.0'
            }
            
            async with aiofiles.open(DATA_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving verification data: {e}")
            raise

    def load_config(self):
        """Load bot configuration with defaults"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    logger.info("Configuration loaded successfully")
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

    async def load_ip_bans(self):
        """Load IP ban data"""
        try:
            if os.path.exists(IP_BANS_FILE):
                async with aiofiles.open(IP_BANS_FILE, 'r') as f:
                    content = await f.read()
                    self.ip_bans = json.loads(content)
        except Exception as e:
            logger.error(f"Error loading IP ban data: {e}")

    async def save_ip_bans(self):
        """Save IP ban data"""
        try:
            async with aiofiles.open(IP_BANS_FILE, 'w') as f:
                await f.write(json.dumps(self.ip_bans, indent=2))
        except Exception as e:
            logger.error(f"Error saving IP ban data: {e}")

    async def load_user_profiles(self):
        """Load user profile data"""
        try:
            if os.path.exists(USER_PROFILES_FILE):
                async with aiofiles.open(USER_PROFILES_FILE, 'r') as f:
                    content = await f.read()
                    self.user_profiles = json.loads(content)
        except Exception as e:
            logger.error(f"Error loading user profiles: {e}")

    async def save_user_profiles(self):
        """Save user profile data"""
        try:
            async with aiofiles.open(USER_PROFILES_FILE, 'w') as f:
                await f.write(json.dumps(self.user_profiles, indent=2))
        except Exception as e:
            logger.error(f"Error saving user profiles: {e}")

    async def create_backup_files(self):
        """Create empty data files if they don't exist"""
        files_to_create = [
            (DATA_FILE, {'verification_data': {}, 'blacklist': [], 'whitelist': [], 'failed_attempts': {}}),
            (INVITES_FILE, {}),
            (IP_BANS_FILE, {}),
            (USER_PROFILES_FILE, {})
        ]
        
        for file_path, default_data in files_to_create:
            if not os.path.exists(file_path):
                try:
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.write(json.dumps(default_data, indent=2))
                    logger.info(f"Created {file_path}")
                except Exception as e:
                    logger.error(f"Error creating {file_path}: {e}")

    def hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    async def is_ip_banned(self, ip: str) -> bool:
        """Check if IP is banned"""
        return ip in self.ip_bans

    async def ban_ip(self, ip: str, reason: str = "Manual ban", banned_by: str = "System") -> bool:
        """Ban an IP address"""
        if not self.is_valid_ip(ip):
            return False
            
        self.ip_bans[ip] = {
            'banned_at': datetime.now().isoformat(),
            'reason': reason,
            'banned_by': banned_by,
            'active': True
        }
        await self.save_ip_bans()
        return True

    async def unban_ip(self, ip: str) -> bool:
        """Unban an IP address"""
        if ip in self.ip_bans:
            self.ip_bans[ip]['active'] = False
            self.ip_bans[ip]['unbanned_at'] = datetime.now().isoformat()
            await self.save_ip_bans()
            return True
        return False

    async def get_users_by_ip(self, ip: str) -> List[str]:
        """Get all user IDs associated with an IP"""
        users = []
        for user_id, data in self.verification_data.items():
            if data.get('ip_raw') == ip:
                users.append(user_id)
        return users

    async def create_user_profile(self, user_id: str, guild_id: str, data: Dict) -> None:
        """Create or update user profile with linked data"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'guilds': {},
                'verification_history': [],
                'security_flags': [],
                'total_verifications': 0
            }
        
        # Link guild-specific data
        self.user_profiles[user_id]['guilds'][guild_id] = {
            'joined_at': data.get('timestamp', datetime.now().isoformat()),
            'verification_data': data,
            'status': 'verified',
            'invite_info': self.invite_data.get(user_id, {}),
            'last_updated': datetime.now().isoformat()
        }
        
        # Add to verification history
        self.user_profiles[user_id]['verification_history'].append({
            'guild_id': guild_id,
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'hwid': data.get('hwid'),
            'ip_hash': data.get('ip_hash'),
            'success': True
        })
        
        self.user_profiles[user_id]['total_verifications'] += 1
        await self.save_user_profiles()

    async def check_hwid_duplicate(self, hwid: str, user_id: str) -> List[str]:
        """Check for HWID duplicates and return list of duplicate user IDs"""
        duplicates = []
        for uid, data in self.verification_data.items():
            if uid != user_id and data.get('hwid') == hwid:
                duplicates.append(uid)
        return duplicates

    async def detect_vpn(self, ip: str, additional_data: Dict = None) -> Dict:
        """Enhanced VPN detection with multiple methods"""
        try:
            detection_result = {
                'is_vpn': False,
                'confidence': 0.0,
                'reasons': [],
                'method': 'basic'
            }
            
            # Basic IP range checks
            try:
                ip_obj = ipaddress.ip_address(ip)
                
                # Check for private IP ranges (shouldn't be public)
                if ip_obj.is_private:
                    detection_result['is_vpn'] = True
                    detection_result['confidence'] = 0.9
                    detection_result['reasons'].append('Private IP range detected')
                
                # Check for known VPN/cloud provider ranges
                vpn_ranges = [
                    # Common VPN provider ranges would go here
                    # This is a simplified example
                ]
                
                # Additional checks based on browser data
                if additional_data:
                    if additional_data.get('webrtc_detected'):
                        detection_result['confidence'] += 0.3
                        detection_result['reasons'].append('WebRTC anomaly detected')
                    
                    if additional_data.get('timezone_mismatch'):
                        detection_result['confidence'] += 0.2
                        detection_result['reasons'].append('Timezone/IP location mismatch')
                
                detection_result['is_vpn'] = detection_result['confidence'] > 0.5
                
            except ValueError:
                detection_result['reasons'].append('Invalid IP format')
            
            return detection_result
            
        except Exception as e:
            logger.error(f"Error in VPN detection: {e}")
            return {'is_vpn': False, 'confidence': 0.0, 'reasons': ['Detection error'], 'method': 'error'}

    async def increment_failed_attempts(self, user_id: str) -> bool:
        """Increment failed attempts and check for auto-blacklist"""
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
            del data['ip_raw']
        
        return data

    async def ping_administrators(self, guild: discord.Guild, embed: discord.Embed, reason: str, ping_type: str = "admin"):
        """Enhanced administrator pinging system"""
        try:
            mentions = []
            
            # Get administrators
            if ping_type == "admin" and self.config.get('admin_ping_enabled', True):
                for member in guild.members:
                    if member.guild_permissions.administrator and not member.bot:
                        mentions.append(member.mention)
            
            # Get staff role members
            elif ping_type == "staff" and self.config.get('staff_role'):
                staff_role = guild.get_role(self.config['staff_role'])
                if staff_role:
                    mentions = [member.mention for member in staff_role.members if not member.bot]
            
            # Get moderators
            elif ping_type == "mod" and self.config.get('moderator_ping_enabled', True):
                for member in guild.members:
                    if (member.guild_permissions.kick_members or 
                        member.guild_permissions.ban_members) and not member.bot:
                        mentions.append(member.mention)
            
            if mentions and len(mentions) <= 15:  # Limit mentions
                mention_text = " ".join(mentions[:10])  # Max 10 mentions
                embed.add_field(
                    name=f"🚨 {ping_type.title()} Alert",
                    value=f"{mention_text}\n**Reason:** {reason}",
                    inline=False
                )
                
                # Add timestamp
                embed.add_field(
                    name="⏰ Alert Time",
                    value=f"<t:{int(datetime.now().timestamp())}:F>",
                    inline=True
                )
                
        except Exception as e:
            logger.error(f"Error pinging administrators: {e}")

    async def track_invite_usage(self, member: discord.Member):
        """Enhanced invite tracking"""
        if not self.config.get('invite_tracking_enabled', False):
            return None
            
        guild = member.guild
        try:
            current_invites = {invite.code: invite.uses for invite in await guild.invites()}
            used_invite = None
            inviter = None
            
            if guild.id in self.guild_invites:
                old_invites = self.guild_invites[guild.id]
                for code, uses in current_invites.items():
                    if code in old_invites and uses > old_invites[code]:
                        used_invite = code
                        break
            
            # Update stored invites
            self.guild_invites[guild.id] = current_invites
            
            if used_invite:
                for invite in await guild.invites():
                    if invite.code == used_invite:
                        inviter = invite.inviter
                        self.invite_data[str(member.id)] = {
                            'invited_by': str(inviter.id) if inviter else 'Unknown',
                            'invite_code': used_invite,
                            'joined_at': datetime.now().isoformat(),
                            'inviter_name': f"{inviter.name}#{inviter.discriminator}" if inviter else 'Unknown',
                            'guild_id': str(guild.id),
                            'uses_at_join': current_invites[used_invite]
                        }
                        await self.save_invite_data()
                        break
                        
            return inviter
                        
        except Exception as e:
            logger.error(f"Error tracking invite usage: {e}")
            return None

    async def log_action(self, guild: discord.Guild, action: str, details: Dict, level: str = "INFO"):
        """Comprehensive action logging"""
        try:
            log_channel_id = self.config.get('log_channel')
            if not log_channel_id:
                return
                
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return
                
            # Create log embed
            color_map = {
                "INFO": 0x3498db,
                "WARNING": 0xf39c12,
                "ERROR": 0xe74c3c,
                "SUCCESS": 0x2ecc71
            }
            
            embed = discord.Embed(
                title=f"📋 {action}",
                color=color_map.get(level, 0x3498db),
                timestamp=datetime.now()
            )
            
            for key, value in details.items():
                embed.add_field(
                    name=key.replace('_', ' ').title(),
                    value=str(value)[:1024],  # Discord field limit
                    inline=True
                )
            
            embed.set_footer(text=f"Level: {level}")
            await log_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")

verification_system = AdvancedVerificationBot()

# Error handling decorator
def handle_errors(func):
    """Decorator for comprehensive error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except discord.Forbidden:
            if len(args) > 0 and hasattr(args[0], 'respond'):
                await args[0].respond("❌ I don't have permission to perform this action.", ephemeral=True)
        except discord.HTTPException as e:
            logger.error(f"Discord HTTP error in {func.__name__}: {e}")
            if len(args) > 0 and hasattr(args[0], 'respond'):
                await args[0].respond("❌ A Discord API error occurred. Please try again.", ephemeral=True)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}\n{traceback.format_exc()}")
            if len(args) > 0 and hasattr(args[0], 'respond'):
                await args[0].respond("❌ An unexpected error occurred. Please contact an administrator.", ephemeral=True)
    return wrapper

# Permission checking decorators
def owner_only():
    """Decorator to restrict commands to bot owner only"""
    def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

def admin_only():
    """Decorator to restrict commands to administrators only"""
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == OWNER_ID
    return commands.check(predicate)

def moderator_only():
    """Decorator to restrict commands to moderators only"""
    def predicate(ctx):
        return (ctx.author.guild_permissions.kick_members or 
                ctx.author.guild_permissions.ban_members or 
                ctx.author.guild_permissions.administrator or 
                ctx.author.id == OWNER_ID)
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await verification_system.load_data()
    
    # Start background tasks
    cleanup_task.start()
    backup_task.start()
    
    # Initialize invite tracking for all guilds
    for guild in bot.guilds:
        if verification_system.config.get('invite_tracking_enabled', False):
            try:
                invites = await guild.invites()
                verification_system.guild_invites[guild.id] = {invite.code: invite.uses for invite in invites}
                logger.info(f"Initialized invite tracking for {guild.name}")
            except Exception as e:
                logger.error(f"Error initializing invites for {guild.name}: {e}")
    
    # Auto-assign unverified role to all members without verified role
    for guild in bot.guilds:
        if (verification_system.config.get('auto_unverified_enabled', True) and 
            verification_system.config.get('unverified_role')):
            
            unverified_role = guild.get_role(verification_system.config['unverified_role'])
            verified_role = guild.get_role(verification_system.config.get('verification_role'))
            
            if unverified_role:
                count = 0
                for member in guild.members:
                    if not member.bot and (not verified_role or verified_role not in member.roles):
                        try:
                            await member.add_roles(unverified_role, reason="Auto-assign unverified role")
                            count += 1
                        except discord.Forbidden:
                            pass
                logger.info(f"Auto-assigned unverified role to {count} members in {guild.name}")

@tasks.loop(hours=24)
async def cleanup_task():
    """Daily cleanup task"""
    try:
        if not verification_system.config.get('auto_cleanup_enabled', True):
            return
            
        retention_days = verification_system.config.get('data_retention_days', 90)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Clean old failed attempts
        old_attempts = []
        for user_id, timestamp in verification_system.failed_attempts.items():
            if isinstance(timestamp, str):
                try:
                    attempt_date = datetime.fromisoformat(timestamp)
                    if attempt_date < cutoff_date:
                        old_attempts.append(user_id)
                except ValueError:
                    pass
        
        for user_id in old_attempts:
            del verification_system.failed_attempts[user_id]
        
        if old_attempts:
            await verification_system.save_data()
            logger.info(f"Cleaned up {len(old_attempts)} old failed attempts")
            
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")

@tasks.loop(hours=6)
async def backup_task():
    """Regular backup task"""
    try:
        if not verification_system.config.get('backup_enabled', True):
            return
            
        # Create timestamped backups
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_files = [
            (DATA_FILE, f"{DATA_FILE}.backup.{timestamp}"),
            (CONFIG_FILE, f"{CONFIG_FILE}.backup.{timestamp}"),
            (INVITES_FILE, f"{INVITES_FILE}.backup.{timestamp}"),
            (IP_BANS_FILE, f"{IP_BANS_FILE}.backup.{timestamp}"),
            (USER_PROFILES_FILE, f"{USER_PROFILES_FILE}.backup.{timestamp}")
        ]
        
        for original, backup in backup_files:
            if os.path.exists(original):
                try:
                    import shutil
                    shutil.copy2(original, backup)
                except Exception as e:
                    logger.error(f"Error backing up {original}: {e}")
        
        logger.info("Backup completed successfully")
        
    except Exception as e:
        logger.error(f"Error in backup task: {e}")

@bot.event
async def on_member_join(member):
    """Enhanced member join handling"""
    try:
        guild = member.guild
        
        # Check if IP is banned (if we have previous data)
        user_profile = verification_system.user_profiles.get(str(member.id))
        if user_profile:
            for guild_data in user_profile.get('guilds', {}).values():
                ip = guild_data.get('verification_data', {}).get('ip_raw')
                if ip and await verification_system.is_ip_banned(ip):
                    try:
                        await member.ban(reason="IP banned - automatic enforcement")
                        await verification_system.log_action(
                            guild, 
                            "Auto-Ban (IP Banned)", 
                            {"User": f"{member} ({member.id})", "IP": ip}, 
                            "WARNING"
                        )
                        return
                    except discord.Forbidden:
                        pass
        
        # Track invite usage
        inviter = await verification_system.track_invite_usage(member)
        
        # Send invite tracking message
        if (verification_system.config.get('invite_tracking_enabled', False) and 
            verification_system.config.get('invite_tracking_channel')):
            
            channel = bot.get_channel(verification_system.config['invite_tracking_channel'])
            if channel:
                embed = discord.Embed(
                    title="👋 New Member Joined",
                    description=f"{member.mention} has joined the server",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="👤 Member", value=f"{member}\n`{member.id}`", inline=True)
                embed.add_field(name="📅 Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
                
                if inviter:
                    embed.add_field(name="📨 Invited by", value=f"{inviter.mention}\n`{inviter.id}`", inline=True)
                    invite_info = verification_system.invite_data.get(str(member.id), {})
                    embed.add_field(name="🔗 Invite Code", value=f"`{invite_info.get('invite_code', 'Unknown')}`", inline=True)
                else:
                    embed.add_field(name="📨 Invited by", value="Unknown/Vanity URL", inline=True)
                    embed.add_field(name="🔗 Invite Code", value="Unknown", inline=True)
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{len(guild.members)}")
                
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass
        
        # Auto-assign unverified role
        if (verification_system.config.get('auto_unverified_enabled', True) and 
            verification_system.config.get('unverified_role')):
            
            unverified_role = guild.get_role(verification_system.config['unverified_role'])
            if unverified_role:
                try:
                    await member.add_roles(unverified_role, reason="Auto-assign unverified role")
                except discord.Forbidden:
                    pass
        
        # Log the join
        await verification_system.log_action(
            guild,
            "Member Joined",
            {
                "Member": f"{member} ({member.id})",
                "Invited By": f"{inviter} ({inviter.id})" if inviter else "Unknown",
                "Account Age": f"<t:{int(member.created_at.timestamp())}:R>"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in on_member_join: {e}")

@bot.event
async def on_member_remove(member):
    """Handle member leave events"""
    try:
        guild = member.guild
        
        # Log the leave
        await verification_system.log_action(
            guild,
            "Member Left",
            {
                "Member": f"{member} ({member.id})",
                "Roles": ", ".join([role.name for role in member.roles[1:]]) if len(member.roles) > 1 else "None"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in on_member_remove: {e}")

@bot.slash_command(name="verification", description="Get the verification website link")
@handle_errors
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
@handle_errors
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
@owner_only()
@handle_errors
async def config_command(ctx, setting: str, value: str = None):
    """Configuration command for bot owner"""
    
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
@owner_only()
@handle_errors
async def autorole_command(ctx, setting: str, value: str = None):
    """Configure automatic role assignment"""
    
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
@owner_only()
@handle_errors
async def invites_command(ctx, action: str = "status", user: discord.Member = None):
    """Manage invite tracking"""
    
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
@owner_only()
@handle_errors
async def blacklist_command(ctx, action: str, user_id: str = None):
    """Manage blacklist"""
    
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
            await verification_system.ping_administrators(ctx.guild, embed, "Manual blacklist addition", "admin")
            
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
@owner_only()
@handle_errors
async def unblacklist_command(ctx, user_id: str):
    """Remove user from blacklist"""
    
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
@owner_only()
@handle_errors
async def stats_command(ctx):
    """View verification statistics"""
    
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
@owner_only()
@handle_errors
async def export_command(ctx, data_type: str = "full"):
    """Export verification data to JSON file"""
    
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
@owner_only()
@handle_errors
async def whitelist_command(ctx, action: str, user_id: str = None):
    """Manage whitelist"""
    
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
@owner_only()
@handle_errors
async def unverify_command(ctx, user_id: str):
    """Remove user verification"""
    
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
            await verification_system.ping_administrators(guild, embed, "Auto-blacklist due to failed verification attempts", "admin")
        
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
        await verification_system.ping_administrators(guild, embed, "Duplicate HWID detected - possible alt account", "mod")
        
        await message.reply(embed=embed)
        return
    
    # Check for VPN/Proxy
    is_vpn = await verification_system.detect_vpn(ip_address)
    if is_vpn['is_vpn']:
        # Auto-blacklist and mute if VPN detected
        verification_system.blacklist.append(discord_id)
        
        # Mute the user
        mute_role = guild.get_role(verification_system.config.get('mute_role'))
        if mute_role:
            try:
                await user.add_roles(mute_role, reason="VPN/Proxy detected - automatic mute")
            except discord.Forbidden:
                pass
        
        embed = discord.Embed(
            title="⚠️ VPN/Proxy Detected",
            description=f"User {user.mention} has been blacklisted and muted due to VPN/Proxy detection.",
            color=0xffa500
        )
        embed.add_field(
            name="🔍 Detection Details",
            value=f"**Confidence:** {is_vpn['confidence']:.1%}\n**Reasons:** {', '.join(is_vpn['reasons'])}",
            inline=False
        )
        embed.add_field(
            name="🛡️ Action Taken",
            value="User has been automatically blacklisted and muted until administrator review.",
            inline=False
        )
        
        # Ping administrators for VPN detection
        await verification_system.ping_administrators(guild, embed, "VPN/Proxy detected - user blacklisted", "admin")
        
        await message.reply(embed=embed)
        await verification_system.save_data()
        return
    
    # Store verification data
    verification_data = {
        'hwid': hwid,
        'ip_hash': verification_system.hash_ip(ip_address),
        'ip_raw': ip_address,  # Only stored for owner access
        'verified_at': datetime.now().isoformat(),
        'user_id': discord_id,
        'username': f"{user.name}#{user.discriminator}",
        'user_display_name': user.display_name,
        'guild_id': str(guild.id),
        'guild_name': guild.name
    }
    
    verification_system.verification_data[discord_id] = verification_data
    
    # Create user profile with linked data
    await verification_system.create_user_profile(discord_id, str(guild.id), verification_data)
    
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
    
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)