from flask import Blueprint, request, jsonify
from app import db
from app.models import Issue, Comment, User
from flask_jwt_extended import jwt_required, get_jwt_identity

api_issues_bp = Blueprint("api_issues", __name__, url_prefix="/api")

# Helper to fetch current user
def current_user():
    uid = get_jwt_identity()
    return User.query.get(uid)

@api_issues_bp.route("/teams", methods=["GET"])
@jwt_required()
def teams_dashboard():
    uid = get_jwt_identity()
    user = User.query.get(uid)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch all teams via TeamMember relationship
    teams = [
                {
                    "id": member.team.id,
                    "name": member.team.name,
                    "role": member.role,
                    "joined_at": member.joined_at.isoformat()
                }
                for member in user.teams
            ]

    return jsonify({"teams": teams}), 200
    

# List issues by team
@api_issues_bp.route("teams/<int:team_id>", methods=["GET"])
@jwt_required()
def api_dashboard(team_id):
    # Query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    status_filter = request.args.get("status", None, type=str)
    sort_field = request.args.get("sort", "created_at", type=str)
    sort_order = request.args.get("order", "desc", type=str)

    query = Issue.query.filter_by(team_id=team_id)

    # Apply filter
    if status_filter:
        query = query.filter(Issue.status == status_filter)

    # Apply sorting (default: created_at desc)
    if hasattr(Issue, sort_field):
        sort_col = getattr(Issue, sort_field)
        if sort_order == "desc":
            sort_col = sort_col.desc()
        query = query.order_by(sort_col)

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    issues = pagination.items

    return jsonify({
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "issues": [{
            "issue_id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "status": issue.status,
            "user_id": issue.user_id,
            "username": issue.author.username if issue.author else None,
            "created_at": issue.created_at
        } for issue in issues]
    }), 200



# -------------------------
# Get issue detail
# -------------------------
@api_issues_bp.route("teams/issue_detail/<int:issue_id>", methods=["GET"])
@jwt_required()
def get_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    return jsonify({
        "id": issue.id,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "created_at": issue.created_at.isoformat(),
        "author": issue.author.username,
        "team_id": issue.team_id,
        "comments": [
            {
                "id": c.id,
                "content": c.content,
                "author": c.author.username,
                "created_at": c.created_at.isoformat()
            } for c in issue.comments
        ]
    }), 200


# -------------------------
# Create issue
# -------------------------
@api_issues_bp.route("teams/create", methods=["POST"])
@jwt_required()
def create_issue():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    team_id = data.get("team_id")

    if not (title and description and team_id):
        return jsonify({"error": "title, description, and team_id required"}), 400

    issue = Issue(title=title, description=description, user_id=user.id, team_id=team_id)
    db.session.add(issue)
    db.session.commit()

    return jsonify({
        "message": "Issue created successfully",
        "issue": {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "status": issue.status,
            "author": user.username,
            "team_id": issue.team_id
        }
    }), 201


# -------------------------
# Add comment
# -------------------------
@api_issues_bp.route("issue_detail/<int:issue_id>/comment", methods=["POST"])
@jwt_required()
def add_comment(issue_id):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    issue = Issue.query.get_or_404(issue_id)
    data = request.get_json() or {}
    content = data.get("content")

    if not content:
        return jsonify({"error": "content required"}), 400

    comment = Comment(content=content, author=user, issue=issue)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "message": "Comment added",
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "author": user.username,
            "issue_id": issue.id,
            "created_at": comment.created_at.isoformat()
        }
    }), 201


# -------------------------
# Toggle issue status
# -------------------------
@api_issues_bp.route("/<int:issue_id>/toggle", methods=["POST"])
@jwt_required()
def toggle_status(issue_id):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    issue = Issue.query.get_or_404(issue_id)

    if issue.status == "open":
        issue.status = "working"
    elif issue.status == "working":
        issue.status = "resolved"
    else:
        issue.status = "open"

    db.session.commit()

    return jsonify({
        "message": "Status updated",
        "issue": {
            "id": issue.id,
            "title": issue.title,
            "status": issue.status
        }
    }), 200
