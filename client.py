import sys
import socket
import random
import threading
import time

import utils

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
token = None
username = None


address = input("Type in the server's address to connect to: ")
if address == "":
    address = "localhost"
tcp_server_port = 9001
udp_server_port = 9002
port = random.randint(9003, 9100)


# メッセージを送信
def message_output():
    while True:
        message = input("Type your message:")
        # print(username, token)
        udp_sock.sendto(
            utils.build_client_message_for_udp(username, token, message),
            (address, udp_server_port),
        )
        # print("Send {} bytes".format(sent))
        time.sleep(0.1)


# # 応答を受信
def message_input():
    while True:
        data, _server = udp_sock.recvfrom(4096)
        username, _token, message = utils.process_message_from_udp(data)
        print(f"{username}: {message}")
        # print(token)


def create_chatroom():
    global username, token
    try:
        # 接続後、サーバとクライアントが相互に読み書きができるようになります
        tcp_sock.connect((address, tcp_server_port))
        print("connecting to {} port {}".format(address, tcp_server_port))
    except socket.error as err:
        print(err)
        sys.exit(1)

    username = input("What is your username: ")
    print(username)
    roomname = input("What is your roomname: ")
    print(roomname)
    tcp_sock.send(
        utils.build_message_for_tcrp(
            roomname, utils.OPERATION_CODE.CREATE, utils.STATE_CODE.REQUEST, username
        )
    )
    data = tcp_sock.recv(4096)
    print("received {} bytes from {}".format(len(data), address))
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    print(
        f"roomname: {roomname}, operation: {operation}, state: {state}, payload: {payload}"
    )
    if payload == utils.STATUS_CODES["ACCEPTED"]:
        print(f"Creating room: {roomname}")
    else:
        print(f"Failed to accept room: {roomname}")
        sys.exit(1)
    data = tcp_sock.recv(4096)
    roomname, operation, state, payload = utils.parse_message_from_tcrp(data)
    print(
        f"roomname: {roomname}, operation: {operation}, state: {state}, payload: {payload}"
    )
    if state == utils.STATE_CODE.CREATED:
        token = payload
        print(f"Room created successfully with token: {token}")
    else:
        print(f"Failed to create room: {roomname}")
        sys.exit(1)


def main():
    create_chatroom()
    # message_output()
    message_output_thread = threading.Thread(target=message_output, daemon=True)
    message_output_thread.start()
    message_input()

    # print(f"roomname: {roomname}, operation: {operation}, state: {state}, payload: {payload}")
    # try:
    #     message_output_thread = threading.Thread(target=message_output, args=(username,), daemon=True)
    #     message_output_thread.start()
    #     # message_input_thread = threading.Thread(target=message_input, daemon=True)
    #     # message_input_thread.start()
    #     message_input()

    # except Exception as e:
    #     print('An error occurred: {}'.format(e))

    # finally:
    #     print('closing socket')
    #     sock.close()


if __name__ == "__main__":
    main()
