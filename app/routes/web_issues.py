from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from app.models import Issue, Comment, User

web_issues_bp = Blueprint("web_issues", __name__)

def current_user():
    return User.query.get(session["user_id"]) if "user_id" in session else None

@web_issues_bp.route("/teams/<int:team_id>/dashboard")
def dashboard(team_id):
    userid = session["user_id"]
    if not userid:
        return redirect(url_for("web_auth.login"))
    
    session["current_team_id"] = team_id

    issues = Issue.query.filter_by(team_id = team_id).all()

    return render_template("issues.html", issues=issues)

@web_issues_bp.route("/issue/<int:issue_id>")
def issue_detail(issue_id):
    if not current_user():
        return redirect(url_for("web_auth.login"))
    issue = Issue.query.get_or_404(issue_id)
    return render_template("issue_detail.html", issue=issue)

@web_issues_bp.route("/issue/create", methods=["GET", "POST"])
def create_issue():
    userid = session["user_id"]
    teamid = session["current_team_id"]

    if not userid:
        return redirect(url_for("web_auth.login"))
    
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        issue = Issue(title=title, description=description, user_id = userid, team_id = teamid)
        db.session.add(issue)
        db.session.commit()
        flash("Issue created successfully!", "success")
        return redirect(url_for("web_issues.dashboard", team_id = teamid))
    return render_template("create_issue.html")

@web_issues_bp.route("/issue/<int:issue_id>/comment", methods=["POST"])
def add_comment(issue_id):
    if not current_user():
        return redirect(url_for("web_auth.login"))
    issue = Issue.query.get_or_404(issue_id)
    content = request.form["content"]
    comment = Comment(content=content, author=current_user(), issue=issue)
    db.session.add(comment)
    db.session.commit()
    flash("Comment added!", "success")
    return redirect(url_for("web_issues.issue_detail", issue_id=issue_id))

@web_issues_bp.route("/issue/<int:issue_id>/toggle", methods=["POST"])
def toggle_status(issue_id):
    if not current_user():
        return redirect(url_for("web_auth.login"))
    
    issue = Issue.query.get_or_404(issue_id)

    if issue:
        if issue.status == "open":
            issue.status = "working"
        elif issue.status == "working":
            issue.status = "resolved"
        else:
            issue.status = "open"
        db.session.commit()
    return redirect(url_for('web_issues.issue_detail', issue_id = issue.id))
        
            
