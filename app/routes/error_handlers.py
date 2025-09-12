from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import traceback

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            "error" : {
                "code" : e.code,
                "name" : e.name,
                "description" : e.description
            }
        }), e.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        return jsonify({
            "error" : {
                "code" : 500,
                "name" : "Internal server error",
                "description" : str(e), #dont show it in the production might have internal info 
                "trace" : traceback.format_exc() #dont show it in the production might have internal info, show only in development
            }
        }), 500
    
    @app.errorhandler(ZeroDivisionError)
    def handle_zero_division(e):
        return jsonify({
            "error": {
                "code": 500,
                "name": "Math Error",
                "description": "You cannot divide by zero."
            }
        }), 500
    
    # Catch KeyError (e.g., accessing missing dict key)
    @app.errorhandler(KeyError)
    def handle_key_error(e):
        return jsonify({
            "error": {
                "code": 500,
                "name": "Key Error",
                "description": f"Missing key: {str(e)}"
            }
        }), 500
    
    # Catch SQLAlchemy errors (e.g., invalid DB operation)
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(e):
        print("=== REAL ERROR ===")
        traceback.print_exc()  # logs full error trace in terminal
        return jsonify({
            "error": {
                "code": 500,
                "name": "Database Error",
                "description": "A database error occurred."
            }
        }), 500
    


