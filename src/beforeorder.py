import requests
import json
import regex as re
import test_json
from hangul_romanize import Transliter
from hangul_romanize.rule import academic

# before_order files
import db

# calls the REST API of the azure ocr text recognition service with the image_url as picture to analyze
# filters the text recognition result and only returns words in korean alphabet
def analyze_pic(image_url):
    assert image_url
    subscription_key = "d4dab977c06043a7b30045c22bd4dbf6"
    vision_base_url = "https://eastus.api.cognitive.microsoft.com//vision/v2.0/"
    ocr_url = vision_base_url + "ocr"

    headers = {'Ocp-Apim-Subscription-Key': subscription_key}
    params  = {'language': 'ko', 'detectOrientation': 'true'}
    data    = {'url': image_url}
    response = requests.post(ocr_url, headers=headers, params=params, json=data)
    response.raise_for_status()

    analysis = response.json()
    return filter_analyze_result(analysis)

def filter_analyze_result(analysis):
    # Extract the word bounding boxes and text.
    line_infos = [region["lines"] for region in analysis["regions"]]
    word_infos = []
    # Only return strings in Hangul
    pattern = re.compile(r'([\p{Hangul}]+)', re.UNICODE)

    for line in line_infos:
        for word_metadata in line:
            for word_info in word_metadata["words"]:
                match = pattern.search(word_info["text"])
                if match:
                    word_infos.append(match.group(0))
    return word_infos

def get_response(message):
    mydb = db.connect_db()
    dish = db.get_dishes(mydb, message)
    if dish:
        return str(dish[0]['name'] + " (" + hangul_romanize(dish[0]['ko_name']) + ") - " + dish[0]["description"])
    else:
        return "No information available"

def get_response_image(url):
    #analyze_result = analyze_pic(url)
    
    test_data = test_json.test()
    analyze_result = filter_analyze_result(test_data)

    mydb = db.connect_db()
    return db.get_dishes(mydb, analyze_result)
    

# romanizes hangul strings using hangul_romanize library
def hangul_romanize(text):
        transliter = Transliter(academic)
        return transliter.translit(text)



#analyze_result = analyze_pic("https://b.zmtcdn.com/data/menus/802/16726802/868b8b4241002eb389dfaa18d8243c71.jpg")

#mydb = db.connect_db()
#available_dishes = db.get_dishes(mydb, analyze_result)