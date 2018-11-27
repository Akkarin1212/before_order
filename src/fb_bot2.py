from flask import Flask, request
from fbmessenger import BaseMessenger
from fbmessenger.templates import GenericTemplate
from fbmessenger.elements import Text, Button, Element
from fbmessenger import quick_replies
from fbmessenger.attachments import Image, Video
from fbmessenger.thread_settings import (
    GreetingText,
    GetStartedButton,
    PersistentMenuItem,
    PersistentMenu,
    MessengerProfile,
)
from fbmessenger.sender_actions import SenderAction
import beforeorder
import regex as re
import json
import os

ACCESS_TOKEN = 'EAARtu5AvLUMBAIMs1tKSkm2DY1JlEAiq0vYeXxdfToBCcuIIVgm1pRgk6zOxI7lBEwO4tK8wvvWor4JtAmpFik6dGPsj4KiYDR92KbsMUsMv1u7VfTnsJ2Nw1GGFUD399nNHTW6BK9InfxFuQz6FTHBvs51S4IGVG2B4SdnRWJlmoMEH4MJ8o70mIiIZD'
VERIFY_TOKEN = 'EAARtu5AvLUMBAIMs1tKSkm2DY1JlEAiq0vYeXxd'
HELP = 'Simply sent me a dish name in Hangul or the image of a menu that you want to translate.'

def process_message(message):
    app.logger.debug('Message received: {}'.format(message))

    if 'sticker_id' in message['message']:        
        response = Text(text="What do you want me to do?")
        return response.to_dict()

    elif 'attachments' in message['message']:
        return process_image(message)

    elif 'quick_reply' in message['message']:
        match = beforeorder.hangul_pattern.search(message['message'].get('text'))
        if match:
            msg = message['message']["quick_reply"]["payload"]
            dishes = json.loads(msg)
            qrs = dishes_to_quick_reply(dishes, message['message'].get('text'))
            response = Text(text=beforeorder.get_response(match.group(0)), quick_replies=qrs)
            return response.to_dict()

    elif 'text' in message['message']:
        match = beforeorder.hangul_pattern.search(message['message'].get('text'))
        if match:        
            response = Text(text=beforeorder.get_response(match.group(0)))
            return response.to_dict()
        else:
            response = Text(text="I can only look up dishes written in Hangul. Please try again.")
            return response.to_dict()
    
    response = Text(text=HELP)
    return response.to_dict()

def process_image(message):
    if message['message']['attachments'][0]['type'] == 'image':
        if '.gif' in message['message']['attachments'][0]["payload"]["url"]:
            response = Text(text="Sadly i can't analyze gif files. Lets try it again with a standart image format.")
            return response.to_dict()

        app.logger.debug('Image received')
        messenger.send(Text("Analyzing the image...").to_dict(), 'RESPONSE')
        messenger.send_action(SenderAction(sender_action='typing_on').to_dict())

        dishes = beforeorder.get_response_image(message["message"]["attachments"][0]["payload"]["url"])
        qrs = dishes_to_quick_reply(dishes)
        response = Text(text='Choose a dish for more informations.', quick_replies=qrs)
        return response.to_dict()

def dishes_to_payload(dishes, current_dish = ''):
    payload = []
    for dish in dishes:
        # skip the dish that we are got informations for just now
        if current_dish and dish == current_dish:
            continue

        if type(dish) is dict:
            payload.append(dish["ko_name"]+"("+dish["name"]+")")
        else:
            payload.append(dish)
    return json.dumps(payload)

def dishes_to_quick_reply(dishes, current_dish = ''):
    replies = []
    payload = dishes_to_payload(dishes, current_dish)
    for dish in dishes:
        # skip the dish that we are got informations for just now
        if current_dish and dish == current_dish:
            continue

        if type(dish) is dict:
            replies.append(quick_replies.QuickReply(title=dish["ko_name"]+"("+dish["name"]+")", payload=payload))
        else:
            replies.append(quick_replies.QuickReply(title=dish, payload=payload))

    return quick_replies.QuickReplies(quick_replies=replies)

class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        messenger.send_action(SenderAction(sender_action='mark_seen').to_dict())
        messenger.send_action(SenderAction(sender_action='typing_on').to_dict())

        #self.send(Text(text="bug fixer").to_dict(), 'RESPONSE')

        action = process_message(message)
        res = self.send(action, 'RESPONSE')
        messenger.send_action(SenderAction(sender_action='typing_off').to_dict())
        app.logger.debug('Response: {}'.format(res))

    def delivery(self, message):
        pass

    def read(self, message):
        pass

    def account_linking(self, message):
        pass

    def postback(self, message):
        payload = message['postback']['payload']
        if 'start' in payload:
            txt = ('Hey, let\'s get started! Try sending me one of these messages: '
                   'text, image, video, "quick replies", '
                   'webview-compact, webview-tall, webview-full')
            self.send({'text': txt}, 'RESPONSE')
        if 'help' in payload:
            self.send({'text': 'A help message or template can go here.'}, 'RESPONSE')

    def optin(self, message):
        pass

    def init_bot(self):
        self.add_whitelisted_domains('https://facebook.com/')
        greeting = GreetingText(text='Welcome to the fbmessenger bot demo.')
        self.set_messenger_profile(greeting.to_dict())

        get_started = GetStartedButton(payload='start')
        self.set_messenger_profile(get_started.to_dict())

        menu_item_1 = PersistentMenuItem(
            item_type='postback',
            title='Help',
            payload='help',
        )
        menu_item_2 = PersistentMenuItem(
            item_type='web_url',
            title='Messenger Docs',
            url='https://developers.facebook.com/docs/messenger-platform',
        )
        persistent_menu = PersistentMenu(menu_items=[
            menu_item_1,
            menu_item_2
        ])

        res = self.set_messenger_profile(persistent_menu.to_dict())
        app.logger.debug('Response: {}'.format(res))


app = Flask(__name__)
app.debug = True
messenger = Messenger(ACCESS_TOKEN)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            if request.args.get('init') and request.args.get('init') == 'true':
                messenger.init_bot()
                return ''
            return request.args.get('hub.challenge')
        raise ValueError('FB_VERIFY_TOKEN does not match.')
    elif request.method == 'POST':
        messenger.handle(request.get_json(force=True))
    return ''

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)