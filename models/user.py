import uuid
import datetime


class User:
    def __init__(self, username):
        self.username = username
        self.address = None
        self.uuid = str(uuid.uuid4())
        self.last_message_time = datetime.datetime.now()

    def update_last_message_time(self):
        self.last_message_time = datetime.datetime.now()

    def update_address(self, address):
        self.address = address

    def is_inactive(self, timeout_seconds):
        """指定された秒数以上メッセージを送信していない場合Trueを返す"""
        if self.last_message_time:
            time_diff = (datetime.datetime.now() - self.last_message_time).total_seconds()
            return time_diff > timeout_seconds
        return False