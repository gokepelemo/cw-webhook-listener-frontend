import streamlit as st
from dotenv import load_dotenv as env
import requests
import re
import os

# Load environment variables from .env file
env()

# Constants
WEBHOOK_TYPES = ["Deploy", "Copy to Live", "Copy to Staging"]

# Variables
webhook_id = ""
api_url = "http://localhost:3000/webhook"
webhook_url = "https://seal-app-ng3cf.ondigitalocean.app/webhook"
secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

# Functions
def parse_webhook_type(webhook_type):
    try:
        return WEBHOOK_TYPES.index(webhook_type)
    except ValueError:
        return None

def reset_action_completed():
    st.session_state["action_completed"] = False

def create_webhook():
    st.session_state["webhook_action"] = "create"
    st.session_state["api_method"] = "POST"
    st.session_state["api_endpoint"] = f"{api_url}/add"

def update_webhook(webhook_id=""):
    st.session_state["webhook_action"] = "update"
    st.session_state["api_method"] = "PUT"
    st.session_state["api_endpoint"] = f"{api_url}/{webhook_id}"
    
def delete_webhook(webhook_id=""):
    st.session_state["webhook_action"] = "delete"
    st.session_state["api_method"] = "DELETE"
    st.session_state["api_endpoint"] = f"{api_url}/{webhook_id}"
    
def simulate_update_webhook():
    return {server_id: "123", app_id: "456", type: "Deploy", deploy_path: "public", branch_name: "main"}

# Instantiate session state with default values
default_values = {
    "email": "",
    "action_completed": False,
    "webhook_action": "create",
    "server_id": "",
    "app_id": "",
    "type": None,
    "api_method": "POST",
    "api_endpoint": f"{api_url}/add",
    "webhook_id": "",
    "deploy_path": "",
    "branch_name": "",
    "staging_server_id": "",
    "staging_app_id": "",
    "backup": False
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value


# Streamlit app
st.set_page_config(page_title="Webhooks for Git Deployments - Cloudways", page_icon="☁️")
st.image("https://i0.wp.com/jaamiah.com/wp-content/uploads/2023/07/Cloudways-by-DO-Vertical-Blue@2x.png", use_column_width=False, width=250)

# Webhook actions
if st.session_state["webhook_action"] == "create":
    st.button("Change Action: Update Webhook", on_click=update_webhook)
    st.subheader("Create a new webhook for git deploys", anchor=False)
elif st.session_state["webhook_action"] == "update":
    st.button("Change Action: Delete Webhook", on_click=delete_webhook)
    st.subheader("Update an existing webhook for git deploys", anchor=False)
    webhook_id = st.text_input("Webhook ID")
elif st.session_state["webhook_action"] == "delete":
    st.button("Change Action: Create Webhook", on_click=create_webhook)
    st.subheader("Delete an existing webhook", anchor=False)
    webhook_id = st.text_input("Webhook ID")

# Form inputs
email = st.text_input("Email", on_change=reset_action_completed, key="email", value=st.session_state.get("email", ""), autocomplete="email")
server_id = st.text_input("Server ID", on_change=reset_action_completed, key="server_id", value=st.session_state.get("server_id", ""), autocomplete="on")
app_id = st.text_input("App ID", on_change=reset_action_completed, key="app_id", value=st.session_state.get("app_id", ""), autocomplete="on")
type = st.selectbox("Type", WEBHOOK_TYPES, index=parse_webhook_type(st.session_state.get("type", "")), placeholder="Select a webhook type...", on_change=reset_action_completed, key="type")

if type == "Deploy":
    deploy_path = st.text_input("Deploy Path", on_change=reset_action_completed, key="deploy_path", value=st.session_state.get("deploy_path", ""), autocomplete="on")
    branch_name = st.text_input("Branch Name", on_change=reset_action_completed, key="branch_name", value=st.session_state.get("branch_name", ""), autocomplete="on")
    backup=st.toggle("Take backup first", on_change=reset_action_completed, key="backup", value=False)
elif type == "Copy to Live" or type == "Copy to Staging":
    staging_server_id = st.text_input("Staging Server ID", on_change=reset_action_completed, key="staging_server_id", value=st.session_state.get("staging_server_id", ""), autocomplete="on")
    staging_app_id = st.text_input("Staging App ID", on_change=reset_action_completed, key="staging_app_id", value=st.session_state.get("staging_app_id", ""), autocomplete="on")

# Form submission
if not st.session_state["action_completed"]:
    if st.session_state["webhook_action"] == "delete":
        button_label = "Delete the Webhook"
    else:
        button_label = f"{'Update the' if st.session_state['webhook_action'] == 'update' else 'Create a'} {type if type else ''} Webhook"
    if st.button(button_label):
        # Validate email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, st.session_state["email"]):
            st.error("Invalid email address.")
        elif not server_id:
            st.error("Server ID is required.")
        elif not app_id:
            st.error("App ID is required.")
        elif not type:
            st.error("Type is required.")
        elif type == "Deploy" and (not deploy_path or not branch_name):
            st.error("Deploy Path and Branch Name are required for Deploy type.")
        elif type in ["Copy to Live", "Copy to Staging"] and (not staging_server_id or not staging_app_id):
            st.error("Staging Server ID and Staging App ID are required for Copy to Live or Copy to Staging type.")
        else:
            # Payload
            payload = {
            "server_id": st.session_state["server_id"],
            "app_id": st.session_state["app_id"],
            "secret_key": os.environ.get("SECRET_KEY", secret_key),
            }
            if type == "Deploy":
                payload["deploy_path"] = st.session_state["deploy_path"]
                payload["branch_name"] = st.session_state["branch_name"]
                payload["backup"] = st.session_state["backup"]
            elif type == "Copy to Live" or type == "Copy to Staging":
                payload["staging_server_id"] = st.session_state["staging_server_id"]
                payload["staging_app_id"] = st.session_state["staging_app_id"]
                payload["backup"] = st.session_state["backup"]

            # Post request to the API
            if st.session_state["api_method"] == "POST":
                response = requests.post(st.session_state["api_endpoint"], json=payload)
            elif st.session_state["api_method"] == "PUT":
                response = requests.put(st.session_state["api_endpoint"], json=payload)
            elif st.session_state["api_method"] == "DELETE":
                response = requests.delete(st.session_state["api_endpoint"], json=payload)
            else:
                st.error("Invalid action type.")

            # Handle response
            if response.status_code == 200:
                new_webhook = response.json()
                webhook_url = f"{webhook_url}/{new_webhook['webhookId']}"
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
                        <div id="buttonContainer"><button onclick="copyToClipboard()" id="copyBtn">Copy Webhook URL</button></div>
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
            else:
                st.error(f"Failed to submit deployment request: {response.text}", icon="❌")
else:
    st.warning("Webhook already created.", icon="⚠️")
            