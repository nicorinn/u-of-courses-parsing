import glob
import process_doc as process_doc
from dotenv import dotenv_values

config = dotenv_values(".env")
evals_dir = config.get('EVALS_DIR')

raw_evals_format = evals_dir + '/*.html'


def main():
    for course_eval in glob.glob(raw_evals_format):
        process_doc.process_eval(course_eval)


if __name__ == '__main__':
    main()
