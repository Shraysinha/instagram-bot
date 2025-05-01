from instagrapi import Client
import os
import base64
import tempfile
import requests
import random

def fetch_comments():
    url = os.getenv("COMMENT_SOURCE_URL")
    if not url:
        raise ValueError("❌ COMMENT_SOURCE_URL environment variable not set.")
    response = requests.get(url)
    response.raise_for_status()
    return [line.strip() for line in response.text.splitlines() if line.strip()]

def load_target_users(file_path="target_users.txt"):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def login_with_session_b64(session_b64):
    session_json = base64.b64decode(session_b64).decode()
    cl = Client()
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_file:
        tmp_file.write(session_json)
        tmp_file_path = tmp_file.name
    cl.load_settings(tmp_file_path)
    cl.get_timeline_feed()  # sanity check to ensure session works
    return cl

def run_bot(bot_name, session_b64, target_users, comments):
    print(f"\n🤖 Logging in as {bot_name}...")
    try:
        cl = login_with_session_b64(session_b64)
    except Exception as e:
        print(f"❌ Failed to login as {bot_name}: {e}")
        return

    for username in target_users:
        try:
            user_id = cl.user_id_from_username(username)
            media_list = cl.user_medias_v1(user_id, 1)
            if not media_list:
                print(f"⚠️ {bot_name}: No media found for {username}. Skipping.")
                continue
            media = media_list[0]
            cl.media_like(media.id)
            comment = random.choice(comments)
            cl.media_comment(media.id, comment)
            print(f"✅ {bot_name} → {username}: {comment}")
        except Exception as e:
            print(f"❌ {bot_name} failed on {username}: {e}")

def main():
    target_users = load_target_users()
    comments = fetch_comments()

    bot_sessions = {
        name: value
        for name, value in os.environ.items()
        if name.startswith("BOT") and name.endswith("_SESSION")
    }

    if not bot_sessions:
        print("❌ No bot sessions found in environment variables (e.g., BOT1_SESSION).")
        return

    for bot_name, session_b64 in bot_sessions.items():
        run_bot(bot_name, session_b64, target_users, comments)

if __name__ == "__main__":
    main()
