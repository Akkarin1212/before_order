import json
import regex as re
import db
#import analyzer

def test():
    f = open('test.txt')
    analysis = json.load(f)
    return analysis

# word_infos = analyzer.filter_analyze_result(analysis)

# print("Found words: " + str(word_infos))

# mysql = db.connect_db()
# dishes = db.get_dishes(mysql, word_infos)
# print("Available dishes: " + str(dishes))
#print("Romanization: " + str(analyzer.hangul_romanize([d['ko_name'] for d in dishes if 'ko_name' in d])))