from PIL import Image
import pytesseract
from dotenv import dotenv_values

config = dotenv_values(".env")
evals_dir = config.get('EVALS_DIR')


def process_image(image_name, lang_code):
    image_path = evals_dir + image_name[1::]
    return pytesseract.image_to_string(Image.open(image_path), lang=lang_code, config='--psm 4')


def get_hours_worked(image_path):
    text = process_image(image_path, 'eng')
    average = -1
    if '<' in text:
        average = get_hours_from_ranges(text)
    else:
        average = get_hours_from_exact_list(text)
    if average > 30:
        print('Hours worked error')
        print(text)
        print(average)
        return -1
    else:
        return average


def get_hours_from_ranges(text):
    init = 0
    while text[init] != '<':
        init += 1
    text = text[init:]
    lines = text.split('\n')
    lower_bound = 0
    i = 0
    while 'Total' not in lines[i]:
        line = lines[i]
        num_votes_str = line[line.find('(') + 1: line.find(')')]
        if num_votes_str:
            count = int(float(num_votes_str))
            lower_bound += count * 5 * i
        i += 1
    line = lines[i]
    student_count = round(float(line[line.find('(') + 1: line.find(')')]))
    upper_bound = lower_bound + 29
    total = (upper_bound + lower_bound) / 2
    average = total / student_count
    return average


def get_hours_from_exact_list(text):
    lines = text.split('\n')
    total = 0
    i = 0
    while 'Total' not in lines[i]:
        line = lines[i]
        # Sometimes a lone ')' is extracted from image, even if not actually present
        if '(' in line and ')' in line:
            num_votes_str = line[line.find('(') + 1: line.find(')')]
            if num_votes_str:
                count = int(float(num_votes_str))
                total += count * (i + 1)
        i += 1
    line = lines[i]
    student_count = int(float(line[line.find('(') + 1: line.find(')')]))
    average = total / student_count
    return average
