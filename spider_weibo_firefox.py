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


def parse_html(html):
    bs = BeautifulSoup(html,'lxml')
    t = bs.find(class_='m-course-list')
    s = t.div.find_all(['div'],recursive=False)
    rr = [parse_html_item(i) for i in s]
    return rr
def get_text(bs,**kargs):
    t = bs.find(**kargs)
    if t:
        return t.text
    else:
        return ''
def parse_html_item(item_bs):
    item = dict()
    try:
        t = item_bs.find(['img'])
        item['course'] = t.attrs['alt']
        # t = item_bs.div.attrs['data-href']
        item['course_url'] = item_bs.attrs['data-href']
        item['national_course'] = '是' if item_bs.text.find('国家精品') != -1 else '否'
        item['university'] = get_text(item_bs, class_='t21 f-fc9')
        all_a = item_bs.find_all(['a'])
        author = []
        for i in all_a:
            attrs = i.attrs.get('class')
            if attrs is None:
                continue
            if attrs[0] == 'f-fc9':
                author.append(i.text)
        item['author'] = ','.join(author)
        item['profile'] = get_text(item_bs,class_='p5 brief f-ib f-f0 f-cb')
        item['hot'] = get_text(item_bs,class_='hot')
    except:
        pass
    return item
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
    for page in pages:
        items = jdata[page]
        url = jdata[page+'_url'][0]
        if not isinstance(url, str):
            url = url[0]
        html = get_html(url)
        bs = BeautifulSoup(html, 'lxml')
        all_tag_text = [(i, i.text) for i in bs.find_all()]
        k = auto_parse.find_item_bs(bs, all_tag_text, items)
        global_marks.append(k)
    return jdata[pages[0]+'_url']
def main(urls,auto_file=None):
    db = sqlite3.connect('spider_database.sqlite3')
    table_name = 'spider_record_ggg318'
    result = []
    driver = get_a_driver()
    now_date = time.strftime('%Y%m%d',time.gmtime())
    tt = init_auto_parse(auto_file)
    result_count = 0
    if tt:
        urls = tt
        is_auto = True 
    else:
        is_auto = False
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
            if is_auto:
                rr = auto_parse.auto_parse_html(html,global_marks[0])
            else:
                rr = parse_html(html)
            for rt in rr:
                rt['parent_url'] = current_url0
                rt['query_date'] = now_date
                for i,tag in enumerate(item[1:]):
                    rt[f'input_tag{i+1}'] = tag 
                keys = list(rt.keys())
                for key in keys:
                    if key.startswith('clicked_'):
                        pass 
            df = pd.DataFrame(rr)
            df.to_sql(table_name,db,if_exists='append')
            db.commit()
            for i in rr:
                result_count += 1
                print(result_count)
                pprint(i)
            try:
                a = driver.find_element_by_link_text('下一页') 
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
    
    main(None,'./ggg318.json')
