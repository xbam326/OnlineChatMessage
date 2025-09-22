import socket
import datetime
import threading

import utils

# AF_INETを使用し、TCPソケットを作成
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# AF_INETを使用し、UDPソケットを作成
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = "localhost"

tcp_server_port = 9001
udp_server_port = 9002

tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

tcp_sock.bind((server_address, tcp_server_port))
tcp_sock.listen(1)
udp_sock.bind((server_address, udp_server_port))

print("starting up on tcp port {}".format(tcp_server_port))
print("starting up on udp port {}".format(udp_server_port))

chatrooms = []


def main():
    make_chatroom_thread = threading.Thread(target=make_chatroom)
    make_chatroom_thread.start()
    chat()


def make_chatroom():
    while True:
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
        if operation == utils.OPERATION_CODES["CREATE"]:
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
        if operation == utils.OPERATION_CODES["JOIN"]:
            chatroom = utils.find_chatroom(roomname, chatrooms)
            print("chatroom", chatroom.roomname)
            print("chatroom", chatroom.users)
            if chatroom is None:
                print(f"Chat room '{roomname}' does not exist. Join request denied.")
                connection.send(
                    utils.build_message_for_tcrp(
                        roomname,
                        operation,
                        utils.STATE_CODE.DENIED,
                        utils.STATUS_CODES["ROOM_NOT_FOUND"],
                    )
                )
                continue
            if utils.is_exists_username_in_chatroom(username, chatroom):
                print(
                    f"Username '{username}' already exists in chat room '{chatroom.roomname}'. Join request denied."
                )
                connection.send(
                    utils.build_message_for_tcrp(
                        roomname,
                        operation,
                        utils.STATE_CODE.DENIED,
                        utils.STATUS_CODES["USERNAME_EXISTS"],
                    )
                )
                continue
            new_user = utils.add_user_to_chatroom(chatroom, username, client_address)
            print(
                f"User '{new_user.username}' joined chat room '{chatroom.roomname}' from {new_user.address} with UUID {new_user.uuid}"
            )
            connection.send(
                utils.build_message_for_tcrp(
                    roomname,
                    operation,
                    utils.STATE_CODE.SUCCESS,
                    new_user.uuid,
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
            continue
        print(f"Chatroom: {chatroom.roomname}, {username}: {message}")
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
