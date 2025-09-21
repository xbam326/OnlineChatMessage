from enum import IntEnum

class OPERATION_CODE(IntEnum):
    CREATE = 0
    JOIN = 1

class STATE_CODE(IntEnum):
    REQUEST = 0
    ACCEPTED = 1
    CREATED = 2

STATUS_CODES = {
    "CREATED": "201",
    "ACCEPTED": "202",
    "ROOM_EXISTS": "409",
    "SERVER_FULL": "503"
}


def process_data(data):
  usermelon = data[0]
  username = data[1:usermelon+1].decode('utf-8')
  message = data[usermelon+1:].decode('utf-8')
  return username, message

def build_message_for_tcrp(roomname,operation,state,payload):
# UTF-8エンコード
    roomname_bytes = roomname.encode('utf-8')
    payload_bytes = payload.encode('utf-8')

    # 制限チェック
    if len(roomname_bytes) > 2**8:
        raise ValueError("Room name too long (max 28 bytes)")
    if len(payload_bytes) > 2**29:
        raise ValueError("Payload too long (max 229 bytes)")

    # ヘッダー部分
    roomnamelen = len(roomname_bytes).to_bytes(1, 'big')
    op = operation.to_bytes(1, 'big')
    st = state.to_bytes(1, 'big')
    payloadlen = len(payload_bytes).to_bytes(29, 'big')

    # ヘッダー(32 bytes) + ボディ
    header = roomnamelen + op + st + payloadlen
    body = roomname_bytes + payload_bytes

    return header + body

def parse_message_from_tcrp(data):
    if len(data) < 32:
        raise ValueError("Data too short for TCRP header")
    
    # ヘッダーの読み取り
    roomnamelen = int.from_bytes(data[0:1], 'big')
    operation = int.from_bytes(data[1:2], 'big')
    state = int.from_bytes(data[2:3], 'big')
    payloadlen = int.from_bytes(data[3:32], 'big')

    # ボディの取り出し位置
    body = data[32:]

    if len(body) < roomnamelen + payloadlen:
        raise ValueError("Data too short for declared body length")

    # ルーム名
    roomname_bytes = body[:roomnamelen]
    roomname = roomname_bytes.decode('utf-8', errors='replace')

    # ペイロード
    payload_bytes = body[roomnamelen:roomnamelen + payloadlen]
    payload = payload_bytes.decode('utf-8', errors='replace')

    return roomname, operation, state, payload