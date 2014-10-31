'''Fropag initialization.'''
import os
from flask import Flask
from flask.ext.assets import Environment, Bundle
from model.core import boot_sql_alchemy
from database import db_session
import config

# Booting flask app
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
boot_sql_alchemy()

# Assets
# ASSETS
assets = Environment(app)
assets.load_path = [os.path.join(os.path.dirname(__file__), 'bower_components')]

assets.register(
    'css_all',
    Bundle(
        'bootstrap/dist/css/bootstrap.min.css',
        output="css_all.css"
    )
)
assets.register(
    'js_all',
    Bundle(
        'jquery/dist/jquery.min.js',
        'bootstrap/dist/js/bootstrap.min.js',
        'd3/d3.js'
    )
)

@app.teardown_appcontext
def shutdown_session(exception=None):
    '''Close the db_session when context ends.'''
    db_session.remove()

# Loading views
import web.public_views
import web.admin_views
import web.service_views
