from multiprocessing.connection import Client, wait
import sys
import communication_multiprocessing as c
import select

def listen(conn):
    global player
    try:
        msg = conn.recv()
        print(msg)
        # responds if the server requests the player
        if '['+player.name+']' in msg: 
            if "Input" in msg:
                response = input().strip()
                conn.send(response)
            if "[SEND INFO]" in msg:
                conn.send(player)
                player = conn.recv()
            if "[LOST]" in msg:
                player.roullette()
                conn.send(player.alive)
            if "[PLAY]" in msg:
                while True:
                    response = input().strip().split(",")
                    if len(response)>0 and len(response)<4:
                        break
                    else:
                        print("Wrong format")
                        print(msg)
                conn.send(response)
    except EOFError: 
            print("Server closed the connection\nClosing the Client....")
            sys.exit(0)# closes the client process if the connection is closed
    except KeyboardInterrupt: sys.exit(0) # close the process due to keyboard interupt
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
    global player
    conn, player = connect()
    # listens the connection for messages
    while True:
        listen(conn)
        
        
    

