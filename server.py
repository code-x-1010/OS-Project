import communication as c
import random

TABLE_RANKS = ["Queen", "King", "Ace"]


def new_deck():
    deck = ["Queen"] * 6 + ["King"] * 6 + ["Ace"] * 6 + ["Joker"] * 2
    random.shuffle(deck)
    return deck


def card_matches(card, table_rank):
    return card == table_rank or card == "Joker"


def new_player(name):
    return {
        "name": name,
        "alive": True,
        "hand": [],
        "chamber_idx": 0,
        "bullet_chamber": random.randint(0, 5),
    }


def hand_str(hand):
    return ", ".join(f"{i + 1}:{card}" for i, card in enumerate(hand))


def pull_trigger(player):
    dying = player["chamber_idx"] == player["bullet_chamber"]
    player["chamber_idx"] += 1
    if dying:
        player["alive"] = False
    return dying


def next_alive_after(names, players, start):
    idx = names.index(start)
    n = len(names)
    for i in range(1, n + 1):
        cand = names[(idx + i) % n]
        if players[cand]["alive"]:
            return cand
    return start


def request_input(conn, name, prompt):
    c.send_to(conn, f"[{name}]Input {prompt}")
    return c.recv_from(conn).strip()


def build_prompt(table_rank, hand, last_play):
    parts = [
        f"Table card: {table_rank}.",
        f"Your hand: [{hand_str(hand)}].",
    ]
    if last_play:
        parts.append(
            f"{last_play['player']} played {last_play['claim']} card(s) claiming {table_rank}."
        )
    parts.append(
        "Enter 'play <i> [j] [k]' to play 1-3 cards, "
        + ("or 'challenge' to call a liar." if last_play else "(you must play — you are first).")
    )
    return " ".join(parts)


def prompt_action(conn, name, table_rank, hand, last_play):
    msg = build_prompt(table_rank, hand, last_play)
    while True:
        resp = request_input(conn, name, msg)
        tokens = resp.lower().split()
        base = build_prompt(table_rank, hand, last_play)
        if not tokens:
            msg = "Empty input. " + base
            continue
        if tokens[0] == "challenge":
            if last_play is None:
                msg = "Cannot challenge — no previous play. " + base
                continue
            return ("challenge", None)
        if tokens[0] == "play":
            try:
                idxs = sorted(set(int(t) - 1 for t in tokens[1:]))
            except ValueError:
                msg = "Indices must be integers. " + base
                continue
            if not (1 <= len(idxs) <= 3):
                msg = "Play 1-3 cards. " + base
                continue
            if any(i < 0 or i >= len(hand) for i in idxs):
                msg = "Index out of range. " + base
                continue
            return ("play", idxs)
        msg = "Unknown command. " + base


def run_round(conns, players, names, starter, round_num):
    alive = [n for n in names if players[n]["alive"]]

    deck = new_deck()
    for n in alive:
        players[n]["hand"] = [deck.pop() for _ in range(5)]

    table_rank = random.choice(TABLE_RANKS)

    c.broadcast(conns.values(), f"\n--- Round {round_num} ---")
    c.broadcast(conns.values(), f"Alive players: {', '.join(alive)}")
    c.broadcast(conns.values(), f"Table card for this round: {table_rank}")
    for n in alive:
        c.send_to(conns[n], f"Your hand: [{hand_str(players[n]['hand'])}]")

    if starter not in alive:
        starter = alive[0]
    order = alive[alive.index(starter):] + alive[: alive.index(starter)]

    last_play = None
    turn = 0

    while True:
        current = order[turn % len(order)]
        p = players[current]

        if len(p["hand"]) == 0:
            if last_play is None:
                c.broadcast(conns.values(), "All hands are empty. Round draws.")
                return None
            c.broadcast(conns.values(), f"{current} has no cards left — forced challenge.")
            action, _ = "challenge", None
        else:
            action, parsed = prompt_action(conns[current], current, table_rank, p["hand"], last_play)

        if action == "challenge":
            revealed = last_play["cards"]
            truthful = all(card_matches(card, table_rank) for card in revealed)
            c.broadcast(
                conns.values(),
                f"{current} challenges {last_play['player']}! Revealed cards: [{', '.join(revealed)}]",
            )
            if truthful:
                c.broadcast(
                    conns.values(),
                    f"All cards match {table_rank}. {current} was wrong — {current} plays roulette.",
                )
                return current
            else:
                c.broadcast(
                    conns.values(),
                    f"Not all cards match {table_rank}. {last_play['player']} lied — plays roulette.",
                )
                return last_play["player"]

        indices = parsed
        played = [p["hand"][i] for i in indices]
        for i in sorted(indices, reverse=True):
            p["hand"].pop(i)
        last_play = {"player": current, "cards": played, "claim": len(played)}
        c.broadcast(
            conns.values(),
            f"{current} plays {len(played)} card(s) face-down, claiming all are {table_rank}.",
        )
        c.send_to(conns[current], f"Your hand: [{hand_str(p['hand'])}]")
        turn += 1


def play_liars_bar(conns):
    names = list(conns.keys())
    if len(names) < 2:
        c.broadcast(conns.values(), "Need at least 2 players. Shutting down.")
        c.await_delivery(conns.values())
        return

    players = {n: new_player(n) for n in names}

    c.broadcast(conns.values(), "=== Liar's Bar ===")
    c.broadcast(conns.values(), f"Players: {', '.join(names)}")
    c.broadcast(
        conns.values(),
        "Deck: 6 Queens, 6 Kings, 6 Aces, 2 Jokers. Each round you're dealt 5 cards.",
    )
    c.broadcast(
        conns.values(),
        "On your turn, play 1-3 cards face-down claiming they are the table card, or challenge the previous player.",
    )
    c.broadcast(
        conns.values(),
        "Jokers always count as the table card. Loser of a challenge plays Russian roulette (1 bullet, 6 chambers).",
    )

    starter = names[0]
    round_num = 0

    while sum(1 for pl in players.values() if pl["alive"]) > 1:
        round_num += 1
        loser = run_round(conns, players, names, starter, round_num)

        if loser is None:
            starter = next_alive_after(names, players, starter)
            continue

        lp = players[loser]
        pull_num = lp["chamber_idx"] + 1
        c.broadcast(
            conns.values(),
            f"{loser} pulls the trigger (pull #{pull_num}, odds 1-in-{6 - lp['chamber_idx']})...",
        )
        died = pull_trigger(lp)
        if died:
            c.broadcast(conns.values(), f"*BANG* {loser} is eliminated!")
            starter = next_alive_after(names, players, loser)
        else:
            c.broadcast(conns.values(), f"*click* {loser} survives.")
            starter = loser

    survivors = [n for n, pl in players.items() if pl["alive"]]
    if survivors:
        c.broadcast(conns.values(), f"\n=== {survivors[0]} wins the game! ===")
    else:
        c.broadcast(conns.values(), "\n=== Nobody survived. ===")
    c.await_delivery(conns.values())


conns = c.handling_connections(("127.0.0.1", 6000), 2, 10)
play_liars_bar(conns)
