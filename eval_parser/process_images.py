from PIL import Image
import pytesseract


def process_image(image_name, lang_code):
    return pytesseract.image_to_string(Image.open(image_name), lang=lang_code)


def get_hours_worked(image_path):
    data_eng = process_image(image_path, "eng")
    print(data_eng)
