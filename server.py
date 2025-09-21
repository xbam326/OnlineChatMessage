import socket
import datetime
import uuid
import utils

# AF_INETを使用し、TCPソケットを作成
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = "localhost"
server_port = 9001
print("starting up on port {}".format(server_port))

target_list = []


def main():
    make_chatroom()


def manage_target_list(username, address, now):
    # すでに存在する場合は更新、存在しない場合は追加
    is_found = False
    # 配列をコピーしてループすることで、削除しながらループできる
    for target in target_list[:]:
        if target["username"] == username and target["address"] == address:
            target["last_message_date"] = now
            is_found = True
        if target["last_message_date"] < now - datetime.timedelta(minutes=3):
            target_list.remove(target)
            print("Removed inactive user: {}".format(target["username"]))

    if not is_found:
        target_list.append(
            {"username": username, "address": address, "last_message_date": now}
        )


def send_message(data):
    for target in target_list[:]:
        try:
            sent = sock.sendto(data, target["address"])
            print("sent {} bytes to {}".format(sent, target["address"]))
        except Exception as e:
            print("Error sending to {}: {}".format(target["address"], e))
            target_list.remove(target)
            print("Removed user due to error: {}".format(target["username"]))


def make_chatroom():
    # ソケットを特殊なアドレス0.0.0.0とポート9001に紐付け
    tcp_sock.bind((server_address, server_port))
    tcp_sock.listen(1)

    while True:
        print("\nwaiting to receive message")
        connection, client_address = tcp_sock.accept()
        print("connection", connection)
        print("client_address", client_address)
        data = connection.recv(4096)

        print("received {} bytes from {}".format(len(data), client_address))
        roomname, operation, state, username = utils.parse_message_from_tcrp(data)
        print(
            f"roomname: {roomname}, operation: {operation}, state: {state}, username: {username}"
        )
        connection.send(
            utils.build_message_for_tcrp(
                roomname,
                operation,
                utils.STATE_CODE.ACCEPTED,
                utils.STATUS_CODES["ACCEPTED"],
            )
        )
        host = User(username, client_address)
        chatroom = ChatRoom(roomname, host)
        print(
            f"Chat room '{chatroom.roomname}' created by {chatroom.host.username} at {chatroom.host.address} with UUID {chatroom.host.uuid}"
        )
        connection.send(
            utils.build_message_for_tcrp(
                roomname, operation, utils.STATE_CODE.CREATED, chatroom.host.uuid
            )
        )


class ChatRoom:
    def __init__(self, roomname, host):
        self.roomname = roomname
        self.host = host
        self.users = [host]


class User:
    def __init__(self, username, address):
        self.username = username
        self.address = address
        self.uuid = str(uuid.uuid4())


if __name__ == "__main__":
    main()
