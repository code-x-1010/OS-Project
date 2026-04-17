from multiprocessing.connection import Client, wait

conn = Client(("127.0.0.1",6000))
print("Trying to connect")
print("Input Player name:")
p_name = input().strip()
conn.send(p_name)
while True:
    msg = conn.recv()
    if "connected" in msg.lower():
        print("Joined the Server")
        break
    print(msg)
    user_input = input().strip()
    conn.send(user_input)
