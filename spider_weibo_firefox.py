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
from IPython import embed
global_attrs = {}
global_browser = {'name':None}

def get_a_driver(profile_path = None):
    if profile_path is not None:
        driver = webdriver.Firefox(profile_path)
    else:
        driver = webdriver.Firefox()
    global_browser['name'] = 'driver'
    global_browser['driver'] = driver
    return driver
def get_a_session():
    global_browser['session'] = requests.Session()
    global_browser['name'] = 'session'
    return global_browser['session']

def get_html(url,table = 0):
    if global_browser['name'] == 'session':
        return global_browser['session'].get(url).text
    elif global_browser['name'] == 'file':
        pass
    elif global_browser['name'] == 'driver':
        driver = global_browser['driver']
        if len(driver.window_handles) <= table:
            get_a_new_tab(driver)
            time.sleep(10)
        if driver.current_window_handle != driver.window_handles[table]:
            driver.switch_to.window(driver.window_handles[table])
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
        print(page,k)
        global_marks.append(k)
    next_button = jdata[pages[0]].get('__next__','下一页')
    return urls[0],next_button
def get_page_in_new_tab(short_url,parrent_url,table):
    website = parrent_url.split('/')
    if short_url.startswith('http'):
        url_clicked = short_url 
    elif short_url.startswith('//'):
        url_clicked = website[0]+short_url
    elif short_url.startswith('/'):
        url_clicked = '/'.join(website[:3]) + short_url
    else:
        url_clicked = '/'.join(website[:-1]) + short_url
    print(table,url_clicked)
    get_html(url_clicked,table)
def main(auto_file=None):
    result = []
    driver = get_a_driver('/home/yxs/.mozilla/firefox/sprj69sp.default')
    now_date = time.strftime('%Y%m%d',time.gmtime())
    input("请登录账号（设置cookie使用，如无需登录账号可直接回车）:")
    tt,next_button = init_auto_parse(auto_file)
    result_count = 0
    urls = tt
    for item in urls:
        temp_result = []
        if isinstance(item,str):
            url = item
        else:
            url = item[0]
        driver.switch_to.window(driver.window_handles[0])
        html = get_html(url)
        wait_browser(driver,50)
        current_url0 = driver.current_url
        while True:
            table_n = 0
            html = driver.page_source
            rr = auto_parse.auto_parse_html(html,global_marks[0])
            for rt in rr:
                rt['parent_url'] = current_url0
                rt['query_date'] = now_date
                for i,tag in enumerate(item[1:]):
                    rt[f'input_tag{i+1}'] = tag 
                keys = list(rt.keys())
                for key in keys:
                    if key.find('.clicked') != -1:
                        table_m = table_n+1
                        get_page_in_new_tab(rt[key],current_url0,table_m)
                        time.sleep(1)
                        html2 = driver.page_source 
                        rty = auto_parse.auto_parse_html(html2,global_marks[table_m])
                        print(rty)
                        if not rty:
                            continue
                        rt.update(rty[0])
            driver.switch_to.window(driver.window_handles[table_n])
            print(len(rr),current_url0)
            for i in rr:
                result_count += 1
                print(result_count)
                pprint(i)
            try:
                try:
                    a = driver.find_element_by_link_text(next_button) 
                    a.send_keys(Keys.ENTER)
                except:
                    next_url = auto_parse.get_next_url(next_button,driver.page_source,driver.current_url)
                    print(next_url)
                    if next_url:
                        driver.get(next_url)


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
        
        temp_p = Path(f'{item[1]}_{item[2]}.csv')
        if temp_p.exists():
            df2 = pd.read_csv(temp_p)[df.keys()]
        df = df.append(df2)
        df = df.drop_duplicates(df.keys())
        df.to_csv(temp_p,index=False)

    df = pd.DataFrame(result)
    df = df.drop_duplicates(df.keys())
    df.to_csv('spider_result.csv',index=False)
def get_a_new_tab(driver):
    js = 'window.open("");'
    # help(driver.execute_script)
    driver.execute_script(js)
    print('add a new tab')
    time.sleep(2)
if __name__ == '__main__':
    
    main('./byr.json')
