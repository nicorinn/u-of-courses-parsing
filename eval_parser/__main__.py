import glob
import process_doc as process_doc

raw_evals_format = './sample_evals/*.html'


def main():
    for course_eval in glob.glob(raw_evals_format):
        process_doc.process_eval(course_eval)


if __name__ == '__main__':
    main()
