import os

is_dev = bool(os.getenv('dev', False))
bot_token = os.getenv("bot_token")
webhook_token = os.getenv("webhook_token")
assemblyai_key = os.getenv("assemblyai_key")
gigachat_secret = os.getenv("gigachat_secret")
web_url = os.getenv("web_url")
admin_chat = int(os.getenv("admin_chat"))

host = os.getenv("IP")
port = int(os.getenv("PORT"))

mysql_server = os.getenv("mysql_server")
mysql_user = os.getenv("mysql_user")
mysql_password = os.getenv("mysql_pw")
