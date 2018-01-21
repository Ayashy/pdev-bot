from flask import Flask, request
from datetime import datetime
import json
import requests
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# This needs to be filled with the Page Access Token that will be provided
# by the Facebook App that will be created.
PAT = 'EAAFsLeSZBJPsBALDhojTSclmiTQDmZBu6XRqBcUk5xQFZBEeEHAtvv3sWWr8m17yfjujBD25Gs4ZCfR32clsi5s7jueovN3ZBl5ZAZBTFsAMCzpuZAqqazj4vGPKFMeFh8lg02ugNVFc8iVt70LX6GXVnkLctpj1MnSF2VNth0F5YwZDZD'

# Verification handler
@app.route('/', methods=['GET'])
def handle_verification():
    """This method sends the verification token
    The token must match the one specified to in the facebook page
    """
    print("Handling Verification.") 
    if request.args.get('hub.verify_token', '') == 'my_voice_is_my_password_verify_me':
        print("Verification successful!")
        return request.args.get('hub.challenge', '')
    else:
        print("Verification failed!")
        return 'Error, wrong validation token'

#Message handler
@app.route('/', methods=['POST'])
def handle_messages():
    print("Handling Messages")
    payload = request.get_data()
    print(payload)
    for sender, message in messaging_events(payload):
        print("Incoming from %s: %s" % (sender, message))
        auto_send_message(PAT, sender, message)
    return "ok"

#Generate the message list
def messaging_events(payload):
    """Generate tuples of (sender_id, message_text) from the
    provided payload.
    """
    data = json.loads(payload)
    messaging_events = data["entry"][0]["messaging"]
    for event in messaging_events:
        if "message" in event and "text" in event["message"]:
            yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
        else:
            yield event["sender"]["id"], "I can't echo this"

#Respond to message
def send_message(token, recipient, text):
    """Send the message text to recipient with id recipient.
    """
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=json.dumps({
            "recipient": {"id": recipient},
            "message": {"text": text.decode('unicode_escape')}
        }),
        headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print(r.text)

if __name__ == '__main__':
    app.run()

#Method to schedual responses
def auto_send_message(token, recipient, text):
    scheduler = BackgroundScheduler()
    scheduler.add_job( lambda: send_message(token, recipient, text), 'interval', seconds=2)
    scheduler.start()
    iters=4
    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while iters!=0:
            time.sleep(2)
            iters-=1
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()