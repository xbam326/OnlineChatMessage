import socket
import random
import threading

import utils

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

address = input("Type in the server's address to connect to: ")
if address == '':
  address = 'localhost'
server_port = 9001
port = random.randint(9002,9100)

def create_message(username: str, message: str) -> bytes:
    username_bytes = username.encode('utf-8')
    usernamelen = len(username_bytes).to_bytes(1, 'big')
    return usernamelen + username_bytes + message.encode('utf-8')

# メッセージを送信
def message_output(username):
    while True:
        message = input()
        sent = sock.sendto(create_message(username, message), (address, server_port))
        print('Send {} bytes'.format(sent))

# 応答を受信
def message_input():
    while True:
        data, _server = sock.recvfrom(4096)
        username, message = utils.process_data(data)
        print(f"{username}: {message}")
        print('What is your message?')

def main():
    # 空の文字列も0.0.0.0として使用できます。
    sock.bind((address,port))
    print('cliemt start on {}:{}'.format(address,port))
    username = input("What is your username: ")
    print(username)
    print("What is your message?")
    try:
        message_output_thread = threading.Thread(target=message_output, args=(username,), daemon=True)
        message_output_thread.start()
        # message_input_thread = threading.Thread(target=message_input, daemon=True)
        # message_input_thread.start()
        message_input()

    except Exception as e:
        print('An error occurred: {}'.format(e))


    finally:
        print('closing socket')
        sock.close()

if __name__ == "__main__":
    main()