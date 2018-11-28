import requests
import json
import regex as re
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import os
import urllib.request

# before_order files
import db

# Hangul matcher
hangul_pattern = re.compile(r'([\p{Hangul}]+)', re.UNICODE)

# calls the REST API of the azure ocr text recognition service with the image_url as picture to analyze
# filters the text recognition result and only returns words in korean alphabet
def analyze_pic(image_url):
    assert image_url
    subscription_key = os.environ['SUBSCRIPTION_KEY']
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

    for line in line_infos:
        for word_metadata in line:
            for word_info in word_metadata["words"]:
                match = hangul_pattern.search(word_info["text"])
                if match:
                    word_infos.append(match.group(0))
    
    return word_infos

def get_response(message):
    mydb = db.connect_db()
    dish = db.get_dishes(mydb, message)
    if dish:
        return str(dish[0]['name'] + " (" + hangul_romanize(dish[0]['ko_name']) + ") - " + dish[0]["description"])
    else:
        return "I can't seem to find information for a dish with that name."

def get_response_image(url):
    analyze_result = analyze_pic(url)
    mydb = db.connect_db()
    return db.get_dishes(mydb, analyze_result)

# romanizes hangul strings using hangul_romanize library
def hangul_romanize(text):
    transliter = Transliter(academic)
    return transliter.translit(text)

def check_image_info(url):
    if not url:
        return "Missing image URL, can't check the file."
    info = get_url_info(url)
    if not info :
        return "Can't fetch informations for the url: {}".format(url)

    # check that file type is supported
    if info["Content-Type"]:
        type = info["Content-Type"]
        if (not type == "image/png") and (not type == "image/jpeg") and (not type == "image/jpg"):
            return "The image format {} is not supported.".format(type)

    # check that file size is less than 4MB
    if info["Content-Length"]:
        size = int(info["Content-Length"])/float(1<<20)
        if size > 4:
            return "The image is too large to analyze ({}). Try cropping the picture and send it again.".format(size)

def get_url_info(url):
    d = urllib.request.urlopen(url)
    return d.info()
 
url = "https://b.zmtcdn.com/data/menus/802/16726802/868b8b4241002eb389dfaa18d8243c71.jpg"
error = check_image_info(url)
if error:
    print(error)