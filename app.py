import streamlit as st
from dotenv import load_dotenv as env
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
import requests
import re
import os

# Load environment variables from .env file
env()

# Constants
SESSION_STATE_MAP = {
    "webhook_id": "webhook_id",
    "email": "email",
    "backup": "backup",
    "serverId": "server_id",
    "appId": "app_id",
    "deployPath": "deploy_path",
    "branchName": "branch_name",
    "stagingServerId": "staging_server_id",
    "stagingAppId": "staging_app_id",
    "type": "type",
    "apiKey": "api_key"
}

WEBHOOK_TYPE_MAP = {
    "deploy": "Deploy",
    "copytolive": "Copy to Live",
    "copytostaging": "Copy to Staging"
}

# Variables
app_url = "https://seal-app-ng3cf.ondigitalocean.app" if os.environ.get("PRODUCTION") == "True" else "http://localhost:3000"
api_url = f"{app_url}/webhook"
secret_key = os.environ.get("SECRET_KEY")
salt = get_random_bytes(16)
api_secret = os.environ.get("API_SECRET")
scrypt_key = scrypt(api_secret, salt, 32, N=2**14, r=8, p=1)

# Functions
def encrypt_api_key(api_key, key):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(api_key.encode('utf-8'))
    return {
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
        'tag': base64.b64encode(tag).decode('utf-8'),
        'nonce': base64.b64encode(cipher.nonce).decode('utf-8')
    }

def reset_action_completed(webhook_id_changed=False):
    st.session_state["action_completed"] = False
    webhook_id = st.session_state["webhook_id"].strip()
    if len(webhook_id) == 26 and webhook_id_changed:
        payload = {"secretKey": secret_key}
        st.session_state["api_endpoint"] = f"{api_url}/{webhook_id}"
        webhook_details = requests.post(f"{st.session_state['api_endpoint']}/details", json=payload)
        if webhook_details.status_code == 200:
            webhook = webhook_details.json()
            for key, value in webhook.items():
                if key != "type" and key != "email":
                    st.session_state[SESSION_STATE_MAP.get(key)] = value
                elif key == "email":
                    continue
                else:
                    st.session_state[key] = WEBHOOK_TYPE_MAP.get(value)
        else:
            st.error(f"Failed to retrieve webhook details: {webhook_details.text}", icon="❌")
    elif st.session_state["webhook_action"] != "create" and len(webhook_id) == 0:
        clear_form_fields()

def clear_form_fields():
    for key in SESSION_STATE_MAP.values():
        if key == "type":
            st.session_state[key] = None
        elif key == "backup":
            st.session_state[key] = False
        else:
            st.session_state[key] = ""
    st.session_state["action_completed"] = False

def create_webhook():
    st.session_state["webhook_action"] = "create"
    st.session_state["api_method"] = "POST"
    st.session_state["api_endpoint"] = f"{api_url}/add"
    clear_form_fields()

def update_webhook(webhook_id=""):
    st.session_state["webhook_action"] = "update"
    st.session_state["api_method"] = "PUT"
    st.session_state["api_endpoint"] = f"{api_url}/{st.session_state['webhook_id']}"
    clear_form_fields()

def delete_webhook(webhook_id=""):
    st.session_state["webhook_action"] = "delete"
    st.session_state["api_method"] = "DELETE"
    st.session_state["api_endpoint"] = f"{api_url}/{st.session_state['webhook_id']}"
    clear_form_fields()

