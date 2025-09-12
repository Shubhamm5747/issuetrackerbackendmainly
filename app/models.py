# app/models.py
from datetime import datetime
from app import db, bcrypt
from zoneinfo import ZoneInfo
import secrets

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # nullable for OAuth users
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

    issues = db.relationship("Issue", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    teams = db.relationship("TeamMember", back_populates="user", cascade="all, delete")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    invite_code = db.Column(db.String(32), unique=True, default=lambda: secrets.token_urlsafe(16))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))

    # Relationships
    members = db.relationship("TeamMember", back_populates="team", cascade="all, delete")
    issues = db.relationship("Issue", backref="team", lazy=True, cascade="all, delete")

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    role = db.Column(db.String(20), default="member")  # optional, e.g., manager/member
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))

    user = db.relationship("User", back_populates="teams")
    team = db.relationship("Team", back_populates="members")

    __table_args__ = (
        db.UniqueConstraint("user_id", "team_id", name="uq_user_team"),
        db.Index("ix_user_team", "user_id", "team_id"),
    )

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open")  # open, in-progress, closed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    comments = db.relationship("Comment", backref="issue", lazy=True, cascade="all, delete")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey("issue.id"), nullable=False)

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
