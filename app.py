#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, send_file
import os
from flask_basicauth import BasicAuth
import requests

app = Flask(__name__)
requests.packages.urllib3.disable_warnings()

# Enable simple BasicAuth by setting envvars
username = os.environ.get("USERNAME", None)
password = os.environ.get("PASSWORD", None)
if username and password:
    app.config['BASIC_AUTH_USERNAME'] = username
    app.config['BASIC_AUTH_PASSWORD'] = password
    basic_auth = BasicAuth(app)
    app.config['BASIC_AUTH_FORCE'] = True
portainer_api_key = os.environ["PORTAINER_API_KEY"]
portainer_host = os.environ["PORTAINER_HOST"]
portainer_stacks = os.environ["PORTAINER_STACKS"]

# API Status codes for started/stopped
stack_statuses = {
    "start": 1,
    "stop": 2
}

stacks_list = portainer_stacks.split(',')
headers = {"X-Api-Key": portainer_api_key}
global last_error
last_error = ""

def get_stack_id(stack_name):
    try:
        req = requests.request("GET", f"{portainer_host}/api/stacks", headers=headers, verify=False)
        if req.ok:
            stacks_json = req.json()
            for stack in stacks_json:
                if stack["Name"] == stack_name:
                    print(f"Found Stack ID {stack['Id']}")
                    return True, None, stack["Id"], stack["EndpointId"], stack["Status"]
            return False, f"Failed to locate Stack {stack_name}", None, None, None
        return False, f"Portainer Error (ID): {req.status_code} - {req.text}", None, None, None
    except Exception as err:
        return False, f"Server Error (ID): {err}", None, None, None

def do_portainer_call(method, uri):
    global last_error
    try:
        req = requests.request(method, f"{portainer_host}{uri}", headers=headers, verify=False)
        if not req.ok:
            print(f"RESP ERROR: {req.status_code} - {req.text}")
            last_error = f"Portainer error: {req.status_code}\n{req.text}"
            return False
    except Exception as err:
        print(f"REQ ERROR: {err}")
        last_error = f"Server error: {err}"
        return False
    return True

@app.route('/', methods=['GET'])
def index():
    return render_template('generic_index.html', stacks=stacks_list)

@app.route('/<action>/<stack>', methods=['POST'])
def control_stack(action, stack):
    global last_error
    last_error = ""
    status, message, stack_id, endpoint_id, stack_status = get_stack_id(stack)
    if not status:
        print(message)
        return(message)
    if stack_status == stack_statuses[action]:
        return f"WARN: Stack {stack} is already {action}"
    if do_portainer_call("POST", f"/api/stacks/{stack_id}/{action}?endpointId={endpoint_id}"):
        print(f"OK: {stack} {action}")
        return f"OK: {stack} {action}"
    print(f"ERROR: {last_error}")
    return f"ERROR: {last_error}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5555, debug=True)
