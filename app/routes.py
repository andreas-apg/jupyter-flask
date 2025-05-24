from flask import request, redirect, render_template, send_from_directory, session, url_for, flash
import os, subprocess, random, string
from .utils import *

load_dotenv()

DATA_DIR = os.environ.get("DATA_DIR")
TMP_DIR = os.environ.get("TMP_DIR")

def init_routes(app):
    @app.route("/images/<filename>")
    def images(filename):
        """Serve image files from the current directory."""
        return send_from_directory(os.path.join(app.root_path, 'static/images'), filename)

    @app.route("/", methods=["GET", "POST"])
    def login():
        """
        Display the login page and handle login POST requests.
        If credentials are valid and system is not locked, start JupyterLab.

        Returns:
            GET:
                - Rendered login template with:
                  * System status (locked/available)
                  * Current session duration (if locked)
                  * Error messages (if any)

            POST:
                - Successful auth:
                  * JupyterLab in new tab
                  * Redirect to home page
                - Failed auth:
                  * Error message in login template
                - System locked:
                  * Appropriate status message
        """
        message, locked, current_user, duration = "", os.path.exists(LOCK_FILE), "", "0 minutes"
        if locked:
            with open(LOCK_FILE, "r") as f: 
                current_user = f.read().strip()
            duration = get_session_duration()

        if request.method == "POST" and not locked:
            username, password = request.form.get("username"), request.form.get("password")
            users, user = load_users(), load_users().get(username)
            if not user or hash_password(password, user["salt"]) != user["hash"]:
                message = "Incorrect username or password."
            else:
                with open(LOCK_FILE, "w") as f: f.write(username)
                log_session_action(username, "start")
                jup_dir = os.path.abspath(f"{DATA_DIR}/{username}")
                os.makedirs(jup_dir, exist_ok=True)
                jup_pw = jupyter_hash(password)

                # stores the checkpoints in /tmp/, but the .jupyter configs of the user
                # are stored in their own folder
                config_dir = os.path.join(DATA_DIR, username, ".jupyter") 
                os.makedirs(config_dir, exist_ok=True)
                checkpoint_dir = os.path.join(TMP_DIR, username, '.ipynb_checkpoints')
                os.makedirs(checkpoint_dir, exist_ok=True)
                with open(os.path.join(config_dir, "jupyter_server_config.py"), "w") as f:
                    f.write(f"c.ServerApp.password = u'{jup_pw}'\n")
                    f.write("c.ServerApp.token = ''\n")
                    f.write(f"c.ServerApp.root_dir = r'{jup_dir}'\n")  # prevents access above
                    f.write(f"c.FileContentsManager.root_dir = r'{jup_dir}'\n")
                    f.write(f"c.FileCheckpoints.checkpoint_dir = r'{checkpoint_dir}'\n")

                proc = subprocess.Popen([
                    "jupyter", "lab", "--no-browser", "--ip=0.0.0.0", "--port=8888",
                    f"--NotebookApp.password={jup_pw}", "--NotebookApp.token=''",
                    f"--notebook-dir={jup_dir}", 
                    f"--config={os.path.join(config_dir, 'jupyter_server_config.py')}"
                ], cwd=jup_dir)
                with open(JUPYTER_PID_FILE, "w") as pf: pf.write(str(proc.pid))

                return f"<script>window.open('http://{get_local_ip()}:8888/lab', '_blank'); window.location.href='/'</script>"

        return render_template("login.html", message=message, locked=locked, current_user=current_user, ip=get_local_ip(), duration=duration)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """
        Display the registration page and handle user registration.
        Ensures unique usernames and matching passwords, creating
        a new user entry in users database.

        Returns:
            GET: Rendered registration template
            POST:
                - On success: Redirect to home page ('/')
                - On failure: Rendered registration template with error message
        """
        message = ""
        if request.method == "POST":
            username, password, confirm = request.form.get("username"), request.form.get("password"), request.form.get("confirm")
            users = load_users()
            if username in users: message = "Username already exists."
            elif password != confirm: message = "Passwords do not match."
            else:
                salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                users[username] = {"salt": salt, "hash": hash_password(password, salt)}
                save_users(users)
                return redirect("/")
        return render_template("register.html", message=message)

    @app.route("/release", methods=["POST"])
    def release():
        """
        Handle lock release. Only the user who set the lock can release it.
        Stops Jupyter if running and cleans up lock and PID files, logging
        the termination as end in the log file.

        Returns:
            - Redirect to home page on successful release
            - HTTP 403 Forbidden with message for:
                - Invalid credentials
                - User not being lock holder
            - Message if no active lock exists

        """
        username, password = request.form.get("username"), request.form.get("password")
        user = load_users().get(username)
        if not user or hash_password(password, user["salt"]) != user["hash"]:
            return render_template("login.html", message="Incorrect password.", locked=True, current_user=username, ip=get_local_ip(), duration=get_session_duration())
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r") as f: current_user = f.read().strip()
            if current_user == username:
                log_session_action(username, "end")
                release_lock()
                return redirect("/")
            else:
                return "You are not the current lock holder.", 403
        return "No active lock."


    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = load_users().get(username)
            
            if user and hash_password(password, user["salt"]) == user["hash"] and is_admin(username):
                session['admin_logged_in'] = True
                session['username'] = username
                return redirect(url_for('admin_logs'))
            
            flash("Invalid credentials.", "error")
        
        return render_template("admin_login.html")

    @app.route("/admin/logs", methods=["GET", "POST"])
    def admin_logs():
        """
        Handle admin log viewing requests.        
        This endpoint allows authenticated admin users to view system logs.

        Returns:
            - If authenticated: Rendered admin logs template with log data
            - If unauthorized: 403 Forbidden response
            - If wrong method: 405 Method Not Allowed response
        
        Note:
            Logs are displayed in reverse chronological order (newest first)
        """
        # If already logged in (session exists)
        if session.get('admin_authenticated'):
            logs = load_logs()
            username = session.get('admin_username')
            return render_template("admin_logs.html", current_user = username, logs=reversed(logs))
        
        # Handle POST (login attempt)
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            if is_admin(username):
                session['admin_authenticated'] = True
                session['admin_username'] = username
                return redirect(url_for('admin_logs'))  # Redirect to GET after POST
                
            return render_template("admin_login.html", error="Invalid credentials")
        
        # Handle GET (show login form)
        return render_template("admin_login.html")

    @app.route("/admin/force_release", methods=["POST"])
    def admin_force_release():
        """
        Force release the current JupyterLab session lock.
        """
        username = session.get('admin_username')

        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r") as f:
                locked_user = f.read().strip()
            logging.warning(f"Admin {username} force-releasing lock from {locked_user}")
            release_lock()
            log_session_action(locked_user, f"force-ended by {username}")  # Log the forced ending
        
        return redirect("/admin/logs?username={username}&password={password}")


    @app.route("/admin/clear_logs", methods=["POST"])
    def clear_logs():
        """
        Clear all system logs.
        """
        username = request.form.get("username")
        password = request.form.get("password")
        
        try:
            with open(LOG_FILE, "w") as f:
                f.write("")
            return redirect("/admin/logs?username={username}&password={password}")
        except Exception as e:
            return f"Error clearing logs: {e}", 500

        return redirect("/admin/logs?username={username}&password={password}")

    @app.route("/admin/logout", methods=["GET", "POST"])
    def admin_logout():
        """Clear admin session and redirect to login"""
        session.clear()  # Removes ALL session data
        flash("You have been logged out", "info")
        return redirect(url_for('admin_login'))  # Redirect to login page