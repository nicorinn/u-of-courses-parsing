from PIL import Image
import pytesseract
from dotenv import dotenv_values

config = dotenv_values(".env")
evals_dir = config.get('EVALS_DIR')


def process_image(image_name, lang_code):
    image_path = evals_dir + image_name[1::]
    return pytesseract.image_to_string(Image.open(image_path), lang=lang_code)


def get_hours_worked(image_path):
    text = process_image(image_path, 'eng')
    lines = text.split('\n')
    lower_bound = 0
    i = 0
    while 'Total' not in lines[i]:
        line = lines[i]
        count_str = line[line.find('(') + 1: line.find(')')]
        if count_str:
            count = int(count_str)
            lower_bound += count * 5 * i
        i += 1
    line = lines[i]
    student_count = int(line[line.find('(') + 1: line.find(')')])
    upper_bound = lower_bound + 29
    total = (upper_bound + lower_bound) / 2
    average = total / student_count

    return average
