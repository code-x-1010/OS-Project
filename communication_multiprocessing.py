from multiprocessing.connection import Listener, Client, wait
import time
import select

class Player:
    def __init__(self,name) -> None:
        self.name = name
        self.bullets = 1
        self.hand = []
        self.alive = True

    def show_hands(self):
        print(self.hand)
        
def handling_connections(addr, min_conn=1, max_conn=4, timeout=0): 
    time_taken =0
    conns = {}
    Server = Listener(addr)
    sock = Server._listener._socket
    start_time=0
    print("Accepting Connections")
    while(time_taken < timeout):
        # escape with maximum connections reached
        if(len(conns) == max_conn):
            print("maximum clients joined")
            broadcast(conns.values(), "Maximum players joined")
            break
        # managing timer if minimum clients have joined
        if(len(conns) >= min_conn):
            if(not start_time):
                print(f"The connecting phase will end in {timeout} seconds")
                start_time = time.time()
            else:
                curr_time = time.time()
                time_taken = curr_time - start_time
        
        readable, _, _ = select.select([sock], [], [], 0) # avoid the blocking nature of accept
        if sock in readable: 
            conn = Server.accept()
            p_name = conn.recv()
            while(p_name in conns.keys()):
                conn.send("Give a different name, already in use:")
                p_name = conn.recv()
            conn.send("Connected")
            player = Player(p_name)
            conn.send(player)
            conns[player] = conn
            print(f"Connection Successful for player [{player.name}]")
    
    return conns

def send_to(conn, msg):
    conn.send(msg)

def recv_from(conn):
    return conn.recv()

def broadcast(conns, msg):
    for conn in conns:
        send_to(conn, "[BROADCAST] "+msg)

