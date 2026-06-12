# Admin Access Management - User Guide

## Overview

This guide explains how to securely manage admin privileges for your Cybertec8 CTF platform.

## Security Note

⚠️ **The `/make-admin` route has been disabled** as it was a security vulnerability that allowed any logged-in user to grant themselves admin privileges. All admin management must now be done through the secure `promote_admin.py` script.

---

## Using the Admin Management Script

### List All Current Admins

```bash
python promote_admin.py list
```

**Output:**
```
📋 Admin Users (2 total):
------------------------------------------------------------
  • admin_user
    Email: admin@example.com
    User ID: 1
    XP: 5000

  • moderator
    Email: mod@example.com
    User ID: 5
    XP: 3200
```

### Promote a User to Admin

```bash
python promote_admin.py promote user@example.com
```

You'll be prompted to confirm:
```
⚠️  You are about to promote user 'username' (user@example.com) to Admin.
Admin users have full access to:
  - Event management
  - Challenge creation
  - Team management
  - Blog management
  - User data

Are you sure? (yes/no):
```

Type `yes` to confirm. The user **must log out and log back in** for changes to take effect.

**Skip confirmation** (use with caution):
```bash
python promote_admin.py promote user@example.com --force
```

### Revoke Admin Privileges

```bash
python promote_admin.py revoke user@example.com
```

Confirmation prompt will appear. Use `--force` to skip.

### Check Admin Status

```bash
python promote_admin.py check user@example.com
```

**Output:**
```
User: username
Email: user@example.com
Status: ✅ Admin
```

### List All Users

```bash
python promote_admin.py users
```

Shows all users with admin status indicated:
```
All Users (10 total):
  • admin_user - admin@example.com [ADMIN]
  • player1 - player1@example.com
  • player2 - player2@example.com
  ...
```

---

## Admin Routes Protected

All the following routes require admin privileges:

| Route | Purpose |
|-------|---------|
| `/admin` | Admin dashboard |
| `/admin/events` | View all events |
| `/admin/create-event` | Create new event |
| `/admin/add-task` | Add CTF challenge |
| `/admin/delete-event/<id>` | Delete event |
| `/admin/delete-task/<id>` | Delete challenge |
| `/admin/manage-teams` | Manage teams |
| `/admin/delete-team/<id>` | Delete team |
| `/admin/blogs` | View all blogs |
| `/admin/add-blog` | Create new blog post |
| `/admin/edit-blog/<id>` | Edit blog post |
| `/admin/delete-blog/<id>` | Delete blog post |

Non-admin users attempting to access these routes will receive a **403 Forbidden** error.

---

## Troubleshooting

### "403 Forbidden" when accessing /admin

**Cause:** You're not logged in as an admin user.

**Solution:**
1. Promote your account: `python promote_admin.py promote your-email@example.com`
2. Log out of the website
3. Log back in
4. Try accessing `/admin` again

### "User not found" error

**Cause:** The email doesn't exist in the database.

**Solution:**
1. Check available users: `python promote_admin.py users`
2. Verify the email is correct
3. Make sure the user has logged in at least once

### Changes not taking effect

**Cause:** Session cache - the user's session still has the old admin status.

**Solution:**
1. User must **log out completely**
2. Log back in
3. Admin privileges will now be active

---

## Best Practices

1. **Limit Admin Access**: Only promote trusted users to admin
2. **Regular Audits**: Periodically run `python promote_admin.py list` to review admins
3. **Revoke Promptly**: Remove admin access when no longer needed
4. **Use Strong Authentication**: Ensure admin accounts use secure passwords/OAuth
5. **Monitor Activity**: Keep track of admin actions in production

---

## Production Deployment

For production environments:

1. **Restrict Script Access**: Ensure `promote_admin.py` is only accessible to server administrators
2. **Environment Variables**: Store sensitive credentials in `.env` file
3. **Database Backups**: Always backup database before bulk admin changes
4. **Audit Logging**: Consider adding logging to track admin privilege changes
5. **Two-Factor Auth**: Implement 2FA for admin accounts (future enhancement)

---

## Quick Reference

```bash
# List admins
python promote_admin.py list

# Promote user
python promote_admin.py promote email@example.com

# Revoke admin
python promote_admin.py revoke email@example.com

# Check status
python promote_admin.py check email@example.com

# List all users
python promote_admin.py users

# Force operation (skip confirmation)
python promote_admin.py promote email@example.com --force
```
