from multiprocessing.connection import Client, wait
import sys
import communication_multiprocessing as c
import select

def listen(conn,player):
    try:
        msg = conn.recv()
        print(msg)
        # responds if the server requests the player
        if '['+player.name+']' in msg and "Input" in msg:
            response = input().strip()
            conn.send(response)
    except EOFError: 
            print("Server closed the connection\nClosing the Client....")
            sys.exit(0)# closes the client process if the connection is closed
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
    deck = ["A"]*6+["K"]*6+["Q"]*6+["Joker"]*2
    deck = player.deal_cards(deck)
    print(deck)
    player.roullette()
    # listens the connection for messages
    while True:
        listen(conn, player)
        
        
    

