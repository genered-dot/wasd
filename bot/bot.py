import discord
from discord.ext import commands
import json
import os
import hashlib
import asyncio
from datetime import datetime, timedelta
import aiofiles
import aiohttp
from typing import Dict, List, Optional

# Bot configuration
OWNER_ID = 945344266404782140
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATA_FILE = 'verification_data.json'
CONFIG_FILE = 'bot_config.json'

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

class VerificationBot:
    def __init__(self):
        self.verification_data: Dict = {}
        self.blacklist: List[str] = []
        self.whitelist: List[str] = []
        self.config: Dict = {
            'verification_channel': None,
            'verification_website': None,
            'verification_role': None,
            'unverified_role': None,
            'mute_role': None
        }
        self.load_data()
        self.load_config()

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
        except Exception as e:
            print(f"Error loading data: {e}")

    async def save_data(self):
        """Save verification data to file"""
        try:
            data = {
                'verification_data': self.verification_data,
                'blacklist': self.blacklist,
                'whitelist': self.whitelist
            }
            async with aiofiles.open(DATA_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_config(self):
        """Load bot configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        """Save bot configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

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
        """Basic VPN detection using IP analysis"""
        # This is a simplified VPN detection
        # In a real implementation, you'd use services like IPQualityScore or similar
        vpn_indicators = [
            'tor-exit', 'proxy', 'vpn', 'hosting', 'datacenter'
        ]
        # Placeholder for actual VPN detection logic
        return False

verification_system = VerificationBot()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await verification_system.load_data()
    
    # Auto-assign unverified role to all members without verified role
    for guild in bot.guilds:
        if verification_system.config.get('unverified_role'):
            unverified_role = guild.get_role(verification_system.config['unverified_role'])
            verified_role = guild.get_role(verification_system.config.get('verification_role'))
            
            if unverified_role:
                for member in guild.members:
                    if not member.bot and (not verified_role or verified_role not in member.roles):
                        try:
                            await member.add_roles(unverified_role, reason="Auto-assign unverified role")
                        except discord.Forbidden:
                            pass

@bot.event
async def on_member_join(member):
    """Auto-assign unverified role to new members"""
    if verification_system.config.get('unverified_role'):
        guild = member.guild
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
            value="`/config channel` - Set verification channel\n"
                  "`/config website` - Set verification website\n"
                  "`/config role` - Set verification role\n"
                  "`/config unverified` - Set unverified role\n"
                  "`/export` - Export verification data\n"
                  "`/whitelist` - Manage whitelist\n"
                  "`/unverify` - Remove user verification\n"
                  "`/blacklist` - Manage blacklist",
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
    
    elif setting == "role":
        if value:
            try:
                role_id = int(value.strip('<>@&'))
                role = ctx.guild.get_role(role_id)
                if role:
                    verification_system.config['verification_role'] = role_id
                    verification_system.save_config()
                    await ctx.respond(f"✅ Verification role set to {role.mention}")
                else:
                    await ctx.respond("❌ Role not found.")
            except ValueError:
                await ctx.respond("❌ Invalid role ID.")
        else:
            current = verification_system.config.get('verification_role')
            role = ctx.guild.get_role(current) if current else None
            await ctx.respond(f"Current verification role: {role.mention if role else 'Not set'}")
    
    elif setting == "unverified":
        if value:
            try:
                role_id = int(value.strip('<>@&'))
                role = ctx.guild.get_role(role_id)
                if role:
                    verification_system.config['unverified_role'] = role_id
                    verification_system.save_config()
                    await ctx.respond(f"✅ Unverified role set to {role.mention}")
                else:
                    await ctx.respond("❌ Role not found.")
            except ValueError:
                await ctx.respond("❌ Invalid role ID.")
        else:
            current = verification_system.config.get('unverified_role')
            role = ctx.guild.get_role(current) if current else None
            await ctx.respond(f"Current unverified role: {role.mention if role else 'Not set'}")
    
    else:
        await ctx.respond("❌ Invalid setting. Use: channel, website, role, or unverified")

@bot.slash_command(name="export", description="Export verification data (Owner only)")
async def export_command(ctx):
    """Export verification data to JSON file"""
    if ctx.author.id != OWNER_ID:
        await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_verified_users': len(verification_system.verification_data),
            'verification_data': verification_system.verification_data,
            'blacklist': verification_system.blacklist,
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
            await ctx.respond(f"✅ User {user_id} added to whitelist.")
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
            await ctx.respond(f"**Whitelisted Users:**\n```\n{whitelist_str}\n```")
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
                
                if verified_role and verified_role in user.roles:
                    await user.remove_roles(verified_role)
                if unverified_role:
                    await user.add_roles(unverified_role)
        except Exception as e:
            print(f"Error updating roles: {e}")
        
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
        embed = discord.Embed(
            title="❌ Verification Failed",
            description=f"User with ID {discord_id} is not in the server. Please join the server first.",
            color=0xff0000
        )
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
        'user_id': discord_id
    }
    await verification_system.save_data()
    
    # Assign verified role and remove unverified role
    verified_role = guild.get_role(verification_system.config.get('verification_role'))
    unverified_role = guild.get_role(verification_system.config.get('unverified_role'))
    
    try:
        if verified_role:
            await user.add_roles(verified_role, reason="Verification completed")
        if unverified_role and unverified_role in user.roles:
            await user.remove_roles(unverified_role, reason="Verification completed")
        
        embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"User {user.mention} has been successfully verified!",
            color=0x00ff00
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
        exit(1)
    
    bot.run(BOT_TOKEN)