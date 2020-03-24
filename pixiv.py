from pixivpy3 import *
import sys, io, re, os
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
from PIL import Image
import requests

import ReadFile


class Downloader(object):
    url = {}

    def __init__(self, conf):
        self.common_conf = conf


class PixivDownloader(Downloader):
    def __init__(self, conf):
        super().__init__(conf["common"])
        self.pixiv_conf = conf["pixiv"]
        self.api = PixivAPI()
        self.aapi = AppPixivAPI()
        self.login(self.pixiv_conf["client"])
        self.my_info = self.aapi.user_detail(self.pixiv_conf["client"]["user_id"])

    def login(self, conf):
        # ログイン処理
        self.api.login(conf["pixiv_id"], conf["password"])
        self.aapi.login(conf["pixiv_id"], conf["password"])

    def get_following_users_info(self):
        #:HACK
        dst = os.path.join(self.pixiv_conf["dst_path"] + self.pixiv_conf["csv"][0])
        if not os.path.isfile(dst):
            following_users_num = self.my_info.profile.total_follow_users
            users_previews, next_url = self.aapi.user_following(
                self.pixiv_conf["client"]["user_id"]
            ).values()

            df_following_users_info = pd.DataFrame()
            df_unsubscribed_user = pd.DataFrame()

            following_users_id = []
            following_users_name = []
            following_users_works = []
            following_users_url = []
            unsubscribed_user = []

            print("getting user...")
            i = 0
            while True:
                i += len(users_previews)
                print("\n processing {}/{}".format(i, following_users_num))
                for prev in users_previews:
                    if not prev["illusts"]:
                        unsubscribed_user.append(prev["user"]["name"])
                        print("{} was unsubscribed".format(prev["user"]["name"]))
                        continue

                    print("getting {}".format(prev["user"]["name"]))
                    following_users_id.append(prev["user"]["id"])
                    following_users_name.append(prev["user"]["name"])
                    following_users_works.append(
                        self.api.users_works(prev["user"]["id"])["pagination"]["total"]
                    )
                    following_users_url.append(
                        "https://www.pixiv.net/users/" + str(prev["user"]["id"])
                    )
                sleep(1)
                next_qs = self.aapi.parse_qs(next_url)
                if next_qs is None:
                    break
                users_previews, next_url = self.aapi.user_following(**next_qs).values()

            df_following_users_info["id"] = following_users_id
            df_following_users_info["username"] = following_users_name
            df_following_users_info["作品数"] = following_users_works
            df_following_users_info["url"] = following_users_url

            df_unsubscribed_user["username"] = unsubscribed_user

            df_following_users_info.to_csv(
                self.pixiv_conf["csv"][0], encoding="utf_8_sig", index=False
            )
            df_unsubscribed_user.to_csv("退会ユーザ.csv", encoding="utf_8_sig", index=False)

    # def get_following_illust(self):

    #     df_following_users_info = read_csv(input_path, info_name)

    #     block_str = read_json(block_str_path)
    #     HAN2ZEN = str.maketrans(block_str["HAN"], block_str["ZEN"])

    #     for i in range(0, len(df_following_users_info) - 1):
    #         target_users_id = df_following_users_info.loc[i]["id"]
    #         target_user_name = df_following_users_info.loc[i]["username"]
    #         target_works_info = api.users_works(target_users_id, per_page=max_works)
    #         target_user_total_illust = target_works_info.pagination.total

    #         target_download_path = "./download/{}".format(
    #             target_user_name.translate(HAN2ZEN)
    #         )

    #         if not os.path.exists(target_download_path):
    #             os.mkdir(target_download_path)

    #         for work in range(0, target_user_total_illust):
    #             target_illust = target_works_info.response[work]
    #             image_name = set_filename(
    #                 target_user_name.translate(HAN2ZEN),
    #                 target_illust.title.translate(HAN2ZEN),
    #                 target_illust.id,
    #             )
    #             # if target_illust.is_manga:
    #             # for page in range(0, target_works_info.response[0].page_count):
    #             #     page_info = target_works_info.response[0].metadata.pages[page]
    #             #     image_name += " {0}ページ".format(page)
    #             #         aapi.download(page_info.image_urls, path=download_path, name=image_name)
    #             # else:
    #             aapi.download(
    #                 target_illust.image_urls.large,
    #                 path=target_download_path,
    #                 name=image_name,
    #             )
    #             time.sleep(1)

    # def set_filename(self, user_name, illust_title, illust_id):

    #     user_name = user_name.encode("utf8").decode("utf8")
    #     illust_title = illust_title.encode("utf8").decode("utf8")

    #     image_name = "{0} - {1} ({2}).png".format(user_name, illust_title, illust_id)
    #     return image_name


def main():

    rf = ReadFile.JsonFile("./config/config.json")
    conf = rf.read()

    pid = PixivDownloader(conf)

    # pid.get_following_users_info()


if __name__ == "__main__":
    main()
