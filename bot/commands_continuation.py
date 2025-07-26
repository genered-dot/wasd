# This file contains additional commands that would be added to the main bot file
# IP Banning and Moderation Commands

@bot.slash_command(name="ipban", description="Ban an IP address and all associated users (Admin only)")
@admin_only()
@handle_errors
async def ipban_command(ctx, ip: str, reason: str = "Manual IP ban"):
    """Ban an IP address"""
    if not verification_system.is_valid_ip(ip):
        await ctx.respond("❌ Invalid IP address format.", ephemeral=True)
        return
    
    # Get all users associated with this IP
    users = await verification_system.get_users_by_ip(ip)
    
    if not users:
        await ctx.respond("❌ No users found with this IP address.", ephemeral=True)
        return
    
    # Ban the IP
    success = await verification_system.ban_ip(ip, reason, str(ctx.author.id))
    if not success:
        await ctx.respond("❌ Failed to ban IP address.", ephemeral=True)
        return
    
    # Ban all associated users
    banned_users = []
    for user_id in users:
        try:
            user = ctx.guild.get_member(int(user_id))
            if user:
                await user.ban(reason=f"IP banned: {reason}")
                banned_users.append(f"{user} ({user_id})")
        except discord.Forbidden:
            pass
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
    
    # Create response embed
    embed = discord.Embed(
        title="🚫 IP Address Banned",
        color=0xff0000,
        timestamp=datetime.now()
    )
    embed.add_field(name="IP Address", value=f"`{ip}`", inline=True)
    embed.add_field(name="Reason", value=reason, inline=True)
    embed.add_field(name="Banned By", value=ctx.author.mention, inline=True)
    embed.add_field(name="Users Banned", value=f"{len(banned_users)} users", inline=True)
    
    if banned_users:
        user_list = "\n".join(banned_users[:10])  # Show max 10 users
        if len(banned_users) > 10:
            user_list += f"\n... and {len(banned_users) - 10} more"
        embed.add_field(name="Banned Users", value=user_list, inline=False)
    
    await ctx.respond(embed=embed)
    
    # Log the action
    await verification_system.log_action(
        ctx.guild,
        "IP Ban",
        {
            "IP": ip,
            "Reason": reason,
            "Banned By": f"{ctx.author} ({ctx.author.id})",
            "Users Affected": len(banned_users)
        },
        "WARNING"
    )
    
    # Ping administrators
    alert_embed = discord.Embed(
        title="🚨 IP Address Banned",
        description=f"IP `{ip}` has been banned by {ctx.author.mention}",
        color=0xff0000
    )
    await verification_system.ping_administrators(ctx.guild, alert_embed, f"IP ban by {ctx.author}", "admin")

