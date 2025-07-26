# 📘 Complete Setup Guide

This guide will walk you through setting up the Discord Verification System from start to finish.

## 🚀 Quick Setup (5 minutes)

### Step 1: Clone or Download
```bash
git clone https://github.com/yourusername/discord-verification-system.git
cd discord-verification-system
```

### Step 2: Run Setup Script
```bash
python setup.py
```

### Step 3: Configure Bot Token
```bash
cd bot
nano .env  # or use your preferred editor
```
Add your Discord bot token:
```
BOT_TOKEN=your_actual_bot_token_here
```

### Step 4: Start the Bot
```bash
python enhanced_bot.py
```

### Step 5: Configure in Discord
Use these slash commands in your Discord server:
```
/config channel #verification-channel
/config website https://yourusername.github.io/repository-name
/config role @Verified
/config unverified @Unverified
```

## 🔧 Detailed Setup

### Prerequisites
- Python 3.8 or higher
- Discord Application/Bot Token
- GitHub account (for hosting the website)
- Discord server with administrator permissions

### 1. Discord Bot Creation

1. **Create Discord Application**:
   - Go to https://discord.com/developers/applications
   - Click "New Application"
   - Give it a name (e.g., "Verification Bot")

2. **Create Bot User**:
   - Go to the "Bot" section
   - Click "Add Bot"
   - Copy the bot token (keep this secret!)

3. **Configure Bot Settings**:
   - Enable "Server Members Intent"
   - Enable "Message Content Intent"
   - Disable "Public Bot" if you want it private

4. **Invite Bot to Server**:
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions:
     - Manage Roles
     - Send Messages
     - Use Slash Commands
     - Read Message History
     - Embed Links
     - Attach Files
   - Use the generated URL to invite the bot

### 2. Server Setup

1. **Create Roles**:
   - `@Verified` - For verified users
   - `@Unverified` - For unverified users  
   - `@Muted` - For users with duplicate HWIDs

2. **Create Channels**:
   - `#verification` - Where verification requests are processed
   - `#welcome` - Where users get verification instructions

3. **Set Role Hierarchy**:
   - Bot role must be above all roles it manages
   - Recommended order: Bot → Verified → Unverified → Muted

### 3. Website Setup (GitHub Pages)

1. **Fork Repository**:
   - Fork this repository to your GitHub account
   - Or create a new repository and upload the files

2. **Enable GitHub Pages**:
   - Go to repository Settings
   - Scroll to "Pages" section
   - Select source: "Deploy from a branch"
   - Select branch: "main" or "master"
   - Your site will be available at: `https://username.github.io/repo-name`

3. **Test Website**:
   - Visit your GitHub Pages URL
   - Verify the verification form loads correctly
   - Test with a sample Discord ID

### 4. Bot Configuration

#### Initial Configuration
```bash
# Set verification channel
/config channel #verification

# Set website URL
/config website https://yourusername.github.io/repo-name

# Set verified role
/config role @Verified

# Set unverified role
/config unverified @Unverified

# Set mute role (optional)
/config mute @Muted
```

#### Advanced Configuration
```bash
# Set max failed attempts before auto-blacklist
/config max_attempts 5

# Enable/disable auto-blacklist
/config auto_blacklist true
```

#### Verify Configuration
```bash
# Check current settings
/config channel
/config website
/config role
/config unverified
```

### 5. Testing the System

1. **Test Bot Commands**:
   ```bash
   /help                    # Show help
   /verification            # Get verification link
   /stats                   # Show statistics (owner only)
   ```

2. **Test Verification Flow**:
   - Use `/verification` command
   - Click the verification link
   - Enter a test Discord ID
   - Check if verification message appears in verification channel

3. **Test Role Assignment**:
   - Complete verification process
   - Check if verified role is assigned
   - Check if unverified role is removed

## 🔧 Advanced Configuration

### Webhook Integration

To connect the website directly to Discord:

1. **Create Webhook**:
   - Go to your verification channel settings
   - Create a webhook
   - Copy the webhook URL

2. **Configure Website**:
   - Edit `index.html`
   - Find the `getWebhookUrl()` function
   - Add your webhook URL

### Enhanced VPN Detection

For production use, consider integrating:

1. **IPQualityScore API**:
   ```bash
   # Add to bot/.env
   IPQUALITYSCORE_API_KEY=your_api_key
   ```

2. **MaxMind GeoIP2**:
   ```bash
   # Add to bot/.env
   MAXMIND_LICENSE_KEY=your_license_key
   ```

### Database Integration

For large servers, consider using a database:

1. **PostgreSQL Setup**:
   ```bash
   # Add to bot/.env
   DATABASE_URL=postgresql://user:password@localhost/verification
   ```

2. **Modify Bot Code**:
   - Replace JSON storage with database calls
   - Add database migration scripts

## 🚨 Troubleshooting

### Common Issues

**❌ Bot not responding to commands**
- Check bot token in `.env` file
- Verify bot has required permissions
- Make sure bot is online

**❌ Verification website not loading**
- Check GitHub Pages is enabled
- Verify repository is public
- Check for typos in website URL

**❌ Roles not being assigned**
- Check bot role hierarchy
- Verify bot has "Manage Roles" permission
- Ensure roles exist and are configured

**❌ Webhook not working**
- Verify webhook URL is correct
- Check Discord webhook permissions
- Test webhook manually

### Debug Mode

Enable debug logging:
```python
# Add to bot file
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Check log files for errors:
```bash
tail -f logs/bot.log
tail -f logs/verification.log
```

## 🔒 Security Best Practices

### Bot Security
- Never share your bot token
- Use environment variables for sensitive data
- Regularly rotate bot tokens
- Monitor bot permissions

### Data Protection
- Raw IP addresses only accessible to owner
- Regular backups of verification data
- Secure webhook URLs
- Comply with privacy laws (GDPR, etc.)

### Server Security
- Limit who can use bot commands
- Monitor verification patterns
- Regular review of blacklist/whitelist
- Keep bot and dependencies updated

## 📊 Monitoring and Maintenance

### Regular Tasks
- Export verification data monthly
- Review blacklist and remove false positives
- Update VPN detection rules
- Monitor server growth and adjust limits

### Analytics
Use `/stats` command to monitor:
- Total verified users
- Failed verification attempts
- Blacklist/whitelist sizes
- System health metrics

### Backup Strategy
```bash
# Regular backup script
/export  # Downloads verification data
# Store backups securely offsite
```

## 🆘 Getting Help

### Support Channels
- Create GitHub issue for bugs
- Check troubleshooting section
- Review Discord.py documentation
- Community Discord servers

### Contributing
- Fork the repository
- Create feature branches
- Submit pull requests
- Follow coding standards

### Updates
- Watch repository for updates
- Test updates in staging environment
- Backup data before major updates
- Read changelog for breaking changes

---

## 📋 Checklist

Before going live, ensure:

- [ ] Bot has all required permissions
- [ ] All roles are created and configured
- [ ] Verification channel is set up
- [ ] Website is accessible and working
- [ ] Test verification process works end-to-end
- [ ] Backup and recovery procedures tested
- [ ] Privacy policy and terms updated
- [ ] Staff trained on moderation commands

**Need more help?** Check the main README.md or create an issue on GitHub!