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
import requests

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
GOOGLE_KEY = os.environ['GOOGLE_KEY']
GOOGLE_ENGINE = os.environ['GOOGLE_ENGINE']
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
            # read the payload and create a list of new quick replies without the dish we are currently getting informations for
            payload = message['message']["quick_reply"]["payload"]
            dishes = json.loads(payload) # payload consists of a list of dishes in json format
            dishes = filter_ko_dish_from_list(dishes, message['message'].get('text'))
            qrs = dishes_to_quick_reply(dishes)

            # look up the informations for this dish
            cur_dish = match.group(0)
            dish_info = analyzer.get_response(cur_dish)
            # if we have informations for the dish, send a picture first and then the dish description
            if dish_info:
                send_addition_image_for_dish(cur_dish)
                response = analyzer.dish_info_to_string(dish_info)
                return Text(text=response, quick_replies=qrs)

            return Text(text="I can't seem to find information for a dish with that name.", quick_replies=qrs)

    elif 'text' in message['message']:
        match = analyzer.hangul_pattern.search(message['message'].get('text'))
        if match:
            dish_info = analyzer.get_response(match.group(0))
            if dish_info:
                send_addition_image_for_dish(match.group(0))
                response = analyzer.dish_info_to_string(dish_info)
                return Text(text=response)
            return Text(text="I can't seem to find information for a dish with that name.")
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

# Creates a json list of dishes with the korean name followed by the english name in brackets
def dishes_to_payload(dishes):
    payload = []
    for dish in dishes:
        # dish is a dictionary when we get the informations from the database
        if type(dish) is dict:
            payload.append(dish["ko_name"]+"("+dish["name"]+")")
        # and a string when we get it from the payload of a facebook quick reply
        else:
            payload.append(dish)
    return json.dumps(payload)

# Creates a QuickReply object for every dish in dishes
# The name of a QuickReply consist of the Korean and English name of a dish
# and its payload consists of a list of all other dishes in json format
def dishes_to_quick_reply(dishes):
    replies = []
    payload = dishes_to_payload(dishes)
    for dish in dishes:
        # dish is a dictionary when we get the informations from the database
        if type(dish) is dict:
            replies.append(quick_replies.QuickReply(title=dish["ko_name"]+"("+dish["name"]+")", payload=payload))
        # and a string when we get it from the payload of a facebook quick reply
        else:
            replies.append(quick_replies.QuickReply(title=dish, payload=payload))

    return quick_replies.QuickReplies(quick_replies=replies)

# Iterates over the dishes list and filters out every occurence of dish_to_filter
# using the hangul pattern matcher of analyzer modul (only the korean letters in both strings are compared!)
def filter_ko_dish_from_list(dishes, dish_to_filter):
    result = []
    for dish in dishes:
        match = analyzer.hangul_pattern.search(dish)
        filter_match = analyzer.hangul_pattern.search(dish)
        # skip this dish if both have the same korean name
        if match.group(0) == filter_match.group(0):
            continue
        result.append(dish)
    return result

        
        

def get_google_image_url(dish):
    startIndex = '1'
    searchUrl = "https://www.googleapis.com/customsearch/v1?q=" + \
        dish + "&start=" + startIndex + "&key=" + GOOGLE_KEY + "&cx=" + GOOGLE_ENGINE + \
        "&searchType=image"
    r = requests.get(searchUrl)
    response = r.content.decode('utf-8')
    result = json.loads(response)
    for image in result["items"]:
        # make sure the file is actually supported (jpeg)
        if image["mime"] == "image/jpeg":
            return image["link"]

def send_addition_image_for_dish(dish):
    url = get_google_image_url(dish)
    response = Image(url=url)
    messenger.send(response.to_dict(), "RESPONSE")

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
        if 'example' in payload:
            txt = ('If you text to me 김밥 or send a picture for menu name 김밥, I will send you a description like this: '
                + analyzer.get_response("김밥"))
            self.send({'text': txt}, 'RESPONSE')

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

        menu_item_3 = PersistentMenuItem(
            item_type='postback',
            title='Example',
            payload='example',
        )
     
        
        # menu_item_4 = PersistentMenuItem(
        #     item_type='web_url',
        #     title='Messenger Docs',
        #     url='https://developers.facebook.com/docs/messenger-platform',
        # )

        persistent_menu = PersistentMenu(menu_items=[
            menu_item_1,
            menu_item_2,
            menu_item_3
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