@bot.slash_command(name="ipunban", description="Unban an IP address (Admin only)")
@admin_only()
@handle_errors
async def ipunban_command(ctx, ip: str):
    """Unban an IP address"""
    if not verification_system.is_valid_ip(ip):
        await ctx.respond("❌ Invalid IP address format.", ephemeral=True)
        return
    
    success = await verification_system.unban_ip(ip)
    if success:
        embed = discord.Embed(
            title="✅ IP Address Unbanned",
            description=f"IP `{ip}` has been unbanned by {ctx.author.mention}",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        await ctx.respond(embed=embed)
        
        # Log the action
        await verification_system.log_action(
            ctx.guild,
            "IP Unban",
            {
                "IP": ip,
                "Unbanned By": f"{ctx.author} ({ctx.author.id})"
            },
            "SUCCESS"
        )
    else:
        await ctx.respond("❌ IP address not found in ban list.", ephemeral=True)

@bot.slash_command(name="ipcheck", description="Check if an IP is banned and see associated users (Moderator only)")
@moderator_only()
@handle_errors
async def ipcheck_command(ctx, ip: str):
    """Check IP ban status and associated users"""
    if not verification_system.is_valid_ip(ip):
        await ctx.respond("❌ Invalid IP address format.", ephemeral=True)
        return
    
    is_banned = await verification_system.is_ip_banned(ip)
    users = await verification_system.get_users_by_ip(ip)
    
    embed = discord.Embed(
        title="🔍 IP Address Information",
        color=0xff0000 if is_banned else 0x00ff00,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="IP Address", value=f"`{ip}`", inline=True)
    embed.add_field(name="Status", value="🚫 Banned" if is_banned else "✅ Not Banned", inline=True)
    embed.add_field(name="Associated Users", value=len(users), inline=True)
    
    if is_banned and ip in verification_system.ip_bans:
        ban_info = verification_system.ip_bans[ip]
        embed.add_field(name="Banned At", value=ban_info.get('banned_at', 'Unknown'), inline=True)
        embed.add_field(name="Reason", value=ban_info.get('reason', 'No reason'), inline=True)
        embed.add_field(name="Banned By", value=ban_info.get('banned_by', 'Unknown'), inline=True)
    
    if users:
        user_list = []
        for user_id in users[:10]:  # Show max 10 users
            user = ctx.guild.get_member(int(user_id))
            if user:
                user_list.append(f"{user} ({user_id})")
            else:
                user_list.append(f"Unknown User ({user_id})")
        
        if len(users) > 10:
            user_list.append(f"... and {len(users) - 10} more")
        
        embed.add_field(name="Users", value="\n".join(user_list), inline=False)
    
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="userinfo", description="Get comprehensive user information (Moderator only)")
@moderator_only()
@handle_errors
async def userinfo_command(ctx, user: discord.Member):
    """Get detailed user information"""
    user_id = str(user.id)
    
    embed = discord.Embed(
        title=f"👤 User Information: {user}",
        color=0x667eea,
        timestamp=datetime.now()
    )
    
    # Basic info
    embed.add_field(name="User ID", value=f"`{user.id}`", inline=True)
    embed.add_field(name="Display Name", value=user.display_name, inline=True)
    embed.add_field(name="Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="Joined Server", value=f"<t:{int(user.joined_at.timestamp())}:R>", inline=True)
    
    # Verification status
    verification_data = verification_system.verification_data.get(user_id)
    if verification_data:
        embed.add_field(name="✅ Verification Status", value="Verified", inline=True)
        embed.add_field(name="Verified At", value=verification_data.get('verified_at', 'Unknown'), inline=True)
        embed.add_field(name="HWID", value=f"`{verification_data.get('hwid', 'Unknown')[:16]}...`", inline=True)
        embed.add_field(name="IP Hash", value=f"`{verification_data.get('ip_hash', 'Unknown')}`", inline=True)
    else:
        embed.add_field(name="❌ Verification Status", value="Not Verified", inline=True)
    
    # Invite information
    invite_info = verification_system.invite_data.get(user_id)
    if invite_info:
        inviter_id = invite_info.get('invited_by')
        if inviter_id != 'Unknown':
            inviter = ctx.guild.get_member(int(inviter_id))
            embed.add_field(
                name="📨 Invited By", 
                value=f"{inviter.mention if inviter else 'Unknown'} ({inviter_id})", 
                inline=True
            )
        embed.add_field(name="🔗 Invite Code", value=f"`{invite_info.get('invite_code', 'Unknown')}`", inline=True)
    
    # Security flags
    security_flags = []
    if user_id in verification_system.blacklist:
        security_flags.append("🚫 Blacklisted")
    if user_id in verification_system.whitelist:
        security_flags.append("⭐ Whitelisted")
    if user_id in verification_system.failed_attempts:
        attempts = verification_system.failed_attempts[user_id]
        security_flags.append(f"❌ Failed Attempts: {attempts}")
    
    if security_flags:
        embed.add_field(name="🛡️ Security Flags", value="\n".join(security_flags), inline=False)
    
    # User profile data
    user_profile = verification_system.user_profiles.get(user_id)
    if user_profile:
        embed.add_field(name="📊 Total Verifications", value=user_profile.get('total_verifications', 0), inline=True)
    
    # Roles
    roles = [role.mention for role in user.roles[1:]]  # Exclude @everyone
    if roles:
        embed.add_field(name="🎭 Roles", value=" ".join(roles[:10]), inline=False)
    
    embed.set_thumbnail(url=user.display_avatar.url)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="tutorial", description="Show comprehensive bot tutorials")
