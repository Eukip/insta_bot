from django.conf import settings

from applications.core import constants
from applications.core.agents import InstagramAgent
from applications.core.models import (
  Account,
  PublicPage,
  Comment,
)


def like_and_comment_public_pages(descending: bool = False) -> bool:
    ordering = '-id' if descending else 'id'
    accounts = Account.objects.filter(social_media=constants.INSTAGRAM).order_by('?')
    public_pages = PublicPage.objects.filter(social_media=constants.INSTAGRAM).order_by(ordering)

    # loop through all instagram accounts
    for account in accounts:
        commented_posts = 0
        insta_agent = InstagramAgent(account.username, account.password)

        # try to login up to 3 times
        retries, login_status = 0, False
        while not login_status and (retries := retries + 1) < 3:
            login_status = insta_agent.login()

        # if log in fails loop to next account
        if not login_status:
            continue

        # send up to 5 comments to public pages, cause instagram limit is 5 comments per hour
        for public_page in public_pages:
            if commented_posts == 5:
                break

            commented_posts += insta_agent.like_and_comment_posts(account, public_page.url, 10)

        # don't forget to close a webdriver
        insta_agent.close_driver()
    insta_agent.close_driver()
    return True


def collect_instagram_posts() -> bool:
    username = settings.INSTAGRAM_USERNAME
    password = settings.INSTAGRAM_PASSWORD
    sessionid = settings.INSTAGRAM_SESSIONID
    insta_agent = InstagramAgent(username, password)
    insta_agent.set_sessionid(sessionid)
    # login_status = insta_agent.login()

    # if not login_status:
    #    return False
    
    total_posts = insta_agent.collect_new_posts()
    print(total_posts)
    return True

