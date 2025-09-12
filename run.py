from app import create_app, db

app = create_app()

from app.models import User, Issue, Comment

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
    