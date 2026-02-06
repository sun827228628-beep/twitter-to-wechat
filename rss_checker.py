import feedparser
import requests
import json
import os
from datetime import datetime
import time

TWITTER_USERS = [
    "elonmusk",
]

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
SENT_FILE = 'sent_items.txt'

def load_sent_items():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_sent_item(item_id):
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{item_id}\n")

def send_to_wechat(title, link, author):
    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL not set")
        return False
    
    title = title.replace('<', '&lt;').replace('>', '&gt;')
    content = f"【{author}】new tweet\n\n{title}\n\n{link}"
    
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print(f"SUCCESS: {title[:30]}...")
                return True
            else:
                print(f"FAILED: {result}")
                return False
        else:
            print(f"HTTP ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

def check_rss():
    sent_items = load_sent_items()
    new_count = 0
    
    for username in TWITTER_USERS:
        rss_url = f"https://rsshub.app/twitter/user/{username}"
        
        try:
            print(f"\nChecking @{username}...")
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                print(f"WARNING: No entries found")
                continue
            
            for entry in feed.entries[:3]:
                item_id = entry.get('id', entry.link)
                
                if item_id not in sent_items:
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')
                    author = username
                    
                    print(f"NEW: {title[:50]}...")
                    
                    if send_to_wechat(title, link, author):
                        save_sent_item(item_id)
                        new_count += 1
                    
                    time.sleep(2)
                else:
                    print(f"SKIP: already sent")
                    
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\nDONE! Sent {new_count} new tweets")

if __name__ == '__main__':
    print(f"START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    check_rss()
