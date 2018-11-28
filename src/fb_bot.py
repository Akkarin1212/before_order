from flask import Flask, request
from fbmessenger import BaseMessenger
from fbmessenger.templates import GenericTemplate
from fbmessenger.elements import Text, Button, Element
from fbmessenger import quick_replies
from fbmessenger.attachments import Image
from fbmessenger.thread_settings import (
    GreetingText,
    GetStartedButton,
    PersistentMenuItem,
    PersistentMenu,
    MessengerProfile,
)
from fbmessenger.sender_actions import SenderAction
import analyzer
import regex as re
import json
import os

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
HELP = 'To get started sent me a dish name written in Hangul or the image of a Korean menu that you would like to translate.'

def process_message(message):
    app.logger.debug('Message received: {}'.format(message))

    if 'sticker_id' in message['message']:        
        return Text(text="What do you want me to do?")

    elif 'attachments' in message['message']:
        return process_image(message)

    elif 'quick_reply' in message['message']:
        match = analyzer.hangul_pattern.search(message['message'].get('text'))
        if match:
            msg = message['message']["quick_reply"]["payload"]
            dishes = json.loads(msg)
            qrs = dishes_to_quick_reply(dishes, message['message'].get('text'))
            return Text(text=analyzer.get_response(match.group(0)), quick_replies=qrs)

    elif 'text' in message['message']:
        match = analyzer.hangul_pattern.search(message['message'].get('text'))
        if match:        
            return Text(text=analyzer.get_response(match.group(0)))
        else:
            return Text(text="I can only look up dishes written in Hangul. Please try again.")
    
    return Text(text=HELP)

def process_image(message):
    if message['message']['attachments'][0]['type'] == 'image':
        url = message['message']['attachments'][0]["payload"]["url"]
        if '.gif' in url:
            return Text(text="Sadly i can't analyze gif files. Lets try it again with a standart image format.")

        #let the user know we're analyzing the image
        app.logger.debug('Image received')
        messenger.send(Text("Analyzing the image...").to_dict(), 'RESPONSE')
        messenger.send_action(SenderAction(sender_action='typing_on').to_dict())

        # first check the image size and type
        error = analyzer.check_image_info(url)
        if error:
            return Text(text=error) 

        # then let the analyzer do its job and get a list of dishes that are visible in the image
        dishes = analyzer.get_response_image(url)
        qrs = dishes_to_quick_reply(dishes)
        if not qrs:
            return Text(text='I didn\'t find any dishes. Try again with a different angle or try writting the dish in Hangul.') 
        return Text(text='Choose a dish for more informations.', quick_replies=qrs)

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

        action = process_message(message)
        res = self.send(action.to_dict(), 'RESPONSE')
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
            txt = ('Hey, let\'s get started! Try sending me either an image of a Korean menu '
                    'or simply send me the name of a Korean dish written in Hangul.')
            self.send({'text': txt}, 'RESPONSE')
        if 'help' in payload:
            self.send({'text': HELP}, 'RESPONSE')

    def optin(self, message):
        pass

    def init_bot(self):
        self.add_whitelisted_domains('https://facebook.com/')

        #get started button
        get_started = GetStartedButton(payload='start')
        messenger_profile = MessengerProfile(get_started=get_started)
        res = self.set_messenger_profile(messenger_profile.to_dict())
        app.logger.debug('Response: {}'.format(res))

        #persistent menu entries

        menu_item_1 = PersistentMenuItem(
            item_type='postback',
            title='Get Started',
            payload='start'
        )

        menu_item_2 = PersistentMenuItem(
            item_type='postback',
            title='Help',
            payload='help',
        )
     
        
        # menu_item_3 = PersistentMenuItem(
        #     item_type='web_url',
        #     title='Messenger Docs',
        #     url='https://developers.facebook.com/docs/messenger-platform',
        # )

        persistent_menu = PersistentMenu(menu_items=[
            menu_item_1,
            menu_item_2
        ])
        
        messenger_profile = MessengerProfile(persistent_menus=[persistent_menu])
        res = self.set_messenger_profile(messenger_profile.to_dict())
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