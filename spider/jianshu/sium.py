# -*- coding: utf-8 -*-
# @author : jared
# @date : 2019/7/5 23:23

import logging
import random
import time

import pyperclip
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from . import load

logging.basicConfig(level='INFO', filename='like.log', format='%(message)s')
headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36"}
jianshu = "https://www.jianshu.com"

articles = set()
user_ids = ["000a530f461c", "68a80b0c87a5", "ef6f9c30080a", "b34dcc8c2394", "37ec6dd9fc1c", "04f7029dba14"]
jianshu_u = "{}/u/".format(jianshu)
for uid in user_ids:
    user = "{}{}".format(jianshu_u, uid)
    html = requests.get(user, headers=headers).text
    bs = BeautifulSoup(html, 'html.parser')
    info = bs.find("div", class_="info")
    p_list = info.find_all("p")
    article_num = int(p_list[2].text)

    count = 0
    while count < article_num:
        for page in range(1, 100):
            html = requests.get("{}?order_by=shared_at&page={}".format(user, page), headers=headers).text
            bs = BeautifulSoup(html, 'html.parser')
            titles = bs.find_all('a', class_="title")
            for title in titles:
                article_url = title.get("href")
                if article_url:
                    count += 1
                    articles.add(article_url)
            if count >= article_num:
                break

logging.info("共发布了{}篇文章".format(len(articles)))


def sleep(min_seconds=3, max_seconds=10):
    time.sleep(random.randint(min_seconds, max_seconds))


data = load.load_account()
for row in data:

    username, password, role = row
    options = Options()
    if role != "6":
        options.add_argument('--headless')
        options.add_argument('log-level=3')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('window-size=1366x728')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('blink-settings=imagesEnabled=false')
    driver = webdriver.Chrome(chrome_options=options)

    driver.get("{}/sign_in".format(jianshu))
    driver.maximize_window()

    if role != "6":
        driver.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/ul/li[4]").click()
        driver.find_element_by_class_name("douban").click()
        sleep()

        driver.close()
        window_handles = driver.window_handles
        driver.switch_to.window(window_handles[-1])
        driver.find_element_by_id("inp-alias").send_keys(username)
        driver.find_element_by_id("inp-pwd").send_keys(password)

    try:
        if role != "6":
            driver.find_element_by_xpath("/html/body/div/div[2]/form[2]/div[4]/input[1]").click()
    except:
        logging.error("{} : 授权登录失败".format(role))
    else:
        if role != "6":
            sleep()
        else:
            sleep(45, 60)

        page_title = driver.title
        if page_title.find("简书") == -1:
            logging.error("{} ：{} 登录失败".format(role, page_title))
        else:
            logging.info("Role: {}".format(role))

            # 1. 喜欢
            for article in articles:
                url = "{}{}".format(jianshu, article)
                driver.get(url)
                bs = BeautifulSoup(driver.page_source, 'html.parser')
                like_element = bs.find("div", class_="btn like-group active")
                if not like_element:
                    logging.info("{}".format(url))

            # 2. 写文
            article_data = load.load_article(role)
            driver.get("{}/writer#/".format(jianshu)), sleep()
            for title, content in article_data.items():
                driver.find_element_by_css_selector("i[class='fa fa-plus-circle']").click(), sleep()
                driver.find_element_by_class_name("_24i7u").clear()
                driver.find_element_by_class_name("_24i7u").send_keys(title), sleep()
                driver.find_element_by_id("arthur-editor").clear()
                pyperclip.copy(content)
                driver.find_element_by_id("arthur-editor").send_keys(Keys.CONTROL, 'v'), sleep()
    finally:
        driver.close()
        driver.quit()
