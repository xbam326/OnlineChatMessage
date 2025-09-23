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

print("Starting TCP server on port {}".format(tcp_server_port))
print("Starting UDP server on port {}".format(udp_server_port))

chatrooms = []


def main():
    tcp_handler_thread = threading.Thread(target=handle_tcp_connections)
    tcp_handler_thread.start()
    handle_udp_messages()


def handle_tcp_connections():
    while True:
        global tcp_sock
        connection, client_address = tcp_sock.accept()
        print("Connection:", connection)
        print("Client address:", client_address)
        data = connection.recv(4096)

        print("Received {} bytes from {}".format(len(data), client_address))
        roomname, operation, state, username = utils.parse_message_from_tcrp(data)
        print(
            f"Room: {roomname}, Operation: {operation}, State: {state}, Username: {username}"
        )
        connection.send(
            utils.build_message_for_tcrp(
                roomname,
                operation,
                utils.STATE_CODE.ACCEPTED,
                utils.STATUS_CODES["ACCEPTED"],
            )
        )
        handle_operation(connection, roomname, operation, username)


def handle_operation(connection, roomname, operation, username):
    if operation == utils.OPERATION_CODES["CREATE"]:
        create_chatroom(connection, roomname, operation, username)
    elif operation == utils.OPERATION_CODES["JOIN"]:
        join_chatroom(connection, roomname, operation, username)
    elif operation == utils.OPERATION_CODES["LEAVE"]:
        print("Leave operation")
        print("Connection:", connection, roomname, operation, username)
        leave_chatroom(connection, roomname, operation, username)


def create_chatroom(connection, roomname, operation, username):
    host = utils.User(username)
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


def join_chatroom(connection, roomname, operation, username):
    chatroom = utils.find_chatroom(roomname, chatrooms)
    print("Chatroom name:", chatroom.roomname)
    print("Chatroom users:", chatroom.users)
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
        return
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
        return
    new_user = utils.add_user_to_chatroom(chatroom, username)
    print(
        f"User '{new_user.username}' joined chat room '{chatroom.roomname}' with UUID {new_user.uuid}"
    )
    connection.send(
        utils.build_message_for_tcrp(
            roomname,
            operation,
            utils.STATE_CODE.SUCCESS,
            new_user.uuid,
        )
    )


def leave_chatroom(connection, roomname, operation, username):
    chatroom = utils.find_chatroom(roomname, chatrooms)
    if chatroom is None:
        print(f"Chat room '{roomname}' does not exist. Leave request denied.")
        connection.send(
            utils.build_message_for_tcrp(
                roomname,
                operation,
                utils.STATE_CODE.DENIED,
                utils.STATUS_CODES["ROOM_NOT_FOUND"],
            )
        )
        return
    user_to_remove = None
    for user in chatroom.users:
        if user.username == username:
            user_to_remove = user
            break
    if user_to_remove is None:
        print(
            f"Username '{username}' not found in chat room '{chatroom.roomname}'. Leave request denied."
        )
        connection.send(
            utils.build_message_for_tcrp(
                roomname,
                operation,
                utils.STATE_CODE.DENIED,
                utils.STATUS_CODES["USERNAME_NOT_FOUND"],
            )
        )
        return
    chatroom.users.remove(user_to_remove)
    print(f"User '{user_to_remove.username}' left chat room '{chatroom.roomname}'")
    connection.send(
        utils.build_message_for_tcrp(
            roomname,
            operation,
            utils.STATE_CODE.SUCCESS,
            utils.STATUS_CODES["SUCCESS"],
        )
    )
    if chatroom.host.username == user_to_remove.username:
        for user in chatroom.users:
            udp_sock.sendto(
                utils.build_server_message_for_udp(
                    "System", "Host has leaved. This chatroom is removed."
                ),
                user.address,
            )
        chatrooms.remove(chatroom)
        print(f"Chat room '{chatroom.roomname}' deleted as it became empty.")


def handle_udp_messages():
    while True:
        print("\nWaiting for UDP message...")
        data, address = udp_sock.recvfrom(4096)
        now = datetime.datetime.now()
        print("Received {} bytes from {}".format(len(data), address))
        username, token, message = utils.process_message_from_udp(data)
        print(f"Username: {username}, Token: {token}, Message: {message}, Time: {now}")
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
