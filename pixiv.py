from pixivpy3 import *
import json
import csv
from time import sleep
import sys, io, re, os

# from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
from PIL import Image
import requests
from retry import retry

pixiv_url = "https://accounts.pixiv.net/login"
pixiv_following_users_list_url = (
    "https://www.pixiv.net/bookmark.php?type=user&rest=show&p="
)
driver_path = "./driver/chromedriver.exe"
client_path = "./json/client.json"
block_str_path = "./json/block.json"
info_path = "./info/"
info_name = "following_users.csv"
userdata_path = "./UserData/"
download_path = "./download/"
max_works = 10000
global browser


def read_json(path):
    # jsonを読み込み
    f = open(path, "r", encoding="utf-8")
    result = json.load(f)
    f.close()
    return result


def read_csv(path, filename):
    df_result = pd.read_csv(path + filename)
    return df_result


def write_csv(path, filename, data):
    data.to_csv(path + filename, encoding="utf_8_sig", index=False)


def set_filename(user_name, illust_title, illust_id):

    block_str = read_json(block_str_path)
    HAN2ZEN = str.maketrans(block_str["HAN"], block_str["ZEN"])

    user_name = user_name.encode("utf8").decode("utf8")
    illust_title = illust_title.encode("utf8").decode("utf8")

    image_name = "{0} - {1} ({2}).png".format(
        user_name.translate(HAN2ZEN), illust_title.translate(HAN2ZEN), illust_id
    )
    return image_name


def get_following_users_info(pages, api, aapi):

    df_following_users_info = pd.DataFrame()

    following_users_id = []
    following_users_name = []
    following_users_works = []
    following_users_url = []

    for page in range(1, pages + 1):

        print(pixiv_following_users_list_url + str(page))
        browser.get(pixiv_following_users_list_url + str(page))
        sleep(1)
        # XPathでaタグからuser_idを取得
        following_users_ids = browser.find_elements_by_xpath(
            '//*[@id="search-result"]/div[1]/ul/li/div/a'
        )
        for i, target_users_id in enumerate(following_users_ids):

            following_users_info = aapi.user_detail(
                int(target_users_id.get_attribute("data-user_id"))
            )
            try:
                following_users_id.append(following_users_info.user.id)
                following_users_name.append(following_users_info.user.name)
                following_users_works.append(
                    following_users_info.profile.total_illusts
                    + following_users_info.profile.total_manga
                )
                following_users_url.append(
                    "https://www.pixiv.net/users/" + str(following_users_info.user.id)
                )
            except:
                continue

    df_following_users_info["id"] = following_users_id
    df_following_users_info["username"] = following_users_name
    df_following_users_info["作品数"] = following_users_works
    df_following_users_info["url"] = following_users_url

    write_csv(info_path, info_name, df_following_users_info)


def get_following_illust(api, aapi, input_path, output_path):

    df_following_users_info = read_csv(input_path, info_name)

    for i in range(0, len(df_following_users_info) - 1):
        target_users_id = df_following_users_info.loc[i]["id"]
        target_user_name = df_following_users_info.loc[i]["username"]
        target_works_info = api.users_works(target_users_id, per_page=max_works)
        target_user_total_illust = target_works_info.pagination.total

        for work in range(0, target_user_total_illust):
            target_illust = target_works_info.response[work]
            image_name = set_filename(
                target_user_name, target_illust.title, target_illust.id
            )
            # if target_illust.is_manga:
            # for page in range(0, target_works_info.response[0].page_count):
            #     page_info = target_works_info.response[0].metadata.pages[page]
            #     image_name += " {0}ページ".format(page)
            #         aapi.download(page_info.image_urls, path=download_path, name=image_name)
            # else:
            aapi.download(
                target_illust.image_urls.large, path=download_path, name=image_name
            )


def login_pixiv(client):

    browser.find_element_by_xpath(
        '//*[@id="LoginComponent"]/form/div[1]/div[1]/input'
    ).send_keys(client["pixiv_id"])
    browser.find_element_by_xpath(
        '//*[@id="LoginComponent"]/form/div[1]/div[2]/input'
    ).send_keys(client["password"])
    sleep(5)
    browser.find_element_by_xpath('//*[@id="LoginComponent"]/form/button').click()
    sleep(30)


def main():

    api = PixivAPI()
    aapi = AppPixivAPI()

    client = read_json(client_path)

    # ログイン処理
    api.login(client["pixiv_id"], client["password"])
    aapi.login(client["pixiv_id"], client["password"])

    self_info = aapi.user_detail(client["user_id"])

    if not os.path.exists(info_path):
        os.mkdir(info_path)

    if not os.path.isfile(info_path + info_name):
        # フォローユーザー一覧ページ数を取得
        following_users_num = self_info.profile.total_follow_users

        if following_users_num % 48 != 0:
            pages = (following_users_num // 48) + 1
        else:
            pages = following_users_num // 48

        get_following_users_info(pages, api, aapi)

    get_following_illust(api, aapi, info_path, download_path)


if __name__ == "__main__":
    # # optionを指定してbrowserを開く
    # options = webdriver.ChromeOptions()
    # options.add_argument('--user-data-dir=' + userdata_path)
    # browser = webdriver.Chrome(executable_path=driver_path, chrome_options=options)

    # browser.get(pixiv_url)
    # sleep(1)

    main()
