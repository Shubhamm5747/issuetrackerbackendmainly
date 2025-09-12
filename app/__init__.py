from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Global extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
oauth = OAuth()
google = None


def create_app():
    app = Flask(__name__)


    #add config_name in function params for testing
    # if config_name == "testing":
    #     app.config["TESTING"] = True
    #     app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    #     app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Config ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///issues.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT Config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 604800))
    )

    # Google OAuth2 Config
    app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")
    app.config['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv("OAUTHLIB_INSECURE_TRANSPORT") == "True"

    # --- Security ---
    Talisman(app, content_security_policy=None)  # basic CSP
    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)  # allow frontend dev

    # --- Init extensions ---
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    oauth.init_app(app)

    # --- JWT Token Blocklist (Revocation Check) ---
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from app.models import TokenBlocklist
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None
    
# Register Google login provider 
    global google
    google = oauth.register(
        name='google',
        client_id = app.config['GOOGLE_CLIENT_ID'], #Your application's public identifier issued by google, it tells which application is requesting access.
        client_secret=app.config['GOOGLE_CLIENT_SECRET'], #Your application's confidential secret key issued by google, It proves that the request for tokens is coming from a legitimate, trusted application.
        access_token_url='https://oauth2.googleapis.com/token', #URL where your Client Application's backend sends the authorization_code (along with client_id and client_secret) to exchange it for access_token and id_token.
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth', #the URL to which your Client Application redirects the user's browser to initiate the OAuth flow and obtain user consent
        authorize_params=None, #Part of the authorization request
        api_base_url='https://www.googleapis.com/oauth2/v1/', #after we obtained access token our google.get('userinfo') call implicitly uses this base URL 
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",  # <--- IMPORTANT
        userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',  # required #While id_token carries basic claims, this endpoint provides the canonical user profile
        client_kwargs={
            'scope': 'openid email profile' #mandatory scope for OpenID Connect, signaling that you want to perform authentication and receive an id_token
        }
    )

    # Register Error Handlers
    from app.routes.error_handlers import register_error_handlers
    register_error_handlers(app)

    # --- Register Blueprints ---
    from app.routes.web_auth import web_auth_bp
    from app.routes.web_issues import web_issues_bp
    from app.routes.api_auth import api_auth_bp
    from app.routes.api_issues import api_issues_bp
    from app.routes.web_teams import web_teams_bp

    app.register_blueprint(web_auth_bp)
    app.register_blueprint(web_issues_bp)
    app.register_blueprint(api_auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_issues_bp, url_prefix="/api/issues")
    app.register_blueprint(web_teams_bp)

    return app


__all__ = ['db', 'bcrypt', 'limiter', 'oauth', 'google']
