import praw
import json
from kafka import KafkaProducer
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = 'reddit_raw'
        
        # Reddit API credentials from .env
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='SentinelRx v1.0'
        )
        self.subreddits = ['medicine', 'AskDocs', 'AskMedicine', 'ChronicIllness']

    def stream_posts(self):
        logger.info(f"Streaming posts from: {', '.join(self.subreddits)}")
        subreddit_str = "+".join(self.subreddits)
        
        try:
            for submission in self.reddit.subreddit(subreddit_str).stream.submissions():
                data = {
                    "id": submission.id,
                    "title": submission.title,
                    "text": submission.selftext,
                    "url": submission.url,
                    "created_utc": submission.created_utc,
                    "subreddit": submission.subreddit.display_name
                }
                self.producer.send(self.topic, data)
                logger.info(f"Sent Reddit post: {submission.id} from /r/{submission.subreddit.display_name}")
        except Exception as e:
            logger.error(f"Error streaming Reddit posts: {e}")

if __name__ == "__main__":
    # Note: Requires valid REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env
    producer = RedditProducer()
    producer.stream_posts()
