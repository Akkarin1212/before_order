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
import beforeorder

ACCESS_TOKEN = 'EAARtu5AvLUMBAIMs1tKSkm2DY1JlEAiq0vYeXxdfToBCcuIIVgm1pRgk6zOxI7lBEwO4tK8wvvWor4JtAmpFik6dGPsj4KiYDR92KbsMUsMv1u7VfTnsJ2Nw1GGFUD399nNHTW6BK9InfxFuQz6FTHBvs51S4IGVG2B4SdnRWJlmoMEH4MJ8o70mIiIZD'
VERIFY_TOKEN = 'EAARtu5AvLUMBAIMs1tKSkm2DY1JlEAiq0vYeXxd'

def process_message(message):
    app.logger.debug('Message received: {}'.format(message))

    if 'attachments' in message['message']:
        if message['message']['attachments'][0]['type'] == 'image':
            app.logger.debug('Image received')

            dishes = beforeorder.get_response_image(message["message"]["attachments"][0]["payload"]["url"])
            replies = []
            for dish in dishes:
                replies.append(quick_replies.QuickReply(title=dish["ko_name"]+"("+dish["name"]+")", payload=dish["ko_name"]))

            qrs = quick_replies.QuickReplies(quick_replies=replies)
            response = Text(text='Choose a dish for more informations.', quick_replies=qrs)
            return response.to_dict()

    if 'quick_reply' in message['message']:
        msg = message['message']['text'].lower()        
        response = Text(text=beforeorder.get_response(message['message']["quick_reply"]["payload"]))
        return response.to_dict()

    elif 'text' in message['message']:
        msg = message['message']['text'].lower()        
        response = Text(text=beforeorder.get_response(message['message'].get('text')))
        return response.to_dict()


class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        action = process_message(message)
        res = self.send(action, 'RESPONSE')
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
    app.run()