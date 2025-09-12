from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Team, TeamMember, Issue, Comment, User

web_teams_bp = Blueprint("web_teams", __name__)

# ----------------------------
# Create a Team
# ----------------------------
def current_user():
    return User.query.get(session["user_id"]) if "user_id" in session else None 

@web_teams_bp.route("/team/create", methods=["GET", "POST"])
def create_team():
    userid = session["user_id"]
    if not userid:
        return redirect(url_for("web_auth.login"))
    
    if request.method == "POST":
        team_name = request.form["name"].strip()
        if not team_name:
            flash("Team name cannot be empty.", "danger")
            return redirect(url_for("web_teams.create_team"))

        # check if name already exists
        if Team.query.filter_by(name=team_name).first():
            flash("Team name already exists.", "danger")
            return redirect(url_for("web_teams.create_team"))

        team = Team(name=team_name)
        db.session.add(team)
        db.session.commit()

        # add creator as team member (manager)
       
        membership = TeamMember(user_id=userid, team_id=team.id, role="manager")
        db.session.add(membership)
        db.session.commit()

        flash(f"Team '{team_name}' created! Invite code: {team.invite_code}", "success")
        return redirect(url_for("web_teams.view_teams"))

    return render_template("create_team.html")

# ----------------------------
# Join a Team via Invite Code
# ----------------------------
@web_teams_bp.route("/team/join", methods=["GET", "POST"])
def join_team():
    if request.method == "POST":
        invite_code = request.form["invite_code"].strip()
        team = Team.query.filter_by(invite_code=invite_code).first()
        if not team:
            flash("Invalid invite code.", "danger")
            return redirect(url_for("web_teams.join_team"))

        userid = session["user_id"]
        # check if user already in team
        if any(m.user_id == userid for m in team.members):
            flash("You are already a member of this team.", "info")
            return redirect(url_for("web_teams.view_teams"))

        # add user to team
        membership = TeamMember(user_id=userid, team_id=team.id, role="member")
        db.session.add(membership)
        db.session.commit()

        flash(f"You joined the team '{team.name}'!", "success")
        return redirect(url_for("web_teams.view_teams"))

    return render_template("join_team.html")

# ----------------------------
# View Teams Current User Belongs To
# ----------------------------

@web_teams_bp.route("/teams")
def view_teams():
    userid = session["user_id"]
    memberships = TeamMember.query.filter_by(user_id=userid).all()
    return render_template("teams.html", memberships=memberships)
