import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def set_chrome_options() -> Options:
    """
    Sets chrome options for Selenium.

    Chrome options for headless browser is enabled.
    """

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}

    return chrome_options


def get_carbon(url_get_carbon):
    # initiating the webdriver. Parameter includes the path of the webdriver.
    driver = webdriver.Chrome(options=set_chrome_options())
    driver.get(url_get_carbon)

    # this is just to ensure that the page is loaded
    time.sleep(1)

    # to get the html source of the page
    html = driver.page_source
    driver.quit()

    # creating soup object
    soup = BeautifulSoup(html, "html.parser")
    # print(soup.prettify())

    # finding an element by its class name
    element = soup.find_all(class_="select-none text-[1rem]")
    # parse the element to get the first word
    carbon = element[0].text.split()[0]

    return carbon
