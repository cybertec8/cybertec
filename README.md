<!-- cspell:words Cybertec Cybertec8 cybertec cybertec8ctf venv SQLAlchemy -->

# Cybertec8 CTF Platform

A Flask-based Capture The Flag (CTF) web application for hosting cybersecurity competitions and events.

## Features

- User authentication with OTP email verification
- Admin dashboard for managing events and tasks
- Team management system
- CTF task creation and submission
- Event organization
- User profiles and team memberships
- **Maintenance mode** for temporarily disabling authentication

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. **Clone or download the repository**

2. **Navigate to the project directory**
   ```bash
   cd cybertec8ctf\cybertec8ctf
   ```

3. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

5. **Install required packages**
   ```bash
   pip install Flask Flask-SQLAlchemy Flask-Login
   ```

## Configuration

### Email Settings (Optional)

The application uses Gmail for sending OTP emails. To enable this feature:

1. Open `app.py`
2. Update the email credentials:
   ```python
   EMAIL_ADDRESS = "your-email@gmail.com"
   EMAIL_PASSWORD = "your-app-password"
   ```

**Note:** Use an [App Password](https://support.google.com/accounts/answer/185833) for Gmail, not your regular password.

### Secret Key (Important for Production)

For production deployment, change the secret key in `app.py`:
```python
app.config["SECRET_KEY"] = "your-secure-random-secret-key"
```

### Maintenance Mode (Optional)

To temporarily disable signup and login (e.g., during maintenance), set `AUTH_ENABLED = False` in `app.py`:

```python
# ---------------- MAINTENANCE MODE ----------------

# Set to False to disable authentication (maintenance mode)
AUTH_ENABLED = False
```

When disabled:
- All pages remain accessible without login
- Signup and login routes redirect to home
- A warning banner appears: "Sign-up and Login are temporarily disabled for maintenance"
- Auth buttons are grayed out and disabled

See [MAINTENANCE_MODE.md](MAINTENANCE_MODE.md) for detailed documentation.

## Running the Application

1. **Make sure you're in the correct directory**
   ```bash
   cd cybertec8ctf\cybertec8ctf
   ```

2. **Activate virtual environment** (if not already activated)
   ```bash
   venv\Scripts\activate
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   
   Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
   or
   ```
   http://localhost:5000
   ```

## First Time Setup

When you run the application for the first time:
- The SQLite database will be automatically created at `instance/ctf.db`
- The database tables will be initialized

## Usage

### Creating an Account
1. Navigate to the sign up page
2. Enter your details
3. Verify your email with the OTP sent to your email address
4. Login with your credentials

### Admin Access
To grant admin privileges to a user, you'll need to manually update the database or create an admin route in the code.

### Creating Teams
1. Login to your account
2. Navigate to the teams section
3. Create a new team or join existing teams using invite codes

### Participating in Events
1. Browse available CTF events
2. Join events with your team
3. Solve tasks to earn points

## Project Structure

```
cybertec8ctf/
├── app.py              # Main application file
├── models.py           # Database models
├── instance/           # Database files
│   └── ctf.db         # SQLite database
├── static/            # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   ├── img/
│   └── avatars/
└── templates/         # HTML templates
    ├── home.html
    ├── auth/          # Authentication pages
    ├── admin/         # Admin pages
    └── console/       # User dashboard pages
```

## Database Models

- **User** - User accounts with authentication
- **Team** - Team information and invite codes
- **TeamMember** - Team membership records
- **TeamRequest** - Join requests for teams
- **Event** - CTF events
- **CTFTask** - Individual challenges/tasks
- **TaskSolve** - Task completion records
- **TaskLike** - Task ratings
- **TaskSubmission** - Flag submission attempts

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, you can change it in `app.py`:
```python
app.run(debug=True, port=5001)
```

### Database Errors
If you encounter database errors, delete the `instance/ctf.db` file and restart the application to recreate the database.

### Email OTP Not Working
- Ensure you're using a Gmail App Password
- Check your internet connection
- Verify the email credentials in `app.py`

## Security Notes

⚠️ **Important for Production:**
- Change the `SECRET_KEY` to a strong, random value
- Set `debug=False` in production
- Use environment variables for sensitive data
- Implement proper authentication and authorization
- Use HTTPS in production
- Regularly update dependencies

## Development

To run in development mode with auto-reload:
```bash
python app.py
```

The application runs with `debug=True` by default, which enables:
- Auto-reload on code changes
- Detailed error pages
- Debug toolbar

## License

This project is for educational purposes.

## Support

For issues or questions, please contact the development team or create an issue in the repository.
