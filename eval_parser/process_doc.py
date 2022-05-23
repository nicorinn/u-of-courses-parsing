from email import header
import json
import os
from bs4 import BeautifulSoup
import process_images as process_images
from dotenv import dotenv_values
from process_comments import process_comments
import requests
from process_comments import process_comments

config = dotenv_values('.env')
api_key = config.get('API_KEY')
server_url = config.get('SERVER_URL')


def process_eval(filename):
    with open(filename) as course_eval:
        soup = BeautifulSoup(course_eval, 'html.parser')
        data_dict = {}
        data_dict['chart_data'] = {}

        extract_primary_info(data_dict, soup)
        process_comments(data_dict, soup)
        process_report_blocks(data_dict, soup)
        extract_respondent_info(data_dict, soup)
        # Send eval to backend
        parsed_eval = get_camel_case_eval(data_dict)
        send_eval_to_server(parsed_eval)


def extract_primary_info(data_dict, soup):
    title = soup.h2.get_text()
    print(title)
    split_title = title.split(' - ')
    extract_num_and_section(data_dict, split_title[0])
    data_dict['title'] = split_title[1]
    # This must come after title, since some evals have quarter info in the title
    extract_quarter(data_dict, soup)
    extract_instructors(data_dict, split_title[2])


def extract_respondent_info(data_dict, soup):
    respondents_block = soup.find('div', class_='audience-data')
    respondent_data = respondents_block.find_all('dd')
    data_dict['enrolled'] = int(respondent_data[0].get_text())
    data_dict['respondents'] = int(respondent_data[1].get_text())


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


def process_report_blocks(data_dict, soup):
    report_blocks = soup.find_all('div', class_='report-block')
    for block in report_blocks:
        extract_hours_worked(data_dict, block)
        extract_tabular_data(data_dict, block)


def extract_hours_worked(data_dict, block):
    hours = -1
    if 'hours per week' in block.get_text():
        hours = extract_hours_from_block(block)

    data_dict['hours'] = hours


def extract_tabular_data(data_dict, block):
    if 'The Instructor' in block.get_text():
        for row in block.find_all('tr'):
            th = row.th
            if th and 'helpful outside of class' in th.get_text():
                data_dict['chart_data']['helpful_outside_class'] = row.td.get_text()
    if block.table:
        for row in block.find_all('tr'):
            if not row.th:
                return
            if 'evaluated fairly' in row.th.get_text():
                data_dict['chart_data']['evaluated_fairly'] = row.td.get_text()
            if 'feedback on my performance' in row.th.get_text():
                data_dict['chart_data']['feedback'] = row.td.get_text()
            if 'standards for success' in row.th.get_text():
                data_dict['chart_data']['standards_for_success'] = row.td.get_text()


def extract_hours_from_block(block):
    image = block.find('img')
    table = block.find('table')
    is_additional_hours_table = 'additional hours' in block.get_text()
    # Contains three images and three tables, but only the third
    # report concerns homework and reading workload
    if image and table and not is_additional_hours_table:
        return -1
    elif image and table and is_additional_hours_table:
        return table.tbody.find_all('tr')[1].td.get_text()
    # Contains table only. Ex. HUMA 14000 5 - Autumn 2016
    elif table:
        return table.tbody.find_all('td')[1].get_text()
    # Contains image only. Ex. CMSC 16100 - Autumn 2021
    elif image:
        hours = process_images.get_hours_worked(image['src'])
        return hours
    return -1


def save_json(data_dict):
    filename = f"{data_dict['dept_and_num'][0]}_{data_dict['sections'][0]}_"
    filename += f"{data_dict['quarter']}_{data_dict['year']}"
    filename = f'./json_evals/{filename}.json'

    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as fp:
        json.dump(data_dict, fp, sort_keys=True, indent=4)


def get_camel_case_eval(data_dict):
    return {
        'apiKey': api_key,
        'section': {
            # TODO add more section numbers
            'number': data_dict['sections'][0],
            'year': data_dict['year'],
            'quarter': data_dict['quarter'],
            'chartData': data_dict['chart_data'],
            'sentiment': data_dict['sentiment'],
            'hoursWorked': data_dict['hours'],
            'isVirtual': False,
            'enrolledCount': data_dict['enrolled'],
            'respondentCount': data_dict['respondents'],
            'title': data_dict['title'],
            'courseNumbers': data_dict['dept_and_num'],
            'instructors': data_dict['instructors']
        }
    }


def send_eval_to_server(course_eval):
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
    res = requests.post(server_url, headers=headers,
                        json=course_eval, verify=False)
    res.raise_for_status()
