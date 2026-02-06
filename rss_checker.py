import feedparser
import requests
import json
import os
from datetime import datetime

# ===== 配置区域 =====
# 要监控的推特用户(可以添加多个)
TWITTER_USERS = [
    "hgsc001",      # 例子:埃隆马斯克
    # "OpenAI",      # 取消注释来添加更多
    # "sama",
]

# 企业微信 Webhook(从环境变量读取)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# 记录文件
SENT_FILE = 'sent_items.txt'
# ====================

def load_sent_items():
    """加载已发送的条目ID"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_sent_item(item_id):
    """保存已发送的条目ID"""
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{item_id}\n")

def send_to_wechat(title, link, author):
    """发送消息到企业微信"""
    if not WEBHOOK_URL:
        print("错误: 未设置 WEBHOOK_URL")
        return False
    
    # 清理标题(去掉 HTML 标签等)
    title = title.replace('<', '&lt;').replace('>', '&gt;')
    
    # 构造消息内容
    content = f"🐦 【{author}】发推了\n\n{title}\n\n🔗 {link}"
    
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
                print(f"✅ 发送成功: {title[:30]}...")
                return True
            else:
                print(f"❌ 发送失败: {result}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False

def check_rss():
    """检查 RSS 更新"""
    sent_items = load_sent_items()
    new_count = 0
    
    for username in TWITTER_USERS:
        rss_url = f"https://rsshub.app/twitter/user/{username}"
        
        try:
            print(f"\n📡 检查 @{username} 的推文...")
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                print(f"⚠️  无法获取 RSS 内容,可能是网络问题或 RSSHub 限流")
                continue
            
            # 只处理最新的3条(避免首次运行发送太多)
            for entry in feed.entries[:3]:
                item_id = entry.get('id', entry.link)
                
                if item_id not in sent_items:
                    title = entry.get('title', '无标题')
                    link = entry.get('link', '')
                    author = username
                    
                    print(f"🆕 发现新推文: {title[:50]}...")
                    
                    if send_to_wechat(title, link, author):
                        save_sent_item(item_id)
                        new_count += 1
                    
                    # 避免发送太快,稍微延迟
                    import time
                    time.sleep(2)
                else:
                    print(f"⏭️  跳过已发送: {entry.get('title', '')[:30]}...")
                    
        except Exception as e:
            print(f"❌ RSS 解析错误: {e}")
    
    print(f"\n✨ 完成! 本次发送了 {new_count} 条新推文")

if __name__ == '__main__':
    print(f"🚀 开始检查 RSS 更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    check_rss()
```

4. 点击 "Commit changes"

### 第五步:配置企业微信 Webhook Secret

1. 在仓库页面,点击 "Settings"(设置)
2. 左侧菜单找到 "Secrets and variables" → "Actions"
3. 点击 "New repository secret"
4. 填写:
   - Name: `WEBHOOK_URL`
   - Secret: **粘贴你的企业微信 Webhook 地址**
```
   例如: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx-xxxx-xxxx