@handle_errors
async def tutorial_command(ctx, topic: str = "overview"):
    """Comprehensive tutorial system"""
    tutorials = {
        "overview": {
            "title": "🎓 Verification System Overview",
            "content": """
**Welcome to the Advanced Verification System!**

This bot provides comprehensive server security through:
• Hardware ID verification
• IP address analysis
• VPN/Proxy detection
• Invite tracking
• Automated moderation

**Key Features:**
• Anti-spoofing protection
• Duplicate account detection
• Automatic role management
• Administrator alerts
• Data privacy protection

**Getting Started:**
Use `/tutorial setup` to learn how to configure the bot.
Use `/tutorial commands` to see all available commands.
Use `/tutorial security` to understand security features.
            """,
            "fields": [
                ("📋 Available Topics", "`setup`, `commands`, `security`, `moderation`, `data`", True),
                ("🔗 Quick Links", "`/verification` - Get verification link\n`/help` - Command help", True)
            ]
        },
        
        "setup": {
            "title": "⚙️ Initial Setup Guide",
            "content": """
**Step-by-Step Setup:**

**1. Basic Configuration:**
```
/config channel #verification-channel
/config website https://your-github-pages-url
/config role @Verified
/config unverified @Unverified
```

**2. Security Settings:**
```
/config max_attempts 3
/config auto_blacklist true
```

**3. Invite Tracking (Optional):**
```
/config invite_tracking true
/config invite_channel #invite-logs
```

**4. Auto-Roles:**
```
/autorole enable
/autorole role @Member
```

**5. Test the System:**
• Use `/verification` to get the verification link
• Complete verification process
• Check roles are assigned correctly
            """,
            "fields": [
                ("🎯 Pro Tips", "• Set up roles before configuring\n• Test with an alt account\n• Configure logging channel", True),
                ("⚠️ Important", "• Bot needs Manage Roles permission\n• Role hierarchy matters\n• Backup your settings", True)
            ]
        },
        
        "commands": {
            "title": "📋 Command Reference",
            "content": """
**User Commands:**
• `/verification` - Get verification website link
• `/help` - Show command help
• `/tutorial <topic>` - Access tutorials

**Owner Commands:**
• `/config <setting> [value]` - Configure bot settings
• `/blacklist <action> [user]` - Manage blacklist
• `/whitelist <action> [user]` - Manage whitelist
• `/unverify <user>` - Remove verification
• `/export` - Export data to JSON
• `/stats` - View statistics

**Admin Commands:**
• `/ipban <ip> [reason]` - Ban IP address
• `/ipunban <ip>` - Unban IP address
• `/userinfo <user>` - Get user details

**Moderator Commands:**
• `/ipcheck <ip>` - Check IP status
• `/userinfo <user>` - View user info
            """,
            "fields": [
                ("🔒 Permission Levels", "Owner = Bot owner only\nAdmin = Server administrators\nMod = Kick/ban permissions", True),
                ("💡 Usage Tips", "• Commands are slash commands\n• Use autocomplete for options\n• Check permissions if commands fail", True)
            ]
        },
        
        "security": {
            "title": "🛡️ Security Features",
            "content": """
**Anti-Spoofing Protection:**
• Hardware ID fingerprinting
• IP address verification
• Browser fingerprint analysis
• Behavioral pattern detection

**VPN/Proxy Detection:**
• WebRTC analysis
• IP range checking
• Timezone verification
• Advanced fingerprinting

**Duplicate Account Prevention:**
• HWID duplicate detection
• Automatic muting
• Administrator alerts
• Manual review process

**Data Protection:**
• IP address hashing
• Encrypted storage
• Access level controls
• Regular backups

**Automated Responses:**
• Auto-blacklisting
• Administrator pinging
• Automatic bans
• Role management
            """,
            "fields": [
                ("🎯 Best Practices", "• Review alerts promptly\n• Configure mute role\n• Monitor statistics\n• Regular data exports", True),
                ("⚙️ Configuration", "• Enable VPN detection\n• Set appropriate thresholds\n• Configure alert channels", True)
            ]
        },
        
        "moderation": {
            "title": "👮 Moderation Guide",
            "content": """
**Handling Alerts:**

**Duplicate HWID Detection:**
1. User is automatically muted
2. Administrators are pinged
3. Review the case manually
4. Unmute if legitimate

**VPN/Proxy Detection:**
1. User verification blocked
2. Manual review required
3. Check if legitimate use
4. Whitelist if approved

**Auto-Blacklisting:**
1. After max failed attempts
2. Administrators notified
3. Use `/unblacklist` if needed
4. Check for false positives

**IP Banning:**
• Use `/ipban` for malicious IPs
• Bans all associated users
• Can be reversed with `/ipunban`
• Monitor with `/ipcheck`
            """,
            "fields": [
                ("⚡ Quick Actions", "`/unblacklist <user>` - Remove blacklist\n`/ipcheck <ip>` - Check IP status\n`/userinfo <user>` - Get details", True),
                ("📊 Monitoring", "• Check `/stats` regularly\n• Review log channel\n• Export data monthly", True)
            ]
        },
        
        "data": {
            "title": "📊 Data Management",
            "content": """
**Data Collection:**
• Discord User ID (required)
• Hardware ID (device fingerprint)
• IP address (raw + hashed)
• Browser information
• Optional: Geolocation, keystroke patterns

**Data Access Levels:**
• **Owner**: Full access to all data
• **Whitelisted**: Hashed data only
• **Regular Users**: No data access

**Data Export:**
• Use `/export` command
• JSON format download
• Automatic DM delivery
• Regular backups recommended

**Privacy Protection:**
• IP addresses are hashed for most users
• Raw IPs only accessible to owner
• Data retention settings available
• GDPR compliance features

**Data Linking:**
• All data linked to User IDs
• Cross-guild tracking possible
• Verification history maintained
• Invite relationships tracked
            """,
            "fields": [
                ("🔒 Privacy", "• Hashed IPs for whitelist\n• Configurable retention\n• Secure storage\n• Access controls", True),
                ("📋 Management", "• Regular exports\n• Monitor data size\n• Clean old records\n• Backup important data", True)
            ]
        }
    }
    
    if topic not in tutorials:
        available_topics = ", ".join(f"`{t}`" for t in tutorials.keys())
        await ctx.respond(f"❌ Invalid topic. Available topics: {available_topics}", ephemeral=True)
        return
    
    tutorial = tutorials[topic]
    embed = discord.Embed(
        title=tutorial["title"],
        description=tutorial["content"],
        color=0x667eea,
        timestamp=datetime.now()
    )
    
    for field_name, field_value, inline in tutorial["fields"]:
        embed.add_field(name=field_name, value=field_value, inline=inline)
    
    embed.set_footer(text="Use /tutorial <topic> to view other tutorials")
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="quickstart", description="Quick setup wizard for new installations")
@admin_only()
@handle_errors
async def quickstart_command(ctx):
    """Interactive setup wizard"""
    embed = discord.Embed(
        title="🚀 Quick Start Wizard",
        description="Let's set up your verification system step by step!",
        color=0x667eea
    )
    
    # Check current configuration
    missing_configs = []
    if not verification_system.config.get('verification_channel'):
        missing_configs.append("Verification Channel")
    if not verification_system.config.get('verification_website'):
        missing_configs.append("Verification Website")
    if not verification_system.config.get('verification_role'):
        missing_configs.append("Verification Role")
    if not verification_system.config.get('unverified_role'):
        missing_configs.append("Unverified Role")
    
    if not missing_configs:
        embed.add_field(
            name="✅ Configuration Complete",
            value="Your verification system is already configured! Use `/tutorial` for advanced features.",
            inline=False
        )
    else:
        embed.add_field(
            name="⚙️ Required Configuration",
            value=f"Missing: {', '.join(missing_configs)}",
            inline=False
        )
        
        setup_steps = [
            "1. Create roles: `@Verified`, `@Unverified`, `@Muted`",
            "2. Create channel: `#verification`",
            "3. Set up GitHub Pages with your verification website",
            "4. Run these commands:",
            "   `/config channel #verification`",
            "   `/config website https://yourusername.github.io/repo`",
            "   `/config role @Verified`",
            "   `/config unverified @Unverified`",
            "5. Test with `/verification`"
        ]
        
        embed.add_field(
            name="📋 Setup Steps",
            value="\n".join(setup_steps),
            inline=False
        )
    
    # Add helpful links
    embed.add_field(
        name="📚 Helpful Commands",
        value="`/tutorial setup` - Detailed setup guide\n`/tutorial commands` - Command reference\n`/help` - Quick command help",
        inline=False
    )
    
    await ctx.respond(embed=embed, ephemeral=True)

