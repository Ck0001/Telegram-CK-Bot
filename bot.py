from flask import Flask, request
import requests

TOKEN = "8563508602:AAE8u7e1u9FvWxMb7nldj_pEi_ddSG7TJks"
ADMIN_CHAT_ID = "-5175915462"

app = Flask(__name__)
forwarded_map = {}

def send_message(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": chat_id, "text": text})

@app.route('/bot', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Incoming update:", data)
    
    # Forward user messages
    if "message" in data and "text" in data["message"] and data["message"]["chat"]["id"] != int(ADMIN_CHAT_ID):
        user_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                            data={"chat_id": ADMIN_CHAT_ID, "text": text}).json()
        group_msg_id = res.get("result", {}).get("message_id")
        if group_msg_id:
            forwarded_map[group_msg_id] = user_id

    # Handle replies from admin group
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"]["text"]
        group_reply_id = data["message"]["reply_to_message"]["message_id"]
        user_id = forwarded_map.get(group_reply_id)
        if user_id:
            send_message(user_id, reply_text)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
