from flask import Flask, request
import requests

TOKEN = "8563508602:AAE8u7e1u9FvWxMb7nldj_pEi_ddSG7TJks"
ADMIN_CHAT_ID = "-5175915462"  # Your Telegram group ID

app = Flask(__name__)

def send_message(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": chat_id, "text": text})

@app.route('/bot', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if "message" in data and "text" in data["message"]:
        user_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        # Forward message to your group
        send_message(ADMIN_CHAT_ID, f"User {user_id}: {text}")
        
    # Detect replies in your group to send back to user
    if "message" in data and "reply_to_message" in data["message"]:
        reply_text = data["message"]["text"]
        reply_to_text = data["message"]["reply_to_message"]["text"]
        user_id = reply_to_text.split(":")[0].replace("User ", "")
        send_message(user_id, reply_text)
    
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
