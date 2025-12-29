from flask import Flask, request
import requests
import json
import os

# ----------------- CONFIG -----------------
TOKEN = "8563508602:AAE8u7e1u9FvWxMb7nldj_pEi_ddSG7TJks"  # Replace with your bot token
ADMIN_CHAT_ID = "-1003509091985"  # Your Telegram group ID
MAP_FILE = "forwarded_map.json"
# ------------------------------------------

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
    """Send a message and log the response."""
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": text}
        ).json()
        print(f"[send_message] chat_id: {chat_id}, text: {text}, response: {res}")
        if not res.get("ok"):
            print(f"❌ Failed to send message to {chat_id}: {res}")
        return res
    except Exception as e:
        print(f"❌ Exception while sending message to {chat_id}: {e}")
        return None

@app.route('/bot', methods=['POST'])
def webhook():
    """Receive updates from Telegram."""
    try:
        data = request.get_json()
        print("[webhook] Incoming update:", json.dumps(data, indent=2))

        if "message" not in data:
            print("⚠️ No 'message' field in update")
            return {"ok": True}

        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # ------------------ Forward user messages ------------------
        if text and str(chat_id) != str(ADMIN_CHAT_ID):
            print(f"[webhook] Forwarding message from {chat_id} to group {ADMIN_CHAT_ID}: {text}")
            forward_text = f"User:{chat_id}\n{text}"
            res = send_message(ADMIN_CHAT_ID, forward_text)

            if res and res.get("ok"):
                group_msg_id = res["result"].get("message_id")
                if group_msg_id:
                    forwarded_map[str(group_msg_id)] = chat_id
                    save_map()
                    print(f"[webhook] Saved mapping: {group_msg_id} -> {chat_id}")
            else:
                print(f"❌ Failed to forward message from {chat_id}")

        # ------------------ Handle replies from admin group ------------------
        if "reply_to_message" in message:
            reply_text = message.get("text", "")
            reply_to = message["reply_to_message"].get("text", "")

            if reply_to.startswith("User:"):
                user_id = reply_to.split("\n")[0].replace("User:", "").strip()
                print(f"[webhook] Admin replied: forwarding to user {user_id}: {reply_text}")
                send_message(user_id, reply_text)

    except Exception as e:
        print(f"❌ Exception in webhook: {e}")

    return {"ok": True}

if __name__ == "__main__":
    print(f"✅ Bot running. Listening on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
