import sys
import os
import logging
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().propagate = True

import json
import flask
from flask import Flask, request, send_from_directory, jsonify, redirect, session, url_for, make_response, render_template
from flask_jsontools import jsonapi
from werkzeug.contrib.fixers import ProxyFix

import oidc
from oidc.oidc import TokenIntrospection
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']
rs = TokenIntrospection(client_id, client_secret)

app = Flask(__name__)
app.debug = False
app.wsgi_app = ProxyFix(app.wsgi_app)

API_BASE = os.environ['API_BASE']



roles = {}
def load_roles():
    r = os.environ['WARDEN_VOLUME_ROOT']
    with open(r + '/roles.json','r') as f:
        global roles
        roles = json.loads(f.read())
load_roles()

def find_in_roles(uid, role):
    return role in roles and uid in roles[role]



@app.route(API_BASE + '/allowed', methods=['POST'])
@rs.require_token_scopes(scopes=['warden'])
@jsonapi
def allowed(token=None):
    return {'allowed':True}

@app.route(API_BASE + '/profile', methods=['POST'])
@rs.require_token_scopes(scopes=['warden'])
@jsonapi
def profile(token=None):
    data = request.json
    uid = data['token']['sub']
    return {
        'profile': find_in_roles(uid, data['profile'])
    }

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'

    '''
        para autorizar el CORS
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS
    '''
    """
    o = request.headers.get('Origin', None)
    rm = request.headers.get('Access-Control-Request-Method', None)
    rh = request.headers.get('Access-Control-Request-Headers', None)

    r.headers['Access-Control-Allow-Methods'] = 'PUT,POST,GET,HEAD,DELETE'
    r.headers['Access-Control-Allow-Origin'] = '*'
    if rh:
        r.headers['Access-Control-Allow-Headers'] = rh
    r.headers['Access-Control-Max-Age'] = 1
    """

    return r

def main():
    app.run(host='0.0.0.0', port=9010, debug=True)

if __name__ == "__main__":
    main()
