import socket
import datetime

import utils

# AF_INETを使用し、TCPソケットを作成
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# AF_INETを使用し、UDPソケットを作成
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = "localhost"

tcp_server_port = 9001
udp_server_port = 9002

tcp_sock.bind((server_address, tcp_server_port))
tcp_sock.listen(1)
udp_sock.bind((server_address, udp_server_port))

print("starting up on tcp port {}".format(tcp_server_port))
print("starting up on udp port {}".format(udp_server_port))

chatrooms = []


def main():
    make_chatroom()
    chat()


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
    global tcp_sock
    # while True:
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
    host = utils.User(username, client_address)
    chatroom = ChatRoom(roomname, host)
    chatrooms.append(chatroom)
    print(
        f"Chat room '{chatroom.roomname}' created by {chatroom.host.username} at {chatroom.host.address} with UUID {chatroom.host.uuid}"
    )
    connection.send(
        utils.build_message_for_tcrp(
            roomname, operation, utils.STATE_CODE.CREATED, chatroom.host.uuid
        )
    )


def chat():
    while True:
        print("\nwaiting to receive message")
        data, address = udp_sock.recvfrom(4096)
        now = datetime.datetime.now()
        print("received {} bytes from {}".format(len(data), address))
        username, token, message = utils.process_message_from_udp(data)
        print(f"username: {username}, token: {token}, message: {message}, now: {now}")
        chatroom = utils.check_token(token, address, chatrooms)
        if chatroom is None:
            print(f"Invalid token: {token}. Message ignored.")
            udp_sock.sendto(
                utils.build_server_message_for_udp("System", "Invalid Token"), address
            )
        for user in chatroom.users:
            udp_sock.sendto(
                utils.build_server_message_for_udp(username, message), user.address
            )


class ChatRoom:
    def __init__(self, roomname, host):
        self.roomname = roomname
        self.host = host
        self.users = [host]


if __name__ == "__main__":
    main()
