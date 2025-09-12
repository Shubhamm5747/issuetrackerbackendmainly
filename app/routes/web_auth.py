from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db, bcrypt, google
from app.models import User
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import timedelta


web_auth_bp = Blueprint("web_auth", __name__)

@web_auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists!", "danger")
            return redirect(url_for("web_auth.register"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("web_auth.login"))
    return render_template("register.html")

@web_auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.password_hash is None:
            flash("This account uses Google login Please sign in with google.", "danger")
            return render_template("login.html")
        
        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("web_teams.view_teams"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@web_auth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('web_auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri, prompt='consent')

@web_auth_bp.route('/google-callback')
def google_callback():
    token = google.authorize_access_token() #exhanging token or id_token for authorisation code
    resp = google.get('userinfo') #google userinfo API endpoint along with Authorization: Bearer <Access Token>|
    user_info = resp.json()
    email = user_info['email']
    raw_name = user_info['name']
    name = raw_name.replace(" ", "").lower()

    # Check if user already exists
    user = User.query.filter_by(email=email).first()

    if not user:
        #register new oauth user with dummy password
        # dummy_password = bcrypt.generate_password_hash("google-oauth-user").decode('utf-8')
        user = User(email = email, username = name)
        db.session.add(user)
        db.session.commit()

    # Normal web session login
    session['user_id'] = user.id
    session['user'] = user.username

    # Generate JWTs for API usage
    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(minutes=60))
    refresh_token = create_refresh_token(identity=str(user.id), expires_delta=timedelta(hours=3))

    # Stash tokens in session so tasks page can show them (DEV ONLY)
    session['api_access_token'] = access_token
    session['api_refresh_token'] = refresh_token

    flash('Logged in with google!', 'success')
    return redirect(url_for('web_teams.view_teams'))

@web_auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("web_auth.login"))
