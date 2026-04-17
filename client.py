from xmlrpc.client import ServerProxy
import sys


def listen(proxy, player_name):
    try:
        msg = proxy.fetch(player_name, 25)
        if msg is None:
            return
        print(msg)

        if '[' + player_name + ']' in msg and "Input" in msg:
            response = input().strip()
            proxy.push(player_name, response)

    except (ConnectionError, OSError):
        print("Server closed the connection\nClosing the Client....")
        sys.exit(0)
    except Exception:
        pass


proxy = ServerProxy("http://127.0.0.1:6000", allow_none=True)
print("Trying to connect")
print("Input Player name:")
while True:
    p_name = input().strip()
    try:
        msg = proxy.join(p_name)
    except (ConnectionError, OSError) as e:
        print(f"Could not reach server: {e}")
        sys.exit(1)
    if "connected" in msg.lower():
        print("Joined the Server")
        break
    print(msg)

while True:
    listen(proxy, p_name)
