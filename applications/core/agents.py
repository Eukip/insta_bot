import gspread
import os
import random
import typing
from collections import defaultdict
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from typing import Tuple

from django.conf import settings

from applications.core import constants
from applications.core.models import (
    Account,
    Comment,
    Post,
    PublicPage,
)


class InstagramAgent:
    def __init__(self, username: str, pw: str) -> None:
        print('Initializing')
        if settings.DEBUG:        
            self.driver = webdriver.Chrome()
        else:
            chrome_options = Options()
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('window-size=1300,600')
            self.driver = webdriver.Chrome(options=chrome_options)
        self.timeout = 60
        self.username = username
        self.pw = pw
    
    def set_sessionid(self, sessionid: str) -> bool:
        self.driver.get('https://instagram.com')
        cookies = {'name': 'sessionid', 'value': sessionid}
        self.driver.add_cookie(cookies)
        return True

    def login(self) -> bool:
        print('Starting to log in')
        print(self.username)
        status = False

        # open instagram and wait 10 seconds
        self.driver.get('https://instagram.com/')
        print(self.driver.page_source)
        sleep(20)

        # wait until all necessary elements present on log in page
        try:
            username_input = EC.presence_of_element_located((By.NAME, 'username'))
            password_input = EC.presence_of_element_located((By.NAME, 'password'))
            login_button = EC.presence_of_element_located((
              By.XPATH,
              '/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[4]/button',
            ))
            WebDriverWait(self.driver, self.timeout).until(username_input)
            WebDriverWait(self.driver, self.timeout).until(password_input)
            WebDriverWait(self.driver, self.timeout).until(login_button)
        except TimeoutException:
            print('Timed out waiting for LOG IN page to load')
            return status
        else:
            self.driver.find_element_by_name('username').send_keys(self.username)
            sleep(5)
            self.driver.find_element_by_name('password').send_keys(self.pw)
            sleep(5)

            # click button "Log in"
            self.driver.find_element_by_xpath(
              '/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[4]/button').click()
            status = True
            sleep(10)

        try:
            decline_storing_history = EC.presence_of_element_located((
              By.XPATH,
              '/html/body/div[1]/section/main/div/div/div/div/button',
            ))
            WebDriverWait(self.driver, self.timeout).until(decline_storing_history)
        except TimeoutException:
            print('Timed out waiting for SAVE HISTORY POP UP to load')
        else:
            # click button "Not now" for storing history
            self.driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div/div/button').click()
            sleep(20)

        try:
            decline_notifications = EC.presence_of_element_located((
              By.XPATH,
              '/html/body/div[4]/div/div/div/div[3]/button[2]',
            ))
            WebDriverWait(self.driver, self.timeout).until(decline_notifications)
        except TimeoutException:
            print('Timed out waiting for ENABLE NOTIFICATIONS POP UP page to load')
        else:
            # click button "Not now" for not enabling notifications
            self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div/div[3]/button[2]').click()
            sleep(20)
            print(self.driver.find_element_by_xpath('/html/body/div[1]/section/main/section/div[3]/div[1]/div/div[2]/div[1]/a').text)
        return status
          
    def collect_new_posts(self) -> int:
        public_pages = PublicPage.objects.filter(social_media=constants.INSTAGRAM)
        total_posts_count = 0

        for page in public_pages:
            self.driver.get(page.url)
            sleep(5)
            posts_count = 0

            try:
                pub_block_existance = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.v1Nh3'))
                WebDriverWait(self.driver, self.timeout).until(pub_block_existance)
        
            except TimeoutException:
                print('Timed out waiting for a publication block to load')
                continue
            else:
                pub_block = self.driver.find_element_by_css_selector('div.v1Nh3')
                pub_block.find_element_by_tag_name('a').click()

            for i in range(settings.MAX_POSTS_COUNT):
                sleep(5)
                url = self.driver.current_url
                if Post.objects.filter(url=url).exists():
                    break

                Post.objects.create(
                    social_media=constants.INSTAGRAM,
                    public_page=page,
                    url=url,
                )
                total_posts_count += 1

                if i < settings.MAX_POSTS_COUNT - 1:
                    try:
                        button_next = EC.presence_of_element_located((By.CSS_SELECTOR, 'a.coreSpriteRightPaginationArrow'))
                        WebDriverWait(self.driver, self.timeout).until(button_next)

                    except TimeoutException:
                        print('Timed out waiting for NEXT button to load')
                        break

                    else:
                        self.driver.find_element_by_css_selector('a.coreSpriteRightPaginationArrow').click()
        return total_posts_count


    def like_and_comment_posts(self, account: Account, link: str, post_number: int) -> int:
        print('Final version')
        print('Started to leave likes and comments')
        print(link)
        self.driver.get(link)
        sleep(10)

        commented_posts, button_like, like_value = 0, None, False

        try:
            publication_block = EC.presence_of_element_located((By.CSS_SELECTOR, 'div.v1Nh3'))
            WebDriverWait(self.driver, self.timeout).until(publication_block)
        except TimeoutException:
            print('Timed out waiting for LIKE BUTTON to load')
        else:
            block = self.driver.find_element_by_css_selector('div.v1Nh3')
            block.find_element_by_tag_name('a').click()
            like_value = self._check_like()
            button_like = self.driver.find_element_by_class_name('fr66n')
            
        
        posts = 0
        while not like_value and (posts := posts + 1) < post_number + 1:
            print(self.driver.current_url)
            if button_like:
                self._like_post(button_like)
                if self._check_like():
                    print('like left')
                else:
                    print('couldn\'t leave like')

            # get random comment for given account
            comments_count = account.comments.count()
            if comments_count == 0:
                continue
            
            if comments_count == 1:
                comment = account.comments.first()

            else:
                random_min, random_max = 0, comments_count - 1
                random_num = random.randint(random_min, random_max)
                comment = account.comments.all()[random_num]

            status = self._comment_post(comment.text)
            if status:
                commented_posts += 1
                print(f'One more comment. Total: {commented_posts} comments')

            if posts < post_number:
                self.driver.find_element_by_css_selector('a.coreSpriteRightPaginationArrow').click()
                like_value = self._check_like()
                button_like = self.driver.find_element_by_class_name('fr66n')

        sleep(10)
        return commented_posts
    
    def close_driver(self) -> None:
        self.driver.quit()

    def _check_like(self) -> bool:
        sleep(5)
        liked = False
        try:
            button_existence = EC.presence_of_element_located((By.CLASS_NAME, 'fr66n'))
            WebDriverWait(self.driver, self.timeout).until(button_existence)
        except TimeoutError:
            print('Timed out waiting for like button')
        else:
            button_like = self.driver.find_element_by_class_name('fr66n')
            like_value = button_like.find_element_by_tag_name('svg').get_attribute("aria-label")
            liked = like_value == 'Unlike'
        return liked

    def _like_post(self, button_like) -> None:
        sleep(10)
        # button_like.click()
        self.driver.execute_script("arguments[0].click();", button_like)

    def _comment_post(self, comment) -> bool:
        sleep(5)
        status = False

        try:
            comment_existence = EC.presence_of_element_located((By.CLASS_NAME, 'Ypffh'))
            WebDriverWait(self.driver, self.timeout).until(comment_existence)
        except TimeoutException:
            print('Couldn\'t wait for comment area')

        try:
            commentArea = self.driver.find_element_by_class_name('Ypffh')
            #commentArea.click()
            self.driver.execute_script("arguments[0].click();", commentArea)
            sleep(10)
            commentArea = self.driver.find_element_by_class_name('Ypffh')
            # commentArea.click()
            self.driver.execute_script("arguments[0].click();", commentArea)
            sleep(20)
            commentArea.send_keys(comment)
            sleep(10)
            commentArea.submit()
            status = True
        except:
            print('Could not leave a comment')

        return status


