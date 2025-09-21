import sys
import socket
import random
import threading

import utils

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

address = input("Type in the server's address to connect to: ")
if address == "":
    address = "localhost"
server_port = 9001
port = random.randint(9002, 9100)


def create_message(username: str, message: str) -> bytes:
    username_bytes = username.encode("utf-8")
    usernamelen = len(username_bytes).to_bytes(1, "big")
    return usernamelen + username_bytes + message.encode("utf-8")


# メッセージを送信
def message_output(username):
    while True:
        message = input()
        sent = sock.sendto(create_message(username, message), (address, server_port))
        print("Send {} bytes".format(sent))


# 応答を受信
def message_input():
    while True:
        data, _server = sock.recvfrom(4096)
        username, message = utils.process_data(data)
        print(f"{username}: {message}")
        print("What is your message?")


def main():
    try:
        # 接続後、サーバとクライアントが相互に読み書きができるようになります
        sock.connect((address, server_port))
        print("connecting to {} port {}".format(address, server_port))
    except socket.error as err:
        print(err)
        sys.exit(1)

    username = input("What is your username: ")
    print(username)
    roomname = input("What is your roomname: ")
    print(roomname)
    sock.send(
        utils.build_message_for_tcrp(
            roomname, utils.OPERATION_CODE.CREATE, utils.STATE_CODE.REQUEST, username
        )
    )
    data = sock.recv(4096)
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
    data = sock.recv(4096)
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
