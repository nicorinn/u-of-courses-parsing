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
    time.sleep(1)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(1)
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
        EC.presence_of_element_located((By.ID, 'login'))
    )

    username_input = form.find_element(by=By.ID, value='username')
    password_input = form.find_element(by=By.ID, value='password')

    username_input.send_keys(username)
    password_input.send_keys(password)

    submit_btn = form.find_element(by=By.ID, value='submit')
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
        urls[anchor.get_attribute('href')] = True


def download_evals():
    # submit login form
    login()
    # give myself 60 seconds to approve the login attempt on Duo
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
                get_department_year_urls(department, year, urls)

    with open('urls', 'w') as fp:
        json.dump(urls, fp, sort_keys=True, indent=4)

    for url in urls.keys():
        driver.get(url)
        time.sleep(3)
        save_page()


if __name__ == '__main__':
    download_evals()