class GoogleSheetsAgent:
    def __init__(self):
        self.sheet_urls = [
            'https://docs.google.com/spreadsheets/d/1l5jSqgehqRkvLzMqL7oubUZvJFjyzTkVHUTvp8Bee2M/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/1sVCPmYbmczpTBuo5U7qxpoxXGotpqmmR1aT0un9i09I/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/1MrBPyf4T7mUWlI6sWxtpE1UsDwR0lPbHQAuvxHOaq18/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/17sTvOGliLVj2aXAaGD_ne04OmEBmPWY-Mc_Er_59QbE/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/1tpdAt3tzgcuGu5fZLQY-9aTYjsQNBz824vXEgi-ylWg/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/1kSwiGu1YgEE4CKqtBaRo08wNC4PyfME13yDxc8f7rpE/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/19LmoVqvXfOHxXYjEDlIuEhC4LLSwl1ikSSGqnOUsC4w/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/1x4u8nH4M_VqVE0e6fL68jrI9S2C9Sg7h0aasnCx3P4U/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/1YSTzSmwgFydVQ3w3r3mPAVmTsKbbbPM1iQ6gH7Th_N4/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/18h5g_qHTro1wT6kAUsUhzHfu9N0bMbDPG8XbE8zMkT0/edit?usp=sharing',
        ]
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(settings.BASE_DIR, 'logs/creds.json'), scope)
        self.client = gspread.authorize(creds)

    def add_new_records(self):
        posts = Post.objects.filter(added_to_gs=False)
        posts_dict = defaultdict(list)

        for post in posts:
            rand_key = random.randint(1,10)

            if rand_key in posts_dict:
                posts_dict[rand_key].append(post)
            else:
                posts_dict[rand_key] = [post, ]

        # send to files
        for sheet_url, key in zip(self.sheet_urls, posts_dict.keys()):
            self.sheet = self.client.open_by_url(sheet_url)
            sheet_posts = posts_dict[key]
            rows = [[post.url, ] for post in sheet_posts]
            
            sheet = self.client.open_by_url(sheet_url).sheet1
            sheet.append_rows(rows)
            
            # change all comments
            for num, comment in enumerate(Comment.objects.all(), 1):
                sleep(5)
                sheet.update_cell(num, 2, comment.text)
        posts.update(added_to_gs=True)

