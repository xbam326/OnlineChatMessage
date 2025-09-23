from .user import User


class Chatroom:
    def __init__(self, roomname, host):
        self.roomname = roomname
        self.host = host
        self.users = [host]

    def find_user(self, username):
        """ユーザー名でユーザーを検索"""
        for user in self.users:
            if user.username == username:
                return user
        return None

    def find_user_by_token(self, token):
        """トークン（UUID）でユーザーを検索"""
        for user in self.users:
            if user.uuid == token:
                return user
        return None

    def add_user(self, username):
        """新しいユーザーを追加"""
        new_user = User(username)
        self.users.append(new_user)
        return new_user

    def remove_user(self, username):
        """ユーザーを削除"""
        user = self.find_user(username)
        if user:
            self.users.remove(user)
            return user
        return None

    def is_username_exists(self, username):
        """ユーザー名が既に存在するか確認"""
        return any(user.username == username for user in self.users)

    def is_host(self, username):
        """指定されたユーザーがホストか確認"""
        return self.host.username == username

    def get_inactive_users(self, timeout_seconds):
        """非アクティブなユーザーのリストを取得"""
        inactive_users = []
        for user in self.users:
            if user.is_inactive(timeout_seconds):
                inactive_users.append(user)
        return inactive_users

    def update_user_activity(self, token, address):
        """ユーザーのアクティビティを更新"""
        user = self.find_user_by_token(token)
        if user:
            user.update_address(address)
            user.update_last_message_time()
            return True
        return False