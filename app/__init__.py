from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    # It's good practice to load secret keys from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_default_secret_key_for_development')

    # Import and register blueprints (routes)
    from . import routes
    # Assuming your routes are defined in a Blueprint named 'bp' in routes.py
    # We will create this blueprint in the next step
    # app.register_blueprint(routes.bp)

    # Register the main routes directly for now until blueprint is set up
    from .routes import main_routes
    app.register_blueprint(main_routes)


    # Initialize extensions here if needed (e.g., db, auth)

    return app
