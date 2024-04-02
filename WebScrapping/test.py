import requests 
from bs4 import BeautifulSoup 
from selenium import webdriver 
from selenium.webdriver.common.keys import Keys 
import time 
from manage_csv import *
  
  
def GetCarbon(url_get_carbon):    
    # initiating the webdriver. Parameter includes the path of the webdriver. 

    # set the webdriver to run in headless mode
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)

    driver.get(url_get_carbon)

    # rest of the code...
    
    # this is just to ensure that the page is loaded 
    time.sleep(1)   
    
    html = driver.page_source #to get the html source of the page

    driver.quit()

    # creating soup object 
    soup = BeautifulSoup(html, 'html.parser')
    #print(soup.prettify())
    # finding an element by its class name
    element = soup.find_all(class_='select-none text-[1rem]')
    # parse the element to get the first word
    carbon=element[0].text.split()[0]
    
    return carbon

#url of the page we want to scrape 
url = "https://app.electricitymaps.com/zone/PT"
carbon=GetCarbon(url)
date=time.strftime("%d/%m/%Y")
hour=time.strftime("%H")
#print the carbon value and time of the request
print("Carbon emmission", carbon, "gCO2eq/kWh at day", date, "and time", hour)
