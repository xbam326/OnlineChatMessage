import socket
import time
from codes import OPERATION_CODES, STATE_CODES, STATUS_CODES

# ===================
# リトライ関連の関数
# ===================


def retry_with_exponential_backoff(
    func, max_retries=3, initial_delay=1, max_delay=32, backoff_factor=2
):
    """指数バックオフでリトライを行う再帰関数

    Args:
        func: 実行する関数（引数なしでcallable）
        max_retries: 最大リトライ回数
        initial_delay: 初期待機時間（秒）
        max_delay: 最大待機時間（秒）
        backoff_factor: バックオフ係数

    Returns:
        成功した場合は関数の戻り値、失敗した場合はNone
    """
    def attempt(retry_count, delay):
        try:
            result = func()
            return result
        except (socket.error, socket.timeout, ConnectionError) as e:
            if retry_count >= max_retries:
                print(f"Maximum retries ({max_retries}) exceeded. Error: {e}")
                return None

            print(
                f"Connection failed, retrying in {delay} seconds... (attempt {retry_count + 1}/{max_retries})"
            )
            time.sleep(delay)

            # 次のdelayを計算（最大値を超えないように）
            next_delay = min(delay * backoff_factor, max_delay)
            return attempt(retry_count + 1, next_delay)

    return attempt(0, initial_delay)


def send_with_retry(sock, data, max_retries=3, initial_delay=0.5):
    """ソケット送信をリトライ付きで実行"""
    def send_data():
        sock.send(data)
        return True

    return retry_with_exponential_backoff(send_data, max_retries, initial_delay)


def recv_with_retry(sock, buffer_size=4096, max_retries=3, initial_delay=0.5):
    """ソケット受信をリトライ付きで実行"""
    def recv_data():
        data = sock.recv(buffer_size)
        if not data:
            raise ConnectionError("No data received from server")
        return data

    return retry_with_exponential_backoff(recv_data, max_retries, initial_delay)


# ===================
# UDPメッセージ関連の関数
# ===================


def _build_udp_message(username, token, message):
    """UDPメッセージの共通構築関数"""
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


def build_client_message_for_udp(username, token, message):
    """クライアント用UDPメッセージ構築"""
    return _build_udp_message(username, token, message)


def build_server_message_for_udp(username, message):
    """サーバー用UDPメッセージ構築"""
    return _build_udp_message(username, "", message)


def process_message_from_udp(data):
    """UDPメッセージ解析"""
    usermelon = data[0]
    tokenmelon = data[1]
    username = data[2 : usermelon + 2].decode("utf-8")
    token = data[usermelon + 2 : usermelon + tokenmelon + 2].decode("utf-8")
    message = data[usermelon + tokenmelon + 2 :].decode("utf-8")
    return username, token, message


# ===================
# TCRPメッセージ関連の関数
# ===================


def build_message_for_tcrp(roomname, operation, state, payload):
    """TCRPメッセージ構築"""
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
    """TCRPメッセージ解析"""
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


# ===================
# チャットルーム関連のヘルパー関数
# ===================


def check_token(token, address, chatrooms):
    """トークンを確認し、該当するチャットルームを取得"""
    for chatroom in chatrooms:
        if chatroom.update_user_activity(token, address):
            return chatroom
    return None


def find_chatroom(roomname, chatrooms):
    """チャットルーム名でチャットルームを検索"""
    for chatroom in chatrooms:
        if chatroom.roomname == roomname:
            return chatroom
    return None


