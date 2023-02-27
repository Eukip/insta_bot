from celery import shared_task
from celery.utils.log import get_task_logger

from applications.core.agents import GoogleSheetsAgent
from applications.core.models import Account
from applications.core.utils import (
    collect_instagram_posts,
    like_and_comment_public_pages,
)

logger = get_task_logger(__name__)


@shared_task
def comment_public_pages_asc():
    logger.info("Started leaving likes and comments ASC")
    commented_posts = like_and_comment_public_pages()
    logger.info("Left likes and comment")


@shared_task
def comment_public_pages_desc():
    logger.info("Started leaving likes and comments DESC")
    like_and_comment_public_pages(descending=True)
    logger.info("Left likes and comments")


@shared_task
def collect_new_instagram_posts():
    logger.info("Started collecting posts from Instagram")
    collect_instagram_posts()
    logger.info("Finished collecting posts from Instagram")
    logger.info("Started pushing posts to google sheets")
    agent = GoogleSheetsAgent()
    agent.add_new_records()
    logger.info("Finished pushing posts to google sheets")
