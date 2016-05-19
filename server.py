from flask import Flask, request
import json
from smooch import Smooch
import os
import adventure.loader as advent

s_api = Smooch(os.getenv("SMOOCH_KEY_ID"), os.getenv("SMOOCH_SECRET"))

app = Flask(__name__)

@app.route('/hooks',methods=['POST'])
def process_mesage():
    """Listens at /hooks for posts to that url."""
    data = json.loads(request.data)
    user_response = data["messages"]["text"]
    user_id = data["appUser"]["userId"]
    if advent.user_exists(user_id):
        response = advent.respond(user_id, user_response)
    else:
        response = advent.new_game(user_id)

    s_api.post_message(iser_id, response, True)
    advent.db_save()
    return "OK"

if __name__ == '__main__':
    webhook_id, webhook_secret = api.ensure_webhook_exists("message:appUser", "advent-term-120.herokuapp.com/hooks")
    app.run()
