import feedparser
import requests
import json
import os
from datetime import datetime
import time

# Twitter usernames to monitor
TWITTER_USERS = [
    "elonmusk",
    "hgsc001",
    "tokutei_view",
]

# Weibo user UIDs to monitor
WEIBO_USERS = [
   "5170800388",
   "6892172355",
   "6084251294",
]

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
SENT_FILE = 'sent_items.txt'

# Multiple RSSHub instances to try
RSSHUB_INSTANCES = [
    "https://rsshub.rssforever.com",
    "https://rss.shab.fun",
    "https://rsshub.app",
]

def load_sent_items():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_sent_item(item_id):
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{item_id}\n")

def send_to_wechat(content):
    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL not set")
        return False
    
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

def check_twitter():
    sent_items = load_sent_items()
    new_count = 0
    
    for username in TWITTER_USERS:
        success = False
        
        for instance in RSSHUB_INSTANCES:
            rss_url = f"{instance}/twitter/user/{username}"
            
            try:
                print(f"\nTrying {instance} for Twitter @{username}...")
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    print(f"SUCCESS with {instance}, found {len(feed.entries)} entries")
                    success = True
                    
                    for entry in feed.entries[:3]:
                        item_id = entry.get('id', entry.link)
                        
                        if item_id not in sent_items:
                            title = entry.get('title', 'No title')
                            link = entry.get('link', '')
                            
                            print(f"NEW: {title[:50]}...")
                            
                            content = f"Twitter @{username} posted:\n\n{title}\n\n{link}"
                            if send_to_wechat(content):
                                save_sent_item(item_id)
                                new_count += 1
                            
                            time.sleep(2)
                    
                    break  # Success, stop trying other instances
                else:
                    print(f"No entries from {instance}")
                    
            except Exception as e:
                print(f"Failed with {instance}: {str(e)[:100]}")
                time.sleep(1)
                continue
        
        if not success:
            print(f"WARNING: All instances failed for @{username}")
    
    return new_count

def check_weibo():
    sent_items = load_sent_items()
    new_count = 0
    
    for uid in WEIBO_USERS:
        success = False
        
        for instance in RSSHUB_INSTANCES:
            rss_url = f"{instance}/weibo/user/{uid}"
            
            try:
                print(f"\nTrying {instance} for Weibo UID {uid}...")
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    print(f"SUCCESS with {instance}, found {len(feed.entries)} entries")
                    success = True
                    
                    author = feed.feed.get('title', f'Weibo-{uid}')
                    
                    for entry in feed.entries[:3]:
                        item_id = entry.get('id', entry.link)
                        
                        if item_id not in sent_items:
                            title = entry.get('title', 'No title')
                            link = entry.get('link', '')
                            
                            print(f"NEW: {title[:50]}...")
                            
                            content = f"Weibo @{author} posted:\n\n{title}\n\n{link}"
                            if send_to_wechat(content):
                                save_sent_item(item_id)
                                new_count += 1
                            
                            time.sleep(2)
                    
                    break  # Success, stop trying other instances
                else:
                    print(f"No entries from {instance}")
                    
            except Exception as e:
                print(f"Failed with {instance}: {str(e)[:100]}")
                time.sleep(1)
                continue
        
        if not success:
            print(f"WARNING: All instances failed for UID {uid}")
    
    return new_count

if __name__ == '__main__':
    print(f"START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using RSSHub instances: {', '.join(RSSHUB_INSTANCES)}")
    
    twitter_count = check_twitter()
    weibo_count = check_weibo()
    
    print(f"\nDONE! Twitter: {twitter_count}, Weibo: {weibo_count}")
