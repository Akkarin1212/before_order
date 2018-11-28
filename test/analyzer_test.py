import requests
import json
import regex as re
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import os
import urllib.request


# Hangul matcher
hangul_pattern = re.compile(r'([\p{Hangul}]+)', re.UNICODE)

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

    for line in line_infos:
        for word_metadata in line:
            for word_info in word_metadata["words"]:
                match = hangul_pattern.search(word_info["text"])
                if match:
                    word_infos.append(match.group(0))
    
    word_infos = list(set(word_infos))
    print(word_infos)
    
    return word_infos


analyze_pic("http://mstyle-food.co.kr/data/file/menu/3717576197_mDUVpKaF_6263df6a81760c4c4aef2f5fa90286bb8e6c81b5.jpg")
