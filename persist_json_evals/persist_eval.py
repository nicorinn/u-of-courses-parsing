import json
from operator import itemgetter
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")
api_port = config.get('API_PORT', 8001)
top_word_count = 15


def persist_eval(filename):
    with open(filename) as json_eval:
        course_eval = json.load(json_eval)
        print(course_eval['title'])
        get_top_words(course_eval)
        print("")


def get_top_words(course_eval):
    top_words = []
    word_count = sum(list(course_eval['words'].values()))
    for word, count in course_eval['words'].items():
        weight = get_tf_idf_score(word, count, word_count)
        top_words.append((word, weight))
    top_words.sort(key=itemgetter(1))
    if len(top_words) >= top_word_count:
        top_words = top_words[:top_word_count]
    return top_words


def get_idf_score(term):
    url = f'http://localhost:{api_port}/api/words/{term}'
    count = requests.get(url)
    count.raise_for_status()
    return float(count.content)


def get_tf_idf_score(term, term_freq, word_count):
    idf = get_idf_score(term)
    tf = float(term_freq)/word_count
    return tf * idf
