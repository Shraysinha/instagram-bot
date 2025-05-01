from instagrapi import Client
import random
import requests
import os
import base64
import json

# Load the comment source URL from environment variable
COMMENT_SOURCE_URL = os.getenv("COMMENT_SOURCE_URL")

def fetch_comments():
    """Fetches a list of comments from the COMMENT_SOURCE_URL"""
    response = requests.get(COMMENT_SOURCE_URL)
    return [line.strip() for line in response.text.splitlines() if line.strip()]

def load_target_users(path="target_users.txt"):
    """Loads target Instagram usernames from a text file"""
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def decode_session(b64_session):
    """Decodes a base64-encoded session JSON string into a Python dict"""
    session_json = base64.b64decode(b64_session).decode()
    return json.loads(session_json)

def load_bot_accounts(path="bot_accounts.json"):
    """Loads bot accounts and retrieves session values from secrets"""
    with open(path, "r") as f:
        bots = json.load(f)
        for bot in bots:
            # Extract secret name from string like "${{ secrets.BOT1_SESSION }}"
            secret_template = bot["session_b64"]
            secret_name = secret_template.replace("${{ secrets.", "").replace(" }}", "")
            session_b64 = os.getenv(secret_name)

            if not session_b64:
                raise ValueError(f"Missing environment variable: {secret_name}")

            bot["session_b64"] = session_b64
        return bots

def login_with_session(session):
    """Logs in using a decoded session object"""
    cl = Client()
    cl.load_settings(session)
    cl.login_by_sessionid(session["sessionid"])
    return cl

def main():
    target_users = load_target_users()
    comments = fetch_comments()
    bot_accounts = load_bot_accounts()

    for bot in bot_accounts:
        print(f"\n🔐 Logging in as: {bot['name']}")
        try:
            session_data = decode_session(bot["session_b64"])
            cl = login_with_session(session_data)

            for username in target_users:
                try:
                    user_id = cl.user_id_from_username(username)
                    media = cl.user_medias(user_id, 1)[0]

                    cl.media_like(media.id)
                    comment = random.choice(comments)
                    cl.media_comment(media.id, comment)
                    print(f"✅ [{bot['name']}] liked & commented on {username}: {comment}")
                except Exception as e:
                    print(f"❌ [{bot['name']}] Failed for {username}: {e}")
        except Exception as e:
            print(f"❌ Could not log in as {bot['name']}: {e}")

if __name__ == "__main__":
    main()
