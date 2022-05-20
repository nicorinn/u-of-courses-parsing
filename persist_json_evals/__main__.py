import os
import glob
import persist_eval as persist_eval

json_dir = './json_evals'
json_evals_format = json_dir + '/*.json'


def persist_json_evals():
    if not os.path.exists(json_dir):
        print(f'Error: no {json_dir} directory found')
    else:
        for json_eval in glob.glob(json_evals_format):
            persist_eval.persist_eval(json_eval)


if __name__ == '__main__':
    persist_json_evals()
