import sys
import socket
import random
import threading
import time

import utils

tcp_sock = None
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
token = None
username = None
roomname = None


address = input("Type in the server's address to connect to: ")
if address == "":
    address = "localhost"
tcp_server_port = 9001
udp_server_port = 9002
port = random.randint(9003, 9100)


def send_messages():
    print("Ready to send messages. Type your message:")
    while True:
        message = input()
        # 入力行をクリア
        print("\033[1A\033[K", end="")
        udp_sock.sendto(
            utils.build_client_message_for_udp(username, token, message),
            (address, udp_server_port),
        )
        time.sleep(0.1)


def receive_messages():
    while True:
        data, _ = udp_sock.recvfrom(4096)
        username, _, message = utils.process_message_from_udp(data)
        print(f"{username}: {message}")


def connect_tcp():
    global username, token, tcp_sock
    try:
        # 接続後、サーバとクライアントが相互に読み書きができるようになります
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((address, tcp_server_port))
        print(f"Connected to server {address} on TCP port {tcp_server_port}")
    except socket.error as err:
        print(err)
        sys.exit(1)


def disconnect_tcp():
    global tcp_sock
    tcp_sock.close()
    print("Disconnected from server.")


def select_operation():
    operation = input("Select operation - Create room (1) / Join room (2): ")
    return operation


def create_chatroom():
    global roomname, username, token, tcp_sock
    username = input("Enter your username: ")
    roomname = input("Enter room name to create: ")
    tcp_sock.send(
        utils.build_message_for_tcrp(
            roomname,
            utils.OPERATION_CODES["CREATE"],
            utils.STATE_CODE.REQUEST,
            username,
        )
    )
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    if payload == utils.STATUS_CODES["ACCEPTED"]:
        print(f"Creating room: {roomname}")
    else:
        print(f"Failed to accept room: {roomname}")
        sys.exit(1)
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    if state == utils.STATE_CODE.CREATED:
        token = payload
        print(f"Room '{roomname}' created successfully!")
    else:
        print(f"Failed to create room: {roomname}")
        sys.exit(1)


def join_chatroom():
    global roomname, username, token
    username = input("Enter your username: ")
    roomname = input("Enter room name to join: ")
    tcp_sock.send(
        utils.build_message_for_tcrp(
            roomname,
            utils.OPERATION_CODES["JOIN"],
            utils.STATE_CODE.REQUEST,
            username,
        )
    )
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    if payload == utils.STATUS_CODES["ACCEPTED"]:
        print(f"Joining room: {roomname}")
    else:
        print(f"Failed to accept room: {roomname}")
        sys.exit(1)
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    if state == utils.STATE_CODE.SUCCESS:
        token = payload
        print(f"Successfully joined room '{roomname}'!")
    else:
        print(f"Failed to join room: {roomname}")
        sys.exit(1)


def exit():
    global tcp_sock, udp_sock, roomname, username
    tcp_sock.send(
        utils.build_message_for_tcrp(
            roomname,
            utils.OPERATION_CODES["LEAVE"],
            utils.STATE_CODE.REQUEST,
            username,
        )
    )
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    if payload == utils.STATUS_CODES["ACCEPTED"]:
        print(f"Leaving room: {roomname}")
    else:
        print(f"Failed to leave room: {roomname}")
        sys.exit(1)
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    if state == utils.STATE_CODE.SUCCESS:
        print(f"Successfully leaving room '{roomname}'!")
    else:
        print(f"Failed to leave room: {roomname}")

    print("\nDisconnected from server.")


def main():
    connect_tcp()
    operation = select_operation()
    if operation not in ["1", "2"]:
        print("Invalid operation")
        sys.exit(1)
    if operation == str(utils.OPERATION_CODES["CREATE"]):
        create_chatroom()
    if operation == str(utils.OPERATION_CODES["JOIN"]):
        join_chatroom()
    disconnect_tcp()
    try:
        send_thread = threading.Thread(target=send_messages, daemon=True)
        send_thread.start()
        receive_messages()
    except KeyboardInterrupt:
        connect_tcp()
        exit()
        tcp_sock.close()
        udp_sock.close()


if __name__ == "__main__":
    main()