# Instantiate session state with default values
default_values = {
    "api_key": "",
    "server_id": "",
    "app_id": "",
    "deploy_path": "",
    "branch_name": "",
    "staging_server_id": "",
    "email": "",
    "webhook_id": "",
    "action_completed": False,
    "webhook_action": "create",
    "type": None,
    "api_method": "POST",
    "api_endpoint": f"{api_url}/add",
    "backup": False
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Streamlit app
st.set_page_config(page_title="Webhooks for Git Deployments - Cloudways", page_icon="☁️")
st.image("https://i.imgur.com/jg9Vyjm.png", use_column_width=False, width=250)

# Webhook actions
if st.session_state["webhook_action"] == "create":
    st.subheader("Create a new webhook for git deploys", anchor=False)
    st.button("Change Action: Update Webhook", on_click=update_webhook)
elif st.session_state["webhook_action"] == "update":
    st.subheader("Update an existing webhook for git deploys", anchor=False)
    st.button("Change Action: Delete Webhook", on_click=delete_webhook)
    webhook_id = st.text_input(
        "Webhook ID", 
        placeholder="Enter a Webhook ID to populate its details", 
        on_change=reset_action_completed, 
        key="webhook_id", 
        autocomplete="on", 
        args=(True,)
    )
elif st.session_state["webhook_action"] == "delete":
    st.subheader("Delete an existing webhook", anchor=False)
    st.button("Change Action: Create Webhook", on_click=create_webhook)
    webhook_id = st.text_input(
        "Webhook ID", 
        on_change=reset_action_completed, 
        key="webhook_id", 
        autocomplete="on"
    )

# Form inputs
email = st.text_input(
    "Email", 
    on_change=reset_action_completed, 
    key="email", 
    autocomplete="email", 
    placeholder=f"Confirm the email address to {st.session_state['webhook_action']} the webhook" if st.session_state["webhook_action"] != "create" else ""
)

if st.session_state["webhook_action"] == "create":
    api_key = st.text_input(
        "API Key", 
        on_change=reset_action_completed, 
        key="api_key", 
        autocomplete="on", 
        placeholder="Optional: Enter to use your own API key", 
        type="password"
    )

if st.session_state["webhook_action"] != "delete":
    server_id = st.text_input(
        "Server ID", 
        on_change=reset_action_completed, 
        key="server_id", 
        autocomplete="on"
    )
    app_id = st.text_input(
        "App ID", 
        on_change=reset_action_completed, 
        key="app_id", 
        autocomplete="on"
    )
    type = st.selectbox(
        "Type", 
        WEBHOOK_TYPE_MAP.values(), 
        index=None, 
        placeholder="Select a webhook type...", 
        on_change=reset_action_completed, 
        key="type"
    )

if st.session_state["type"] == "Deploy":
    deploy_path = st.text_input(
        "Deploy Path", 
        on_change=reset_action_completed, 
        key="deploy_path", 
        autocomplete="on"
    )
    branch_name = st.text_input(
        "Branch Name", 
        on_change=reset_action_completed, 
        key="branch_name", 
        autocomplete="on"
    )
elif st.session_state["type"] in ["Copy to Live", "Copy to Staging"] and st.session_state["webhook_action"] != "delete":
    staging_server_id = st.text_input(
        "Staging Server ID", 
        on_change=reset_action_completed, 
        key="staging_server_id", 
        autocomplete="on"
    )
    staging_app_id = st.text_input(
        "Staging App ID", 
        on_change=reset_action_completed, 
        key="staging_app_id", 
        autocomplete="on"
    )

if st.session_state["webhook_action"] != "delete":
    backup = st.checkbox(
        "Take backup first", 
        on_change=reset_action_completed, 
        key="backup", 
        value=False
    )

# Form submission
if not st.session_state["action_completed"]:
    if st.session_state["webhook_action"] == "delete":
        button_label = "Delete the Webhook"
    else:
        button_label = f"{'Update the' if st.session_state['webhook_action'] == 'update' else 'Create a'} {st.session_state['type'] if st.session_state['type'] else ''} Webhook"
    
    if st.button(button_label):
        # Validate email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        # Validate form fields
        if not re.match(email_pattern, st.session_state["email"]):
            st.error("Invalid email address.")
        elif (not st.session_state["server_id"] or not st.session_state["app_id"]) and st.session_state["webhook_action"] != "delete":
            st.error("Server ID and App ID are required.")
        elif (st.session_state["type"] == "Deploy" and not st.session_state["branch_name"]):
            st.error("Branch Name is required.")
        elif (st.session_state["type"] in ["Copy to Live", "Copy to Staging"] and (not st.session_state["staging_server_id"] or not st.session_state["staging_app_id"])):
            st.error("Staging Server ID and Staging App ID are required.")
        else:
            normalized_type = st.session_state["type"].lower().replace(" ", "") if st.session_state["type"] else None
            api_key = st.session_state["api_key"].strip() if st.session_state["api_key"] else os.environ.get("API_KEY")
            if api_key:
                encrypted_api_key = encrypt_api_key(api_key, scrypt_key)
                api_key = {
                    'salt': base64.b64encode(salt).decode('utf-8'),
                    'ciphertext': encrypted_api_key['ciphertext'],
                    'tag': encrypted_api_key['tag'],
                    'nonce': encrypted_api_key['nonce']
                }
            # Construct the payload
            payload = {
                "secretKey": os.environ.get("SECRET_KEY", secret_key),
                "backup": st.session_state["backup"],
                "email": st.session_state["email"].strip(),
                "type": normalized_type,
                "apiKey": api_key
            }

            # Add additional fields based on the webhook type
            if st.session_state["type"] == "Deploy":
                payload["deployPath"] = st.session_state["deploy_path"].strip()
                payload["branchName"] = st.session_state["branch_name"].strip()
            elif st.session_state["type"] in ["Copy to Live", "Copy to Staging"]:
                payload["stagingServerId"] = st.session_state["staging_server_id"].strip()
                payload["stagingAppId"] = st.session_state["staging_app_id"].strip()

            # Set API endpoint based on the webhook action
            if st.session_state["webhook_action"] == "create":
                st.session_state["api_endpoint"] = f"{api_url}/add"
            elif st.session_state["webhook_action"] == "update":
                st.session_state["api_endpoint"] = f"{api_url}/{st.session_state['webhook_id']}"
            elif st.session_state["webhook_action"] == "delete":
                st.session_state["api_endpoint"] = f"{api_url}/{st.session_state['webhook_id']}"

            # Post request to the API
            try:
                if st.session_state["api_method"] == "POST":
                    response = requests.post(st.session_state["api_endpoint"], json=payload)
                elif st.session_state["api_method"] == "PUT":
                    response = requests.put(st.session_state["api_endpoint"], json=payload)
                elif st.session_state["api_method"] == "DELETE":
                    response = requests.delete(st.session_state["api_endpoint"], json=payload)
                else:
                    st.error("Invalid API method.")
                
                response.raise_for_status()  # Raise an exception for HTTP errors

                # Handle response
                if st.session_state["webhook_action"] == "delete":
                    st.success(f"Webhook {st.session_state['webhook_id']} was deleted successfully.", icon="✅")
                elif st.session_state["webhook_action"] == "update":
                    st.success(f"Webhook {st.session_state['webhook_id']} was updated successfully.", icon="✅")
                else:
                    new_webhook = response.json()
                    webhook_url = f"{api_url}/{new_webhook['webhookId']}"
                    st.success(f"Your Webhook was created successfully. ID: {new_webhook['webhookId']}", icon="✅")
                    st.session_state["action_completed"] = True

                    st.components.v1.html(f"""
                    <div>
                        <style>
                        :root {{
                            --stButton-primary-color: #2F39BF;
                        }}
                        #webhookUrl {{
                            position: absolute;
                            left: -1000px;
                        }}
                        #copyBtn {{
                            cursor: pointer;
                            padding: 0.5rem;
                            background-color: rgb(255, 255, 255);
                            border: 1px solid rgba(49, 51, 63, 0.2);
                            border-radius: 0.5rem;
                            font-family: "Source Sans Pro", sans-serif;
                        }}
                        #copyBtn:hover {{
                            color: var(--stButton-primary-color);
                            border-color: var(--stButton-primary-color);
                        }}
                        #buttonContainer {{
                            display: flex;
                            justify-content: center;
                            margin-top: 1rem;
                        }}
                        button[title="View fullscreen"]{{
                            display: none;
                        }}
                        </style>
                        <input type="text" value="{webhook_url}" id="webhookUrl" readonly />
                        <div id="buttonContainer">
                            <button onclick="copyToClipboard()" id="copyBtn">Copy Webhook URL</button>
                        </div>
                    </div>
                    <script>
                        function copyToClipboard() {{
                            var copyText = document.getElementById("webhookUrl");
                            copyText.select();
                            copyText.setSelectionRange(0, 99999); // For mobile devices
                            document.execCommand("copy");
                            document.getElementById("copyBtn").innerText = "Copied!";
                        }}
                    </script>
                    """, height=100)
            except requests.exceptions.RequestException as e:
                st.error(f"API request failed: {e}")
else:
    st.warning("Webhook already created.", icon="⚠️")