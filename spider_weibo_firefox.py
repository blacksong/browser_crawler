import time
import random
import sys
from bs4 import BeautifulSoup
import re
import pandas as pd
import sqlite3
from os.path import getsize
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from pprint import pprint
import json
from selenium.webdriver.common.keys import Keys
import auto_parse
global_attrs = {}
global_browser = {'name':None}

def get_a_driver():
    profile_path = '/home/yxs/.mozilla/firefox/sprj69sp.default'
    try:
        driver = webdriver.Firefox(profile_path)
    except:
        driver = webdriver.Firefox()
    global_browser['name'] = 'driver'
    global_browser['driver'] = driver
    return driver
def get_a_session():
    global_browser['session'] = requests.Session()
    global_browser['name'] = 'session'
    return global_browser['session']

def get_html(url):
    if global_browser['name'] == 'session':
        return global_browser['session'].get(url).text
    elif global_browser['name'] == 'file':
        pass
    elif global_browser['name'] == 'driver':
        driver = global_browser['driver']
        driver.get(url)
        wait_browser(driver,20)
        return driver.page_source
def wait_browser(driver,sec):
    try:
        WebDriverWait(driver, 50)
    except:
        pass


global_marks = []
def init_auto_parse(auto_file):
    if auto_file is None:
        return None
    jdata = json.loads(open(auto_file).read())
    pages = [i for i in jdata.keys() if not i.endswith('_url')]
    pages.sort()
    urls = []
    for page in pages:
        items = jdata[page]
        url = items['__urls__'][0]
        urls.append(items['__urls__'])
        if not isinstance(url, str):
            url = url[0]
        html = get_html(url)
        bs = BeautifulSoup(html, 'lxml')
        all_tag_text = [(i, i.text) for i in bs.find_all()]
        k = auto_parse.find_item_bs(bs, all_tag_text, items)
        global_marks.append(k)
    next_button = jdata[pages[0]].get('__next__','下一页')
    return urls[0],next_button
def main(auto_file=None):
    result = []
    driver = get_a_driver()
    now_date = time.strftime('%Y%m%d',time.gmtime())
    tt,next_button = init_auto_parse(auto_file)
    result_count = 0
    urls = tt
    for item in urls:
        temp_result = []
        if isinstance(item,str):
            url = item
        else:
            url = item[0]
        html = get_html(url)
        wait_browser(driver,50)
        current_url0 = driver.current_url
        while True:
            html = driver.page_source
            rr = auto_parse.auto_parse_html(html,global_marks[0])
            for rt in rr:
                rt['parent_url'] = current_url0
                rt['query_date'] = now_date
                for i,tag in enumerate(item[1:]):
                    rt[f'input_tag{i+1}'] = tag 
                keys = list(rt.keys())
                for key in keys:
                    if key.startswith('clicked_'):
                        pass 
            for i in rr:
                result_count += 1
                print(result_count)
                pprint(i)
            try:
                a = driver.find_element_by_link_text(next_button) 
                a.send_keys(Keys.ENTER)

                time.sleep(random.randrange(10,20))
            
                wait_browser(driver,30)
               
                result.extend(rr)
                temp_result.extend(rr)
                current_url = driver.current_url
                if current_url == current_url0:
                    break 
                else:
                    current_url0 = current_url
            except Exception as e:
                print(e)
                print('没有下一页')
                result.extend(rr)
                temp_result.extend(rr)
                break
        df = pd.DataFrame(temp_result)
        df = df.drop_duplicates(df.keys())
        df.to_csv(f'{item[1]}_{item[2]}.csv')
    df = pd.DataFrame(result)
    df = df.drop_duplicates(df.keys())
    df.to_csv('spider_result.csv')
def get_a_new_tab(driver):
    js = 'window.open("");'
    driver.execute_script(js)
if __name__ == '__main__':
    
    main('./mooc.json')
