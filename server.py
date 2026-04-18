import communication as c
from client import Player
import copy
import random

# set global vars
_raw_conns = c.handling_connections(("127.0.0.1", 6000), min_conn=2, timeout=10)
players_dict = {conn: name for name, conn in _raw_conns.items()}
alive_players = copy.copy(players_dict)
current_player_index = None
current_player = None
game_over = False
deck = ["A"] * 6 + ["K"] * 6 + ["Q"] * 6 + ["Joker"] * 2
previous_hand = None


def setup_round(alive_dict):
    global deck, players_dict
    for conn, player_name in list(alive_dict.items()):
        c.send_to(conn, f"[{player_name}] [SEND INFO]")
        data = c.recv_from(conn)
        if data is None:
            continue
        player = Player.from_dict(data)
        deck = player.deal_cards(deck)
        c.send_to(conn, player.to_dict())  # send back the updated object


def get_curr_player(conn):
    global players_dict, current_player
    current_player = None
    if conn not in players_dict:
        return
    c.send_to(conn, f"[{players_dict[conn]}] [SEND INFO]")
    data = c.recv_from(conn)
    if data is not None:
        current_player = Player.from_dict(data)
        c.send_to(conn, current_player.to_dict())  # echo back


def get_player_with_hands():
    global player_with_hands, players_dict
    for conn, player_name in list(player_with_hands.items()):
        c.send_to(conn, f"[{player_name}] [SEND INFO]")
        data = c.recv_from(conn)
        if data is not None:
            c.send_to(conn, data)


def get_alive_number():
    global player_with_hands, players_dict
    counter = 0
    for conn, player_name in list(player_with_hands.items()):
        c.send_to(conn, f"[{player_name}] [SEND INFO]")
        data = c.recv_from(conn)
        if data is not None:
            c.send_to(conn, data)
            if data["alive"]:
                counter += 1
    return counter


def get_hand_number():
    global player_with_hands, players_dict
    counter = 0
    for conn, player_name in list(player_with_hands.items()):
        c.send_to(conn, f"[{player_name}] [SEND INFO]")
        data = c.recv_from(conn)
        if data is not None:
            c.send_to(conn, data)
            if data["alive"] and data["hand"] != []:
                counter += 1
    return counter


c.broadcast(players_dict, "GAME STARTING !!!!")
while not game_over:
    if len(alive_players) <= 1:
        if len(alive_players) == 1:
            winner = alive_players[next(iter(alive_players))]
            c.broadcast(players_dict, f"WINNER is {winner}")
        c.broadcast(players_dict, "GAME OVER !!!!")
        game_over = True
        break
    deck = ["A"] * 6 + ["K"] * 6 + ["Q"] * 6 + ["Joker"] * 2  # reset deck each round
    setup_round(alive_players)

    # randomly assign the starting player
    current_player_index = random.randint(0, len(alive_players) - 1)

    player_with_hands = copy.copy(players_dict)

    c.broadcast(alive_players, "Round is starting")

    first_turn = True
    round_symbol = random.choice(["A", "K", "Q"])
    round_over = False
    while not round_over:
        if len(alive_players) <= 1:
            break
        current_player_index = current_player_index % len(alive_players)
        curr_conn = list(alive_players.keys())[current_player_index]
        get_curr_player(curr_conn)
        if get_alive_number() == 1:
            break
        while current_player is None:
            current_player_index = (current_player_index + 1) % len(alive_players)
            curr_conn = list(alive_players.keys())[current_player_index]
            get_curr_player(curr_conn)
        if current_player.alive == False:
            continue
        get_player_with_hands()
        if get_hand_number() == 1:
            c.send_to(curr_conn, f"[{players_dict[curr_conn]}] [LOST]")
            msg = c.recv_from(curr_conn)
            round_over = True
            if msg is True:
                c.broadcast(alive_players, f"{players_dict[curr_conn]} is ALIVE !!!!")
            else:
                c.broadcast(alive_players, f"{players_dict[curr_conn]} is DEAD !!!!")
                if curr_conn in alive_players:
                    del alive_players[curr_conn]
            c.broadcast(alive_players, "ROUND OVER !!!!")

        else:
            curr_conn = list(alive_players.keys())[current_player_index]
            turn_over = False
            while True:
                if first_turn:
                    c.send_to(curr_conn, f"[{players_dict[curr_conn]}] Input your action (PLAY/SHOW). Since your the first turn of the round:")
                    msg = c.recv_from(curr_conn)
                else:
                    c.send_to(curr_conn, f"[{players_dict[curr_conn]}] Input your action (PLAY/CALL/SHOW):")
                    msg = c.recv_from(curr_conn)
                if msg == "PLAY":
                    c.send_to(curr_conn, f"[{players_dict[curr_conn]}] [PLAY] Give your card index min of 1 to max of 3 as '0,2,3':")
                    hand_index = c.recv_from(curr_conn)
                    turn_over = True
                    if len(hand_index) > 0 and len(hand_index) < 4:
                        previous_hand = []
                        for i in hand_index:
                            previous_hand.append(current_player.hand[int(i)])
                        for i in previous_hand:
                            current_player.hand.remove(i)
                        c.send_to(curr_conn, current_player.to_dict())
                        current_player_index = (current_player_index + 1) % len(alive_players)
                elif msg == "CALL" and not first_turn:
                    if len(previous_hand) == 0:
                        c.send_to(curr_conn, f"[{players_dict[curr_conn]}] Input your action (PLAY/SHOW). Since Previous Player has no cards:")
                        msg = c.recv_from(curr_conn)
                    else:
                        turn_over = True
                        round_over = True
                        c.broadcast(alive_players, f"{players_dict[curr_conn]} chose to call LIAR !!!!")
                        prev_conn = list(alive_players.keys())[(current_player_index - 1) % len(alive_players)]
                        if previous_hand.count(round_symbol) != len(previous_hand):
                            c.broadcast(alive_players, f"{players_dict[prev_conn]} is a LIAR !!!!")
                            c.send_to(prev_conn, f"[{players_dict[prev_conn]}] [LOST]")
                            msg = c.recv_from(prev_conn)
                            if msg is True:
                                c.broadcast(alive_players, f"{players_dict[prev_conn]} is ALIVE !!!!")
                            else:
                                c.broadcast(alive_players, f"{players_dict[prev_conn]} is DEAD !!!!")
                                if prev_conn in alive_players:
                                    del alive_players[prev_conn]
                        else:
                            c.broadcast(alive_players, f"{players_dict[prev_conn]} is not a LIAR !!!!")
                            c.send_to(curr_conn, f"[{players_dict[curr_conn]}] [LOST]")
                            msg = c.recv_from(curr_conn)
                            if msg is True:
                                c.broadcast(alive_players, f"{players_dict[curr_conn]} is ALIVE !!!!")
                            else:
                                c.broadcast(alive_players, f"{players_dict[curr_conn]} is DEAD !!!!")
                                if curr_conn in alive_players:
                                    del alive_players[curr_conn]
                        c.broadcast(alive_players, "ROUND OVER !!!!")
                        previous_hand = None
                        current_player_index = (current_player_index + 1) % max(len(alive_players), 1)
                if turn_over:
                    first_turn = False
                    break

c.await_delivery(players_dict)
