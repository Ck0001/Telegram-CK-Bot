from flask import Flask, request
import requests
import json
import os

TOKEN = "8563508602:AAE8u7e1u9FvWxMb7nldj_pEi_ddSG7TJks"
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

    if "message" in data and "text" in data["message"]:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message["text"]

        # Ignore messages from the admin group to avoid loops
        if str(chat_id) != str(ADMIN_CHAT_ID):
            # Get user's display name
            first_name = message["chat"].get("first_name", "")
            last_name = message["chat"].get("last_name", "")
            username = message["chat"].get("username", "")

            display_name = f"{first_name} {last_name}".strip()
            if username:
                display_name += f" | @{username}"

            forward_text = f"User:{display_name}\n{text}"
            res = send_message(ADMIN_CHAT_ID, forward_text)

            # Save mapping to track replies
            if res and res.get("ok"):
                group_msg_id = res["result"].get("message_id")
                if group_msg_id:
                    forwarded_map[str(group_msg_id)] = chat_id
                    save_map()
                    print(f"[webhook] Saved mapping: {group_msg_id} -> {chat_id}")

    # Handle replies from admin group
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"]["text"]
        reply_to = data["message"]["reply_to_message"]["text"]

        if reply_to.startswith("User:"):
            user_id = forwarded_map.get(str(data["message"]["reply_to_message"]["message_id"]))
            if user_id:
                send_message(user_id, reply_text)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
