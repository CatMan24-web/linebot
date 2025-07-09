from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


@app.route("/")
def home():
    return "<h1>Welcome to the LINE Bot Server!</h1>"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@app.route("/esp32", methods=['POST'])
def esp32():
    group_id = os.getenv('GROUP_ID')
    data = request.get_json()
    message_text = data.get('message', 'Current Route: /ESP32!')

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        try:
            # Send a push message to the target group
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=group_id,
                    messages=[TextMessage(text=message_text)]
                )
            )
        except Exception as e:
            app.logger.error(f"An error occurred: {e}")
            return 'Failed to send message.', 500

    return 'OK'


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    global TARGET_GROUP_ID
    
    # check if the event is from a group
    if event.source.type == 'group':
        
        # check if the message is the bind command
        if event.message.text == '!bind':

            # get group_id from the event and save it
            TARGET_GROUP_ID = event.source.group_id
            print(f"Group ID captured: {TARGET_GROUP_ID}")
            app.logger.info(f"Group ID captured: {TARGET_GROUP_ID}")

            # reply with a message to inform the user that the binding was successful
            reply_text = f"✅ Successfully retrieved the group ID: {TARGET_GROUP_ID}!"
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
            return


if __name__ == "__main__":
    app.run()