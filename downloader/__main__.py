from fileinput import filename
from math import remainder
import os
from tabnanny import check
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import time
import json
from pynput.keyboard import Key, Controller

config = dotenv_values(".env")
username = config.get('USERNAME')
password = config.get('PASSWORD')
selenium_dir = config.get('SELENIUM_DIR')

urls_filename = 'downloader/urls.json'
titles_urls_filename = 'downloader/titles_urls.json'

chrome_options = Options()
chrome_options.add_argument(f'--user-data-dir={selenium_dir}')
chrome_options.add_argument(f'--profile-directory={selenium_dir}/Profile 2')

driver = webdriver.Chrome(
    ChromeDriverManager().install(), options=chrome_options)
keyboard = Controller()


def save_page():
    keyboard.press(Key.cmd)
    keyboard.press('s')
    keyboard.release('s')
    keyboard.release(Key.cmd)
    time.sleep(1.5)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(2)
    keyboard.press(Key.esc)
    keyboard.release(Key.esc)
    keyboard.press(Key.esc)
    keyboard.release(Key.esc)
    time.sleep(1)


def get_options(select):
    options = select.find_elements(
        by=By.TAG_NAME, value='option')
    result = []

    for option in options:
        if option.get_attribute('value'):
            result.append(option.get_attribute('value'))
    return result


def login():
    driver.get('https://coursefeedback.uchicago.edu/')

    form = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, 'form18'))
    )

    username_input = form.find_element(by=By.ID, value='okta-signin-username')
    password_input = form.find_element(by=By.ID, value='okta-signin-password')

    username_input.send_keys(username)
    password_input.send_keys(password)

    submit_btn = form.find_element(by=By.ID, value='okta-signin-submit')
    submit_btn.click()


def load_department_year_results_table(department, year):
    driver.get(
        f'https://coursefeedback.uchicago.edu/?Department={department}&AcademicYear={year}&AcademicTerm=All')
    search_results = WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'search-results'))
    )
    tables = search_results.find_elements(
        by=By.ID, value='evalSearchResults')
    if len(tables) > 0:
        return tables[0]
    else:
        return None


def get_results_from_table():
    tbody = driver.find_element(by=By.TAG_NAME, value='tbody')
    results = tbody.find_elements(by=By.CLASS_NAME, value='title')
    return results


def get_department_year_urls(department, year, urls):
    table = load_department_year_results_table(department, year)
    if not table:
        return
    results = get_results_from_table()
    for result in results:
        anchor = result.find_element(by=By.TAG_NAME, value='a')
        urls[anchor.get_attribute('href')] = False


def download_each_eval(urls):
    titles_urls = {}
    for url in urls.keys():
        driver.get(url)
        is_loaded = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'reportView'))
        )
        time.sleep(0.3)
        save_page()
        # map each downloaded eval to its url
        titles_urls[driver.title] = url
    # save eval filename -> url mapping for later retrieval
    with open(titles_urls_filename, 'w') as fp:
        json.dump(titles_urls, fp, sort_keys=True, indent=4)


def save_eval_urls():
    department_select = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, 'academicSubject'))
    )
    year_select = driver.find_element(by=By.ID, value='academicYear')
    departments = get_options(department_select)
    years = get_options(year_select)

    urls = {}

    for department in departments:
        for year in years[::-1]:
            if int(year) > 2016:
                print(department, year)
                get_department_year_urls(department, year, urls)

    with open(urls_filename, 'w') as fp:
        json.dump(urls, fp, sort_keys=True, indent=4)


def download_evals():
    # submit login form
    login()
    # give myself 60 seconds to approve the login attempt on Duo
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, 'academicSubject'))
    )
    if not os.path.exists(urls_filename):
        save_eval_urls()
    with open(urls_filename) as urls_file:
        urls = json.load(urls_file)
        download_each_eval(urls)


if __name__ == '__main__':
    download_evals()
