from bs4 import BeautifulSoup
import json
import re
from flair.models import TextClassifier
from flair.models import SequenceTagger
from flair.data import Sentence


def process_eval(filename):
    with open(filename) as course_eval:
        soup = BeautifulSoup(course_eval, 'html.parser')
        data_dict = {}

        extract_primary_info(data_dict, soup)
        process_comments(data_dict, soup)

        json_string = json.dumps(data_dict)
        print(json_string)


def extract_primary_info(data_dict, soup):
    title = soup.h2.get_text()
    split_title = title.split(' - ')
    extract_num_and_section(data_dict, split_title[0])
    data_dict['title'] = split_title[1]
    extract_instructors(data_dict, split_title[2])


def extract_num_and_section(data_dict, text):
    course_nums = text.split(',')
    data_dict['sections'] = []
    data_dict['dept_and_num'] = []

    for course in course_nums:
        course = course.strip()
        split_course = course.split(' ')
        # Get first and second words
        dept_and_num = split_course[0] + ' ' + split_course[1]
        data_dict['dept_and_num'].append(dept_and_num)
        data_dict['sections'].append(split_course[2])


def extract_instructors(data_dict, text):
    text = text.strip()
    text = text.removeprefix('Instructor(s)')
    # Not always present
    text = text.removeprefix(':')
    text = text.strip()
    instructors = text.split(',')
    for instructor in instructors:
        instructor.strip()
    data_dict['instructors'] = instructors


def process_comments(data_dict, soup):
    comments = []
    classifier = TextClassifier.load('en-sentiment')
    total_score = 0

    for table in soup.find_all('table'):
        if table.thead.tr.th.get_text() == 'Comments':
            for row in table.tbody.find_all('tr'):
                comment = row.td.get_text()
                comments.append(comment)
                total_score += get_sentiment_score(comment, classifier)
    data_dict['sentiment'] = total_score / len(comments)


def get_sentiment_score(comment, classifier):
    sentence = Sentence(comment)
    classifier.predict(sentence)
    score = sentence.labels[0].score
    if sentence.labels[0].value == 'NEGATIVE':
        score = score * -1
    return score


def save_word(word):
    print(word)
