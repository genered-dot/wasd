# 📋 Changelog

## Latest Update - Enhanced Verification System

### 🎉 Major New Features

#### Administrator Alerts
- **Auto-ping administrators** when duplicate HWIDs (alt accounts) are detected
- **Auto-ping administrators** when users are automatically blacklisted
- **Manual blacklist alerts** ping administrators when someone is manually blacklisted
- Limits mentions to 10 administrators maximum to prevent spam

#### Invite Tracking System
- **Complete invite tracking** - tracks who invited whom using which invite code
- **Invite logs channel** - dedicated channel for join notifications with invite info
- **Invite lookup** - `/invites lookup @user` to see who invited a specific user
- **Invite statistics** - shows total tracked invites in stats
- **Automatic tracking** - works with all types of invites including vanity URLs

#### Auto-Role System
- **Post-verification auto-role** - assign additional roles after verification
- **Auto unverified role** - automatically assign unverified role to new members
- **Configurable auto-roles** - enable/disable and set custom roles
- **Role management** - automatically removes auto-roles when unverifying users

#### Enhanced Blacklist Management
- **Unblacklist command** - `/unblacklist` to remove users from blacklist
- **Failed attempts reset** - automatically reset when removing from blacklist
- **Administrator notifications** - alerts when blacklist actions occur

#### Improved Whitelist System
- **Clarified purpose** - whitelist is specifically for accessing hashed verification data
- **Hashed data export** - whitelisted users can export anonymized data
- **Clear access levels** - owner gets full data, whitelist gets hashed data only

### 🔧 Configuration Enhancements

#### New Commands
```bash
# Invite tracking configuration
/config invite_tracking true/false
/config invite_channel #invite-logs

# Auto-role configuration
/autorole enable/disable
/autorole role @RoleName
/autorole unverified_enable/disable
/autorole status

# Enhanced blacklist management
/unblacklist user_id

# Invite management
/invites status
/invites lookup @user
```

#### Updated Statistics
- Added invite tracking metrics
- Added auto-role status
- Added invite tracking status
- Enhanced overview of system features

### 🗂️ Data Management

#### New Data Files
- `invite_data.json` - stores who invited whom
- Enhanced `verification_data.json` with invite information
- Improved export includes invite data for owner

#### Privacy Protection
- **Invite data included** in verification success messages
- **Hashed IP protection** maintained for whitelisted users
- **Raw IP access** still restricted to owner only

### 🛡️ Security Improvements

#### Administrator Notifications
- Immediate alerts for suspicious activity
- Proper escalation for duplicate HWID detection
- Manual oversight notifications for blacklist actions

#### Enhanced Permissions
- Added `Manage Guild` permission for invite tracking
- Added `View Audit Log` as recommended permission
- Maintained strict owner-only access controls

### 🔄 System Improvements

#### Bot Intents
- Added `invites` intent for invite tracking functionality
- Maintained existing `members` and `message_content` intents

#### Error Handling
- Improved error handling for invite tracking
- Better permission error messages
- Enhanced logging for debugging

#### Performance
- Efficient invite tracking with minimal API calls
- Optimized administrator ping system
- Smart mention limiting to prevent spam

### 🧹 Code Cleanup

#### File Structure
- **Removed duplicate bot.py** - only enhanced_bot.py remains
- **Updated documentation** to reflect single bot file
- **Streamlined setup process** with automated script

#### Dependencies
- **Removed unnecessary hashlib2** dependency
- **Maintained core dependencies** for reliability
- **Added python-dotenv** for environment management

---

## How to Update

If you're upgrading from a previous version:

1. **Backup your data**:
   ```bash
   /export  # This will send your current data to DMs
   ```

2. **Update the bot file**:
   - Replace your old bot file with `enhanced_bot.py`
   - The old `bot.py` file is no longer needed

3. **Configure new features**:
   ```bash
   /config invite_tracking true
   /config invite_channel #invite-logs
   /autorole enable
   /autorole role @YourRole
   ```

4. **Test new functionality**:
   - Test invite tracking by having someone join
   - Test auto-role by completing verification
   - Check administrator pings work correctly

## Breaking Changes

- **None** - All existing functionality is preserved
- **Enhanced features** are additive and optional
- **Existing data** is fully compatible

## Support

For questions about the new features:
1. Check the updated README.md
2. Review SETUP_GUIDE.md for detailed instructions
3. Create an issue on GitHub if you need help

---

**Note**: This update maintains full backward compatibility while adding powerful new features for server administration and security.