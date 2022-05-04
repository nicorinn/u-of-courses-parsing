from ast import Raise
from statistics import quantiles
import string
from bs4 import BeautifulSoup
import json
from flair.models import TextClassifier
from flair.data import Sentence
import re
import requests
import os


def process_eval(filename):
    with open(filename) as course_eval:
        soup = BeautifulSoup(course_eval, 'html.parser')
        data_dict = {}

        extract_primary_info(data_dict, soup)
        process_comments(data_dict, soup)
        # Send current section to word frequency API
        persist_eval_words(data_dict)
        # Save resulting json
        json_string = json.dumps(data_dict)
        print(json_string)


def extract_primary_info(data_dict, soup):
    title = soup.h2.get_text()
    split_title = title.split(' - ')
    extract_num_and_section(data_dict, split_title[0])
    data_dict['title'] = split_title[1]
    # This must come after title, since some evals have quarter info in the title
    extract_quarter(data_dict, soup)
    extract_instructors(data_dict, split_title[2])


def extract_num_and_section(data_dict, text):
    course_nums = text.split(',')
    data_dict['sections'] = []
    data_dict['dept_and_num'] = []
    data_dict['words'] = {}

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
    data_dict['instructors'] = []
    for instructor in instructors:
        data_dict['instructors'].append(instructor.strip())


def extract_quarter(data_dict, soup):
    project_title = soup.find(
        'dl', class_='cover-page-project-title').dd.get_text()
    split_title = project_title.split(' - ')
    qtr_and_year = split_title[1]
    # Pre-2020 evals have quarter and year in course title
    if split_title[0] == 'Data Migration':
        paren_split = data_dict['title'].split('(')
        # Remove quarter and year from course title
        data_dict['title'] = paren_split[0].strip()
        qtr_and_year = paren_split[1].removesuffix(')')
    # Split quarter and year: 'Spring 2021' -> ['Spring', '2021']
    qtr_and_year_split = qtr_and_year.split(' ')
    data_dict['quarter'] = qtr_and_year_split[0]
    data_dict['year'] = int(qtr_and_year_split[1])


def process_comments(data_dict, soup):
    comments = []
    classifier = TextClassifier.load('en-sentiment')

    total_score = 0

    for table in soup.find_all('table'):
        if table.thead.tr.th.get_text() == 'Comments':
            for row in table.tbody.find_all('tr'):
                comment = row.td.get_text()
                total_score += get_sentiment_score(comment, classifier)
                process_comment_words(data_dict, comment)
                comments.append(comment)

    data_dict['sentiment'] = total_score / len(comments)


def get_sentiment_score(comment, classifier):
    sentence = Sentence(comment)
    classifier.predict(sentence)
    score = sentence.labels[0].score
    if sentence.labels[0].value == 'NEGATIVE':
        score = score * -1
    return score


def process_comment_words(data_dict, comment):
    alpha_only_comment = re.sub('[^a-zA-Z]+', ' ', comment.lower())
    comment_words = alpha_only_comment.split()
    for word in comment_words:
        if word in data_dict['words']:
            data_dict['words'][word] += 1
        else:
            data_dict['words'][word] = 1


def persist_eval_words(data_dict):
    port = os.environ.get('API_PORT', 8001)

    section_data = {
        'department_and_number': data_dict['dept_and_num'][0],
        'year': data_dict['year'],
        'quarter': data_dict['quarter'],
        'number': data_dict['sections'][0]
    }
    # Save section and verify success
    section_res = requests.post(
        'http://localhost:' + str(port) + '/api/sections', data=json.dumps(section_data))
    section_res.raise_for_status()

    word_list = []
    for word in data_dict['words'].keys():
        # TODO remove instructor names
        word_list.append({
            "word": word,
            "count": data_dict['words'][word]})
    # Save words and verify success
    res = requests.post('http://localhost:' + str(port) +
                        '/api/words', data=json.dumps(word_list))
    res.raise_for_status()
