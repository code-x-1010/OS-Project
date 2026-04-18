from xmlrpc.client import ServerProxy
import sys
import random


class Player:
    def __init__(self, name) -> None:
        self.name = name
        self.bullets = 1
        self.hand = []
        self.alive = True

    def show_hands(self):
        print(self.hand)

    def deal_cards(self, deck):
        self.hand = random.sample(deck, k=5)
        for card in self.hand:
            deck.remove(card)
        return deck

    def roullette(self):
        n = random.randint(0, 6)
        if n <= self.bullets:
            print("You are dead")
            self.alive = False
        else:
            print("You have escaped..., but not for long")
            self.bullets += 1
            print(f"Now the chamber has {self.bullets} bullets")

    def to_dict(self):
        return {
            "name": self.name,
            "bullets": self.bullets,
            "hand": list(self.hand),
            "alive": self.alive,
        }

    @staticmethod
    def from_dict(d):
        p = Player(d["name"])
        p.bullets = d["bullets"]
        p.hand = list(d["hand"])
        p.alive = d["alive"]
        return p


def listen(proxy):
    global player
    try:
        msg = proxy.fetch(player.name, 25)
        if msg is None:
            return
        print(msg)
        # responds if the server requests the player
        if '[' + player.name + ']' in msg:
            if "Input" in msg:
                while True:
                    response = input().strip()
                    if response == "SHOW":
                        player.show_hands()
                    else:
                        break
                proxy.push(player.name, response)
            if "[SEND INFO]" in msg:
                proxy.push(player.name, player.to_dict())
                player = Player.from_dict(proxy.fetch(player.name, 25))
            if "[LOST]" in msg:
                player.roullette()
                proxy.push(player.name, player.alive)
            if "[PLAY]" in msg:
                while True:
                    raw = input().strip()
                    if raw == "SHOW":
                        player.show_hands()
                        continue
                    response = raw.split(",")
                    if len(response) > 0 and len(response) < 4:
                        break
                    else:
                        print("Wrong format")
                        print(msg)
                proxy.push(player.name, response)
                player = Player.from_dict(proxy.fetch(player.name, 25))
    except (ConnectionError, OSError):
        print("Server closed the connection\nClosing the Client....")
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[client error] {type(e).__name__}: {e}")


def connect():
    # Establishing connection with server
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
            p = Player(p_name)
            print("Joined the Server")
            break
        print(msg)

    return proxy, p


if __name__ == "__main__":
    player = None
    proxy, player = connect()
    # listens the connection for messages
    while True:
        listen(proxy)
