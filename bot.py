from flask import Flask, request
import requests
import json
import os

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_CHAT_ID = "-1003509091985"  # Make sure this is your group ID
MAP_FILE = "forwarded_map.json"

app = Flask(__name__)

# Load mapping from JSON file (persistent)
if os.path.exists(MAP_FILE):
    with open(MAP_FILE, "r") as f:
        forwarded_map = json.load(f)
else:
    forwarded_map = {}

def save_map():
    with open(MAP_FILE, "w") as f:
        json.dump(forwarded_map, f)

def send_message(chat_id, text):
    res = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": text}
    ).json()
    print(f"send_message -> chat_id: {chat_id}, text: {text}, response: {res}")
    return res

@app.route('/bot', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Incoming update:", json.dumps(data, indent=2))

    # Forward user messages
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        # Ignore messages from the admin group to avoid loops
        if str(chat_id) != str(ADMIN_CHAT_ID):
            forward_text = f"User:{chat_id}\n{text}"
            res = send_message(ADMIN_CHAT_ID, forward_text)
            
            # Save mapping if message was successfully sent
            group_msg_id = res.get("result", {}).get("message_id")
            if group_msg_id:
                forwarded_map[str(group_msg_id)] = chat_id
                save_map()

    # Handle replies from admin group
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"]["text"]
        reply_to = data["message"]["reply_to_message"]["text"]

        if reply_to.startswith("User:"):
            user_id = reply_to.split("\n")[0].replace("User:", "").strip()
            send_message(user_id, reply_text)

    return {"ok": True}

if __name__ == "__main__":
    # Listen on all interfaces for Render
    app.run(host="0.0.0.0", port=5000)
