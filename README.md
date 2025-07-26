# 🔐 Discord Server Verification System

A comprehensive Discord verification system that combines a static GitHub Pages website with a powerful Discord bot to prevent spoofing, detect VPNs, and manage user verification through hardware ID (HWID) and IP address analysis.

## 🌟 Features

### Static Website (`index.html`)
- **Modern UI**: Beautiful, responsive design with glassmorphism effects
- **HWID Generation**: Advanced hardware fingerprinting using canvas, screen, and browser data
- **IP Detection**: Automatic IP address retrieval for location analysis
- **VPN/Proxy Detection**: WebRTC-based detection for common VPN services
- **Data Collection**: Secure collection of Discord ID, HWID, IP, and browser fingerprint
- **Security**: Client-side data validation and encryption

### Discord Bot Features
- **Modern Slash Commands**: Full slash command implementation
- **Automatic Role Management**: Auto-assign verified/unverified/custom roles
- **HWID Duplicate Detection**: Prevents multiple accounts per device with admin alerts
- **VPN/Proxy Detection**: Advanced IP analysis and blocking
- **Blacklist System**: Automatic blacklisting after failed attempts with admin pings
- **Whitelist System**: Special access for trusted users (hashed data only)
- **Invite Tracking**: Track who invited whom with detailed logging
- **Administrator Alerts**: Automatic pinging when alts/blacklists are detected
- **Auto-Role System**: Configurable roles assigned after verification
- **Data Export**: JSON export for owner and whitelisted users
- **Permission Checks**: Comprehensive permission validation
- **Owner-Only Commands**: Secure administrative controls

## 🚀 Quick Start

### 1. Website Setup
1. Fork this repository
2. Enable GitHub Pages in repository settings
3. Your verification website will be available at: `https://yourusername.github.io/repository-name`

### 2. Discord Bot Setup

#### Prerequisites
- Python 3.8+
- Discord Application with Bot Token
- Server with appropriate permissions

#### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/repository-name.git
cd repository-name/bot

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your bot token
```

#### Environment Setup
Create a `.env` file in the `bot/` directory:
```env
BOT_TOKEN=your_discord_bot_token_here
```

#### Running the Bot
```bash
# Run the enhanced bot
python enhanced_bot.py
```

## 📋 Commands

### User Commands
- `/verification` - Get the verification website link
- `/help` - Show help information

### Owner Commands (ID: 945344266404782140)
- `/config <setting> [value]` - Configure bot settings
- `/blacklist <action> [user_id]` - Manage blacklist
- `/unblacklist <user_id>` - Remove user from blacklist
- `/whitelist <action> [user_id]` - Manage whitelist (hashed data access)
- `/autorole <setting> [value]` - Configure automatic role assignment
- `/invites <action> [user]` - Manage invite tracking
- `/unverify <user_id>` - Remove user verification
- `/export [type]` - Export verification data
- `/stats` - View verification statistics

## ⚙️ Configuration

### Bot Configuration Options
```bash
# Set verification channel
/config channel #verification-channel

# Set verification website
/config website https://yourusername.github.io/repository-name

# Set verification role
/config role @Verified

# Set unverified role
/config unverified @Unverified

# Set mute role (for duplicate HWID users)
/config mute @Muted

# Set max failed attempts before auto-blacklist
/config max_attempts 3

# Enable/disable auto-blacklist
/config auto_blacklist true

# Configure invite tracking
/config invite_tracking true
/config invite_channel #invite-logs

