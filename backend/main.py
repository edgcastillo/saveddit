from fastapi import FastAPI
import praw
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

class RedditCredentials(BaseModel):
    client_id: str
    client_secret: str
    username: str
    password: str
@app.post("/saved", response_model=List[Dict])
def get_saved_items(credentials: RedditCredentials):
    reddit = praw.Reddit(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        user_agent="SavedPostsFetcher/1.0",
        username=credentials.username,
        password=credentials.password
    )

    saved_items = []
    for item in reddit.user.me().saved(limit=None):
        saved_item = {
            "type": "comment" if isinstance(item, praw.models.Comment) else "post",
            "title": item.body if isinstance(item, praw.models.Comment) else item.title,
            "url": f"https://reddit.com{item.permalink}",
            "subreddit": item.subreddit.display_name
        }
        saved_items.append(saved_item)
    
    return saved_items