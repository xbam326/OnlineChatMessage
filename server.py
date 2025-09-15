import socket
import datetime

import utils

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = 'localhost'
server_port = 9001
print('starting up on port {}'.format(server_port))

target_list = []

def main():
  # ソケットを特殊なアドレス0.0.0.0とポート9001に紐付け
  sock.bind((server_address, server_port))

  while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)

    print('received {} bytes from {}'.format(len(data), address))
    username, message = utils.process_data(data)
    print('username: {}, message: {}'.format(username, message))
    now = datetime.datetime.now()
    print('Time: {}'.format(now.strftime('%Y-%m-%d %H:%M:%S')))

    manage_target_list(username, address, now)
    send_message(data)

def manage_target_list(username, address, now):
  # すでに存在する場合は更新、存在しない場合は追加
  is_found = False
  # 配列をコピーしてループすることで、削除しながらループできる
  for target in target_list[:]:
    if target['username'] == username and target['address'] == address:
      target['last_message_date'] = now
      is_found = True
    if target['last_message_date'] < now - datetime.timedelta(minutes=3):
      target_list.remove(target)
      print('Removed inactive user: {}'.format(target['username']))
  
  if not is_found:   
    target_list.append({
      'username': username,
      'address': address,
      'last_message_date': now
    })

def send_message(data):
  for target in target_list[:]:
    try:
      sent = sock.sendto(data, target['address'])
      print('sent {} bytes to {}'.format(sent, target['address']))
    except Exception as e:
      print('Error sending to {}: {}'.format(target['address'], e))
      target_list.remove(target)
      print('Removed user due to error: {}'.format(target['username']))




if __name__ == "__main__":
  main()