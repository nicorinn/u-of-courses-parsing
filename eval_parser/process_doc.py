from email import header
import json
import os
from re import U
from bs4 import BeautifulSoup
import process_images as process_images
from dotenv import dotenv_values
from process_comments import process_comments
import requests
from process_comments import process_comments
from pathlib import Path

config = dotenv_values('.env')
api_key = config.get('API_KEY')
server_url = config.get('SERVER_URL')
evals_dir = config.get('EVALS_DIR')

titles_urls_filename = '../downloader/titles_urls.json'
titles_urls_path = Path(__file__).parent / titles_urls_filename


def process_eval(filename):
    with titles_urls_path.open() as titles_urls_file:
        unformatted_json_urls = json.load(titles_urls_file)
        json_urls = remove_spaces_from_page_titles(unformatted_json_urls)

        with open(filename) as course_eval:
            soup = BeautifulSoup(course_eval, 'html.parser')
            data_dict = {}
            # Exclude evaluations without a valid quarter
            if 'Late Period' in soup.h2.get_text():
                return

            save_eval_url(data_dict, soup, json_urls)
            extract_primary_info(data_dict, soup)
            process_comments(data_dict, soup)
            process_report_blocks(data_dict, soup)
            extract_respondent_info(data_dict, soup)
            # Send eval to backend
            parsed_eval = get_camel_case_eval(data_dict)
            send_eval_to_server(parsed_eval)
            print('')


def remove_spaces_from_page_titles(unformatted_json_urls):
    '''Returns an identical dictionary, but with spaces in keys removed.
    This is necessary because Selenium and BeautifulSoup have different spacing
    in page titles'''
    json_urls = {}
    for key in unformatted_json_urls:
        spaceless_key = key.replace(' ', '')
        json_urls[spaceless_key] = unformatted_json_urls[key]
    return json_urls


def save_eval_url(data_dict, soup, title_urls):
    # for some reason, page titles differ between selenium and beautifulsoup
    page_title = soup.head.title.get_text().replace(' ', '')
    if page_title in title_urls:
        data_dict['url'] = title_urls[page_title]
    else:
        data_dict['url'] = None


def extract_primary_info(data_dict, soup):
    title = soup.h2.get_text()
    print(title)
    split_title = title.split(' - ')
    extract_num_and_section(data_dict, split_title[0])
    data_dict['title'] = split_title[1]
    # in some cases, the quarter is in the title only
    if len(split_title) == 4:
        extract_four_part_quarter(data_dict, split_title[2])
    # This must come after title, since some evals have quarter info in the title
    extract_three_part_quarter(data_dict, soup)
    extract_instructors(data_dict, split_title[-1])


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


def extract_four_part_quarter(data_dict, text):
    paren_split = text.split('(')
    qtr_and_year = paren_split[1].removesuffix(')')
    # Split quarter and year: 'Spring 2021' -> ['Spring', '2021']
    qtr_and_year_split = qtr_and_year.split(' ')
    data_dict['quarter'] = qtr_and_year_split[0]
    data_dict['year'] = int(qtr_and_year_split[1])


def extract_three_part_quarter(data_dict, soup):
    project_title = soup.find(
        'dl', class_='cover-page-project-title').dd.get_text()
    split_title = project_title.split(' - ')
    qtr_and_year = split_title[1]
    # Pre-2020 evals have quarter and year in course title
    # Some formats have already been extracted in extract_primary_info()
    if 'quarter' in data_dict:
        return
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
    data_dict['hours'] = -1
    report_blocks = soup.find_all('div', class_='report-block')
    for block in report_blocks:
        extract_hours_worked(data_dict, block)
        extract_tabular_data(data_dict, block)


def extract_hours_worked(data_dict, block):
    if 'hours per week' in block.get_text():
        hours = extract_hours_from_block(block)
        # some blocks can be misleading as the comments contain "additional hours"
        # so the -1 that results from those blocks should not overwrite the current value
        data_dict['hours'] = hours if hours != -1 else data_dict['hours']


def extract_tabular_data(data_dict, block):
    if 'The Instructor' in block.get_text():
        for row in block.find_all('tr'):
            th = row.th
            if th and 'helpful outside of class' in th.get_text():
                data_dict['helpful_outside_class'] = row.td.get_text()
    if block.table:
        for row in block.find_all('tr'):
            if not row.th:
                return
            if 'evaluated fairly' in row.th.get_text():
                data_dict['evaluated_fairly'] = row.td.get_text()
            if 'feedback on my performance' in row.th.get_text():
                data_dict['feedback'] = row.td.get_text()
            if 'standards for success' in row.th.get_text():
                data_dict['standards_for_success'] = row.td.get_text()


def extract_hours_from_block(block):
    image = block.find('img')
    table = block.find('table')
    is_additional_hours_table = 'additional hours' in block.get_text()
    # Contains three images and three tables, but only the third
    # report concerns homework and reading workload
    if image and table and not is_additional_hours_table:
        return -1
    elif image and table and is_additional_hours_table:
        text = table.tbody.find_all('tr')[1].td.get_text()
        if text[0].isdigit():
            return round(float(text))
        else:
            return -1
    # Contains table only. Ex. HUMA 14000 5 - Autumn 2016
    elif table:
        text = table.tbody.find_all('td')[1].get_text()
        if text[0].isdigit():
            return round(float(text))
        else:
            return -1
    # Contains image only. Ex. CMSC 16100 - Autumn 2021
    elif image:
        hours = process_images.get_hours_worked(image['src'])
        return round(float(hours))
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
    data = {
        'apiKey': api_key,
        'section': {
            # TODO add more section numbers
            'number': data_dict['sections'][0],
            'year': data_dict['year'],
            'quarter': data_dict['quarter'],
            'keywords': data_dict['keywords'],
            'sentiment': data_dict['sentiment'],
            'isVirtual': False,
            'enrolledCount': data_dict['enrolled'],
            'respondentCount': data_dict['respondents'],
            'title': data_dict['title'],
            'commentCount': data_dict['comment_count'],
            'url': data_dict['url']
        }
    }
    if 'feedback' in data_dict:
        data['section']['usefulFeedback'] = float(data_dict['feedback'])
    else:
        data['section']['usefulFeedback'] = None

    if 'evaluated_fairly' in data_dict:
        data['section']['evaluatedFairly'] = float(
            data_dict['evaluated_fairly'])
    else:
        data['section']['evaluatedFairly'] = None

    if 'standards_for_success' in data_dict:
        data['section']['standardsForSuccess'] = float(
            data_dict['standards_for_success'])
    else:
        data['section']['standardsForSuccess'] = None

    if 'helpful_outside_class' in data_dict:
        data['section']['helpfulOutsideOfClass'] = float(
            data_dict['helpful_outside_class'])
    else:
        data['section']['helpfulOutsideOfClass'] = None

    if data_dict['hours'] >= 0:
        data['section']['hoursWorked'] = data_dict['hours']
    else:
        data['section']['hoursWorked'] = None

    data['section']['courseNumbers'] = data_dict['dept_and_num']
    data['section']['instructors'] = data_dict['instructors']

    return data


def send_eval_to_server(course_eval):
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
    res = requests.post(server_url, headers=headers,
                        json=course_eval)
    res.raise_for_status()
