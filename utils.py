def process_data(data):
  usermelon = data[0]
  username = data[1:usermelon+1].decode('utf-8')
  message = data[usermelon+1:].decode('utf-8')
  return username, message