# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask.ext.assets import Environment, Bundle

app = Flask(__name__)
app.debug = True
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

@app.route('/')
def index():
    return render_template('index.html', publication = [])

if __name__ == "__main__":
    app.run()


