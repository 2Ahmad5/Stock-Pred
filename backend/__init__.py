from flask import Flask
from regression_backtestingV5_3 import regres
from robust_mv10 import main
from run_regression_final import run_regress
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    # Register blueprints
    app.register_blueprint(regres)
    app.register_blueprint(main)
    app.register_blueprint(run_regress)

    return app