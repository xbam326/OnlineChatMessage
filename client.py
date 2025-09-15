import socket
import random
import time 

import utils

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

address = input("Type in the server's address to connect to: ")
if address == '':
  address = 'localhost'
server_port = 9001
port = random.randint(9002,9100)

# client_id = random.randint(1000,9999)


def create_message(username: str, message: str) -> bytes:
    username_bytes = username.encode('utf-8')
    usernamelen = len(username_bytes).to_bytes(1, 'big')
    return usernamelen + username_bytes + message.encode('utf-8')

def main():
  # 空の文字列も0.0.0.0として使用できます。
  sock.bind((address,port))
  print('cliemt start on {}:{}'.format(address,port))

  try:
    username = input("What is your username: ")
    print(username)
    message = input("What is youer message: ")
    sent = sock.sendto(create_message(username, message), (address, server_port))
    print('Send {} bytes'.format(sent))
    while True:
      # サーバへのデータ送信
      time.sleep(1)
      # 応答を受信
      print('waiting to receive')
      data, _server = sock.recvfrom(4096)
      username, message = utils.process_data(data)
      print(f"{username}: {message}")


  finally:
    print('closing socket')
    sock.close()

if __name__ == "__main__":
  main()