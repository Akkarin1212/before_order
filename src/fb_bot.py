from flask import Flask, request
from pymessenger.bot import Bot
import beforeorder

app = Flask(__name__)
ACCESS_TOKEN = 'EAARtu5AvLUMBAIMs1tKSkm2DY1JlEAiq0vYeXxdfToBCcuIIVgm1pRgk6zOxI7lBEwO4tK8wvvWor4JtAmpFik6dGPsj4KiYDR92KbsMUsMv1u7VfTnsJ2Nw1GGFUD399nNHTW6BK9InfxFuQz6FTHBvs51S4IGVG2B4SdnRWJlmoMEH4MJ8o70mIiIZD'
VERIFY_TOKEN = 'EAARtu5AvLUMBAIMs1tKSkm2DY1JlEAiq0vYeXxd'
bot = Bot(ACCESS_TOKEN)

#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                    response_sent_text = beforeorder.get_response(message['message'].get('text'))
                    send_message(recipient_id, response_sent_text)
                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    response_sent_nontext = beforeorder.get_response_image(message["message"]["attachments"][0]["payload"]["url"])
                    send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

if __name__ == "__main__":
    app.run()