# Add these additional configuration commands
@bot.slash_command(name="advanced_config", description="Advanced configuration options (Owner only)")
@owner_only()
@handle_errors
async def advanced_config_command(ctx, setting: str, value: str = None):
    """Advanced configuration options"""
    advanced_settings = {
        "log_channel": "Set logging channel",
        "staff_role": "Set staff role for alerts", 
        "vpn_detection": "Enable/disable VPN detection",
        "auto_ban_vpn": "Auto-ban VPN users",
        "strict_mode": "Enable strict verification mode",
        "data_retention": "Data retention period (days)",
        "backup_enabled": "Enable automatic backups",
        "advanced_fingerprinting": "Enable advanced fingerprinting",
        "keystroke_analysis": "Enable keystroke analysis",
        "geolocation_tracking": "Enable geolocation tracking",
        "behavioral_analysis": "Enable behavioral analysis"
    }
    
    if setting not in advanced_settings:
        available = "\n".join([f"`{k}` - {v}" for k, v in advanced_settings.items()])
        await ctx.respond(f"❌ Invalid setting. Available options:\n{available}", ephemeral=True)
        return
    
    # Handle different setting types
    if setting in ["log_channel", "staff_role"]:
        if value:
            try:
                if setting == "log_channel":
                    channel_id = int(value.strip('<>#'))
                    channel = bot.get_channel(channel_id)
                    if channel:
                        verification_system.config['log_channel'] = channel_id
                        verification_system.save_config()
                        await ctx.respond(f"✅ Log channel set to {channel.mention}")
                    else:
                        await ctx.respond("❌ Channel not found.")
                elif setting == "staff_role":
                    role_id = int(value.strip('<>@&'))
                    role = ctx.guild.get_role(role_id)
                    if role:
                        verification_system.config['staff_role'] = role_id
                        verification_system.save_config()
                        await ctx.respond(f"✅ Staff role set to {role.mention}")
                    else:
                        await ctx.respond("❌ Role not found.")
            except ValueError:
                await ctx.respond("❌ Invalid ID format.")
        else:
            current_id = verification_system.config.get(setting)
            if setting == "log_channel":
                current = bot.get_channel(current_id) if current_id else None
                await ctx.respond(f"Current log channel: {current.mention if current else 'Not set'}")
            elif setting == "staff_role":
                current = ctx.guild.get_role(current_id) if current_id else None
                await ctx.respond(f"Current staff role: {current.mention if current else 'Not set'}")
    
    elif setting == "data_retention":
        if value:
            try:
                days = int(value)
                if days > 0:
                    verification_system.config['data_retention_days'] = days
                    verification_system.save_config()
                    await ctx.respond(f"✅ Data retention set to {days} days")
                else:
                    await ctx.respond("❌ Days must be greater than 0.")
            except ValueError:
                await ctx.respond("❌ Invalid number.")
        else:
            current = verification_system.config.get('data_retention_days', 90)
            await ctx.respond(f"Current data retention: {current} days")
    
    else:  # Boolean settings
        if value:
            if value.lower() in ['true', 'enable', 'on', '1']:
                verification_system.config[setting] = True
                verification_system.save_config()
                await ctx.respond(f"✅ {setting.replace('_', ' ').title()} enabled")
            elif value.lower() in ['false', 'disable', 'off', '0']:
                verification_system.config[setting] = False
                verification_system.save_config()
                await ctx.respond(f"✅ {setting.replace('_', ' ').title()} disabled")
            else:
                await ctx.respond("❌ Invalid value. Use: true/false, enable/disable, on/off, 1/0")
        else:
            current = verification_system.config.get(setting, False)
            await ctx.respond(f"{setting.replace('_', ' ').title()} is currently: {'Enabled' if current else 'Disabled'}")

# Additional utility commands would continue here...