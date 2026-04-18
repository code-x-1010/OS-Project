import communication_multiprocessing as c
import copy
import random

#set global vars
players_dict= c.handling_connections(("127.0.0.1",6000), min_conn = 2, max_conn = 4, timeout=10)
alive_players= players_dict
current_player_index = None
current_player = None
game_over = False
deck = ["A"]*6+["K"]*6+["Q"]*6+["Joker"]*2
previous_hand = None

def setup_round(alive_dict):
    global deck, players_dict
    for conn, player_name in enumerate(alive_dict):
        players_dict = c.send_to(conn, players_dict, f"[{player_name}] [SEND INFO]")
        players_dict, player = c.recv_from(conn, players_dict)
        deck = player.deal_cards(deck)
        players_dict = c.send_to(conn, players_dict, player) # send back the updated object

def get_curr_player(conn):
    global players_dict, current_player
    current_player = None
    players_dict = c.send_to(conn, players_dict, f"[{player_name}] [SEND INFO]")
    if players_dict[conn] in players_dict.values(): # if player still connected
        players_dict, current_player = c.recv_from(conn, players_dict)

def get_player_with_hands():
    global player_with_hands, players_dict
    for conn, _ in enumerate(player_with_hands):
        players_dict = c.send_to(conn, players_dict, f"[{player_name}] [SEND INFO]")
        players_dict, player = c.recv_from(conn, players_dict)
        
def get_alive_number():
    global player_with_hands, players_dict
    counter = 0
    for conn, _ in enumerate(player_with_hands):
        players_dict = c.send_to(conn, players_dict, f"[{player_name}] [SEND INFO]")
        players_dict, player = c.recv_from(conn, players_dict)
        if player.alive:
            counter +=1
    return counter
    
def get_hand_number():
    global player_with_hands, players_dict
    counter = 0
    for conn, _ in enumerate(player_with_hands):
        players_dict = c.send_to(conn, players_dict, f"[{player_name}] [SEND INFO]")
        players_dict, player = c.recv_from(conn, players_dict)
        if player.alive and player.hand != []:
            counter +=1
    return counter

players_dict = c.broadcast(players_dict, players_dict, "GAME STARTING !!!!")
while not game_over:
    if(len(alive_players)) == 1:
        players_dict = c.broadcast(players_dict, players_dict, f"WINNER is {alive_players[next(iter(alive_players))]}")
        players_dict = c.broadcast(players_dict, players_dict, "GAME OVER !!!!")
    setup_round(alive_players)

    #check the alive players connections
    for conn, _ in enumerate(alive_players):
        if alive_players[conn] not in players_dict.values():
            del alive_players[conn]
    #randomly assign the starting player
    current_player_index = random.randint(0, len(alive_players)-1)
    
    player_with_hands = players_dict
    
    c.broadcast(alive_players,"Round is starting")

    first_turn = True
    round_symbol = random.sample(["A","K","Q"])
    round_over = False
    while not round_over:
        get_curr_player(current_player_index)
        if get_alive_number() ==1:
            break
        while current_player is None:
            current_player_index = (current_player_index + 1 ) % len(alive_players)
            get_curr_player(current_player_index)
        if(current_player.alive == False):
            continue
        get_player_with_hands()
        if(get_hand_number()==1):
            c.send_to(curr_conn,players_dict,f"[{players_dict[curr_conn]}] [LOST]")
            players_dict, msg = c.recv_from(curr_conn,players_dict)
            round_over = True
            if msg is True:
                players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[curr_conn]} is ALIVE !!!!")
            else:
                players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[curr_conn]} is DEAD !!!!")
            players_dict = c.broadcast(alive_players, players_dict, "ROUND OVER !!!!")

        else:
            curr_conn = list(alive_players.keys())[current_player_index]
            turn_over = False
            while True:
                if first_turn:
                    c.send_to(curr_conn,players_dict,f"[{players_dict[curr_conn]}] Input your action (PLAY/SHOW). Since your the first turn of the round:")
                    players_dict, msg = c.recv_from(curr_conn,players_dict)
                else:
                    c.send_to(curr_conn,players_dict,f"[{players_dict[curr_conn]}] Input your action (PLAY/CALL/SHOW):")
                    players_dict, msg = c.recv_from(curr_conn,players_dict)
                if msg == "PLAY":
                    c.send_to(curr_conn,players_dict,f"[{players_dict[curr_conn]}] [PLAY] Give your card index min of 1 to max of 3 as '0,2,3':")
                    players_dict, hand_index = c.recv_from(curr_conn,players_dict)
                    turn_over = True
                    if len(hand_index)>0 and len(hand_index)<4:
                        previous_hand=[]
                        for i in hand_index:
                            previous_hand.append(current_player.hand[int(i)])
                        for i in previous_hand:
                            current_player.hand.remove(i)
                        c.send_to(curr_conn,players_dict,current_player)
                        current_player_index = (current_player_index + 1) % len(alive_players) 
                elif msg == "CALL" and not first_turn:
                    if len(previous_hand) == 0:
                        c.send_to(curr_conn,players_dict,f"[{players_dict[curr_conn]}] Input your action (PLAY/SHOW). Since Previous Player has no cards:")
                        players_dict, msg = c.recv_from(curr_conn,players_dict)
                    else:
                        turn_over = True
                        players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[curr_conn]} chose to call LIAR !!!!")
                        prev_conn = (curr_conn - 1) % len(alive_players)
                        if previous_hand.count(round_symbol) != len(previous_hand):
                            players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[prev_conn]} is a LIAR !!!!")
                            c.send_to(prev_conn,players_dict,f"[{players_dict[prev_conn]}] [LOST]")
                            players_dict, msg = c.recv_from(prev_conn,players_dict)
                            if msg is True:
                                players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[prev_conn]} is ALIVE !!!!")
                            else:
                                players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[prev_conn]} is DEAD !!!!")
                        else:
                            players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[prev_conn]} is not a LIAR !!!!")
                            c.send_to(curr_conn,players_dict,f"[{players_dict[curr_conn]}] [LOST]")
                            players_dict, msg = c.recv_from(curr_conn,players_dict)
                            if msg is True:
                                players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[curr_conn]} is ALIVE !!!!")
                            else:
                                players_dict = c.broadcast(alive_players, players_dict, f"{players_dict[curr_conn]} is DEAD !!!!")
                        previous_hand = None
                        current_player_index = (current_player_index + 1) % len(alive_players) 
                if turn_over:
                    break
                            