# Configure auto-roles
/autorole enable
/autorole role @Member
/autorole unverified_enable
```

### Required Bot Permissions
- Manage Roles
- Send Messages
- Use Slash Commands
- Read Message History
- Embed Links
- Attach Files
- Manage Guild (for invite tracking)
- View Audit Log (recommended)

## 🔒 Security Features

### Anti-Spoofing Measures
1. **Hardware ID Generation**: Unique device fingerprinting
2. **IP Address Tracking**: Location-based verification
3. **Browser Fingerprinting**: Additional device identification
4. **Duplicate Detection**: Prevents multiple accounts per device
5. **VPN/Proxy Detection**: Blocks suspicious connections

### Data Protection
- **IP Hashing**: Raw IPs only accessible to owner
- **Whitelisted Access**: Limited data access for trusted users
- **Secure Storage**: Encrypted data files
- **Automatic Cleanup**: Failed attempts reset system

### Blacklist System
- **Auto-Blacklist**: Automatic blocking after failed attempts
- **Manual Management**: Owner can add/remove users
- **Failed Attempt Tracking**: Monitors verification failures
- **Whitelist Override**: Trusted users bypass restrictions

## 📊 Data Management

### Data Collection
The system collects:
- Discord User ID
- Hardware ID (HWID)
- IP Address (raw + hashed)
- Browser Fingerprint
- Verification Timestamp
- User Information
- Invite Information (who invited whom)
- Failed Attempt Tracking

### Data Access Levels
1. **Owner**: Full access to all data including raw IPs
2. **Whitelisted**: Access to hashed data only
3. **Regular Users**: No data access

### Export Options
- **Full Export**: Complete data dump (owner only)
- **Hashed Export**: Privacy-protected data (whitelisted users)
- **Statistics**: Verification metrics and analytics

## 🛠️ Customization

### Website Customization
Edit `index.html` to customize:
- Colors and styling
- Information collected
- Validation rules
- VPN detection methods
- Webhook URLs

### Bot Customization
Modify bot files to add:
- Additional commands
- Custom verification logic
- Enhanced VPN detection
- Integration with external APIs
- Advanced analytics

## 📁 File Structure
```
├── index.html              # Static verification website
├── bot/
│   ├── enhanced_bot.py     # Enhanced Discord bot with all features
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   ├── verification_data.json  # User verification data (auto-created)
│   ├── bot_config.json     # Bot configuration (auto-created)
│   └── invite_data.json    # Invite tracking data (auto-created)
├── setup.py                # Automated setup script
├── README.md               # This file
├── SETUP_GUIDE.md         # Detailed setup instructions
└── .gitignore             # Git ignore file
```

## 🔧 Troubleshooting

### Common Issues

**Bot Not Responding**
- Check bot token in `.env` file
- Verify bot has required permissions
- Ensure bot is online and invited to server

**Verification Not Working**
- Configure verification channel: `/config channel #channel`
- Set verification website: `/config website https://your-site.com`
- Check webhook configuration in website

**Role Assignment Issues**
- Verify bot has Manage Roles permission
- Check role hierarchy (bot role must be above target roles)
- Configure roles: `/config role @RoleName`

**Data Export Problems**
- Only owner (945344266404782140) can export full data
- Whitelisted users get hashed data only
- Check DM permissions for file delivery

### Error Messages
- `❌ Permission Error`: Bot lacks required permissions
- `🚫 User Blacklisted`: User is on blacklist
- `⚠️ Duplicate HWID`: Multiple accounts detected
- `❌ Verification Not Configured`: Missing bot configuration

## 🔐 Security Considerations

### Best Practices
1. **Keep Bot Token Secret**: Never share or commit bot tokens
2. **Regular Backups**: Export verification data regularly
3. **Monitor Logs**: Check for suspicious activities
4. **Update Dependencies**: Keep libraries up to date
5. **Limit Permissions**: Give bot only necessary permissions

### Privacy Compliance
- Raw IP addresses only accessible to owner
- Data export includes privacy controls
- User consent through verification process
- Secure data storage and transmission

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Contact the project maintainer
- Check the troubleshooting section

## 🔄 Updates

The system is designed to be:
- **Scalable**: Handle large Discord servers
- **Maintainable**: Clean, documented code
- **Extensible**: Easy to add new features
- **Secure**: Multiple layers of protection

---

**Note**: This system is designed for legitimate server verification purposes. Use responsibly and in compliance with Discord's Terms of Service and applicable privacy laws.
