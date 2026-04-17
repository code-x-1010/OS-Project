from multiprocessing.connection import Client, wait
import sys

def listen(c,p):
    try:
        msg = c.recv()
        print(msg)

        # sends response if requested from server
        if '['+p.name+']' in msg and "Input" in msg:
            response = input().strip()
            c.send(response)

    # closes the client process if the connection is closed
    except EOFError: 
        print("Server closed the connection\nClosing the Client....")
        sys.exit(0)
    except:
        pass

def connect():
    # Establishing connection with server
    conn = Client(("127.0.0.1",6000))
    print("Trying to connect")
    print("Input Player name:")
    while True:
        p_name = input().strip()
        conn.send(p_name)
        msg = conn.recv()
        if "connected" in msg.lower():
            p = conn.recv()
            print("Joined the Server")
            break
        print(msg)
    
    return conn, p

if __name__ == "__main__":
    conn, player = connect()
    # listens the connection for messages
    while True:
        listen(conn, player)
