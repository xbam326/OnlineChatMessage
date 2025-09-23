from enum import IntEnum
import uuid


OPERATION_CODES = {"CREATE": 1, "JOIN": 2, "LEAVE": 3}


class STATE_CODE(IntEnum):
    REQUEST = 0
    ACCEPTED = 1
    CREATED = 2
    SUCCESS = 3
    DENIED = 4


STATUS_CODES = {
    "SUCCESS": "200",
    "CREATED": "201",
    "ACCEPTED": "202",
    "ROOM_NOT_FOUND": "404",
    "ROOM_EXISTS": "409",
    "USERNAME_EXISTS": "430",
    "SERVER_FULL": "503",
}


class User:
    def __init__(self, username):
        self.username = username
        self.address = None
        self.uuid = str(uuid.uuid4())


def build_client_message_for_udp(username, token, message):
    # UTF-8エンコード
    username_bytes = username.encode("utf-8")
    token_bytes = token.encode("utf-8")
    message_bytes = message.encode("utf-8")

    # 制限チェック
    if len(username_bytes) > 2**8:
        raise ValueError("Username too long (max 28 bytes)")
    if len(token_bytes) > 2**8:
        raise ValueError("Token too long (max 28 bytes)")
    if len(message_bytes) > 2**29:
        raise ValueError("Message too long (max 229 bytes)")

    # ヘッダー部分
    usernamelen = len(username_bytes).to_bytes(1, "big")
    tokenlen = len(token_bytes).to_bytes(1, "big")

    # ヘッダー(2 bytes) + ボディ
    header = usernamelen + tokenlen
    body = username_bytes + token_bytes + message_bytes

    return header + body


def build_server_message_for_udp(username, message):
    # UTF-8エンコード
    username_bytes = username.encode("utf-8")
    token_bytes = "".encode("utf-8")
    message_bytes = message.encode("utf-8")

    # 制限チェック
    if len(username_bytes) > 2**8:
        raise ValueError("Username too long (max 28 bytes)")
    if len(token_bytes) > 2**8:
        raise ValueError("Token too long (max 28 bytes)")
    if len(message_bytes) > 2**29:
        raise ValueError("Message too long (max 229 bytes)")

    # ヘッダー部分
    usernamelen = len(username_bytes).to_bytes(1, "big")
    tokenlen = len(token_bytes).to_bytes(1, "big")

    # ヘッダー(2 bytes) + ボディ
    header = usernamelen + tokenlen
    body = username_bytes + token_bytes + message_bytes

    return header + body


def process_message_from_udp(data):
    usermelon = data[0]
    tokenmelon = data[1]
    username = data[2 : usermelon + 2].decode("utf-8")
    token = data[usermelon + 2 : usermelon + tokenmelon + 2].decode("utf-8")
    message = data[usermelon + tokenmelon + 2 :].decode("utf-8")
    return username, token, message


def build_message_for_tcrp(roomname, operation, state, payload):
    # UTF-8エンコード
    roomname_bytes = roomname.encode("utf-8")
    payload_bytes = payload.encode("utf-8")

    # 制限チェック
    if len(roomname_bytes) > 2**8:
        raise ValueError("Room name too long (max 28 bytes)")
    if len(payload_bytes) > 2**29:
        raise ValueError("Payload too long (max 229 bytes)")

    # ヘッダー部分
    roomnamelen = len(roomname_bytes).to_bytes(1, "big")
    op = operation.to_bytes(1, "big")
    st = state.to_bytes(1, "big")
    payloadlen = len(payload_bytes).to_bytes(29, "big")

    # ヘッダー(32 bytes) + ボディ
    header = roomnamelen + op + st + payloadlen
    body = roomname_bytes + payload_bytes

    return header + body


def parse_message_from_tcrp(data):
    if len(data) < 32:
        roomnamelen = int.from_bytes(data[0:1], "big")
        print(f"roomnamelen: {roomnamelen}")
        operation = int.from_bytes(data[1:2], "big")
        print(f"operation: {operation}")
        state = int.from_bytes(data[2:3], "big")
        print(f"state: {state}")
        payloadlen = int.from_bytes(data[3:32], "big")
        print(f"payloadlen: {payloadlen}")

        raise ValueError("Data too short for TCRP header")

    # ヘッダーの読み取り
    roomnamelen = int.from_bytes(data[0:1], "big")
    operation = int.from_bytes(data[1:2], "big")
    state = int.from_bytes(data[2:3], "big")
    payloadlen = int.from_bytes(data[3:32], "big")

    # ボディの取り出し位置
    body = data[32:]

    if len(body) < roomnamelen + payloadlen:
        raise ValueError("Data too short for declared body length")

    # ルーム名
    roomname_bytes = body[:roomnamelen]
    roomname = roomname_bytes.decode("utf-8", errors="replace")

    # ペイロード
    payload_bytes = body[roomnamelen : roomnamelen + payloadlen]
    payload = payload_bytes.decode("utf-8", errors="replace")

    return roomname, operation, state, payload


def check_token(token, address, chatrooms):
    for chatroom in chatrooms:
        for user in chatroom.users:
            if user.uuid == token:
                user.address = address
                return chatroom


def find_chatroom(roomname, chatrooms):
    for chatroom in chatrooms:
        if chatroom.roomname == roomname:
            return chatroom
    return None


def is_exists_username_in_chatroom(username, chatroom):
    for user in chatroom.users:
        if user.username == username:
            return True
    return False


def add_user_to_chatroom(chatroom, username):
    new_user = User(username)
    chatroom.users.append(new_user)
    return new_user
