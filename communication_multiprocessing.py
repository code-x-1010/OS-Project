from multiprocessing.connection import Listener, Client, wait
import time
import select
import random

class Player:
    def __init__(self,name) -> None:
        self.name = name
        self.bullets = 1
        self.hand = []
        self.alive = True

    def show_hands(self):
        print(self.hand)
    
    def deal_cards(self, deck):
        self.hand = random.sample(deck, k=5) # the 5 cards to deal
        for card in self.hand:
            deck.remove(card)
        return deck # returns the deck with remaining cards
    
    def roullette(self):
        n = random.randint(0,6)
        if n <= self.bullets:
            print("You are dead")
            self.alive = False
        else:
            print("You have escaped..., but not for long")
            self.bullets += 1
            print(f"Now the chamber has {self.bullets} bullets")

        
def handling_connections(addr, min_conn=1, max_conn=4, timeout=0): 
    time_taken =0
    conns_dict = {}
    Server = Listener(addr)
    sock = Server._listener._socket
    start_time=0
    print("Accepting Connections")
    while(time_taken < timeout):
        # escape with maximum connections reached
        if(len(conns_dict) == max_conn):
            print("maximum clients joined")
            broadcast(conns_dict.values(), "Maximum players joined")
            break
        # managing timer if minimum clients have joined
        if(len(conns_dict) >= min_conn):
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
            while(p_name in conns_dict.keys()):
                conn.send("Give a different name, already in use:")
                p_name = conn.recv()
            conn.send("Connected")
            player = Player(p_name)
            conn.send(player)
            conns_dict[conn] = p_name
            print(f"Connection Successful for player [{player.name}]")
    
    return conns_dict

def send_to(conn, conn_dict, msg):
    try:
        conn.send(msg)
    except EOFError:
        broadcast(conn_dict, f"Player [{conn_dict[conn]}] has disconnected")
        del conn_dict[conn]
    finally:
        return conn_dict

def recv_from(conn, conn_dict):
    try:
        msg = conn.recv()
    except EOFError:
        broadcast(conn_dict, f"Player [{conn_dict[conn]}] has disconnected")
        del conn_dict[conn]
        msg = None
    finally:
        return conn_dict, msg

def broadcast(conns, conn_dict, msg):
    for conn in conns.keys():
        conn_dict = send_to(conn, conn_dict, "[BROADCAST] "+msg)
    return conn_dict

