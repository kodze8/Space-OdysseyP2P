import random
import socket
import threading
import time
import waiting_room
import spaceship

DISCOVERY_PORT = 8001
BROADCAST_IP = '255.255.255.255'

ADDRESS = socket.gethostbyname(socket.gethostname())


def make_discovery_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except OSError:
        pass
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(('', DISCOVERY_PORT))
    return s


def location_generator():
    return random.randint(10, 500), random.randint(10, 500)


def append_waiting_room(username, port):
    with waiting_room.lock:
        waiting_room.user_list.append(f"{username} (Port: {port})")


class Peer:
    def __init__(self):
        self.room_open = True
        self.peers = set()
        self.peer_locations = {}  # port : (x, y)

        self.port = 0
        self.username = ""
        self.socket = self.initiate_socket()

        self.is_host = False
        self.host_ranks = []
        self.score = 0
        (self.x, self.y) = location_generator()

        # added13
        self.peer_pings = {}

        threading.Thread(target=self.announcer, args=(self.port, self.username,),
                         daemon=True).start()
        threading.Thread(target=self.listener, daemon=True).start()
        threading.Thread(target=self.receive_msg, daemon=True).start()

        waiting_room.run_waiting_room()

        self.game_on = False
        threading.Thread(target=self.send_msg, args=("STOP",), daemon=True).start()
        while len(self.peer_locations) != len(self.peers):
            time.sleep(0.01)

        self.space_ship = spaceship.Spaceship(self.x, self.y, self.peer_locations)

        self.game_on = True
        threading.Thread(target=self.ping_peers, daemon=True).start()
        threading.Thread(target=self.send_my_location, daemon=True).start()
        threading.Thread(target=self.save_monkey, daemon=True).start()

        self.space_ship.move()
        threading.Thread(target=self.send_msg, args=("EXIT",), daemon=True).start()

    def ping_peers(self):
        while self.game_on:
            for (ip, port) in self.peers:
                timestamp = time.time()
                msg = f"PING:{self.port}:{timestamp}"
                try:
                    self.socket.sendto(msg.encode(), (ip, port))
                    # PING MSG printed on Terminal
                    print(msg)
                except Exception:
                    continue
            time.sleep(2)  # ping every 2 seconds

    def send_my_location(self):
        while self.game_on:
            if self.x != self.space_ship.spaceship_x or self.y != self.space_ship.spaceship_y:
                self.x = self.space_ship.spaceship_x
                self.y = self.space_ship.spaceship_y
                msg = f"NEW-LOCATION-{self.port}:{self.x},{self.y}"
                self.send_msg(msg)

    def save_monkey(self):
        while self.game_on:
            for monkey_loc in self.space_ship.dots.copy():
                if abs(self.x - monkey_loc[0]) < 15 and abs(self.y - monkey_loc[1]) < 15:
                    msg = f"TRY-SAVE:{self.port}:{monkey_loc[0]},{monkey_loc[1]}"
                    self.send_msg(msg)
                    self.socket.sendto(msg.encode(), (ADDRESS, self.port))
            time.sleep(0.1)

    def initiate_socket(self):
        self.username, self.port = waiting_room.get_user_input()
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        invalid_port = True
        while invalid_port:
            try:
                soc.bind((ADDRESS, self.port))
                invalid_port = False
            except Exception:
                self.username, self.port = waiting_room.get_user_input("PORT NUMBER IS USED")
        append_waiting_room(self.username, self.port)
        return soc

    def host_maker(self):
        rank = random.randint(0, 1000000)
        self.host_ranks.append((rank, self.port))

        msg = f"RANK-PORT:{rank}-{self.port}"
        for peer in self.peers:
            self.socket.sendto(msg.encode(), peer)

        start_time = time.time()
        expected_ranks = len(self.peers) + 1

        while len(self.host_ranks) < expected_ranks and time.time() - start_time < 5:
            time.sleep(0.1)

        highest = max(self.host_ranks, key=lambda x: x[0])

        if highest[1] == self.port:
            self.is_host = True
            print("I am the host.")
        else:
            print("Another peer is the host.")

        self.host_ranks = []
        threading.Thread(target=self.broadcast_location).start()

    def start_game(self):
        msg = f"LOCATION-{self.port}:{self.x},{self.y}"
        self.send_msg(msg)

    def receive_msg(self):
        while True:
            try:
                data, addr = self.socket.recvfrom(4096)
                data = data.decode()

                if data == "SHUTDOWN":
                    if self.is_host:
                        self.is_host = False

                    self.socket.close()
                    break

                if data.startswith("CLOSE-ROOM"):

                    self.room_open = False
                    waiting_room.running = False
                    # threading.Thread(target=self.host_maker).start()

                elif data.startswith("RANK-PORT"):
                    r, p = data.split(":")[1].split("-")
                    self.host_ranks.append((int(r), int(p)))

                elif data.startswith("PEER-LEFT") or data.startswith("HOST-LEFT"):
                    port_left = int(data.split(":")[1])
                    self.peers.remove((ADDRESS, port_left))
                    self.peer_locations.pop(port_left)  # ADDED
                    if data.startswith("HOST-LEFT"):
                        threading.Thread(target=self.host_maker).start()

                # -- LOCATION-[PORT]:x,y --
                elif data.startswith("LOCATION"):
                    port_location = int(data.split(":")[0].split("-")[1])
                    x_location = int(data.split(":")[1].split(",")[0])
                    y_location = int(data.split(":")[1].split(",")[1])
                    self.peer_locations[port_location] = (x_location, y_location)

                # -- NEW-LOCATION-[PORT]:x,y --
                elif data.startswith("NEW-LOCATION") and self.game_on:
                    port_location = int(data.split(":")[0].split("-")[2])
                    x_location = int(data.split(":")[1].split(",")[0])
                    y_location = int(data.split(":")[1].split(",")[1])
                    self.peer_locations[port_location] = (x_location, y_location)
                    self.space_ship.player_locations[port_location] = (x_location, y_location)

                # -- MONKEY-LOCATION: x,y --
                elif data.startswith("MONKEY-LOCATION") and self.game_on:
                    monkey_x = int(data.split(":")[1].split(",")[0])
                    monkey_y = int(data.split(":")[1].split(",")[1])
                    self.space_ship.dots.append((monkey_x, monkey_y))

                # -- TRY-SAVE:{port}:x,y --
                elif data.startswith("TRY-SAVE") and self.game_on:
                    if self.is_host:
                        port = int(data.split(":")[1])
                        x = int(data.split(":")[2].split(",")[0])
                        y = int(data.split(":")[2].split(",")[1])
                        loc = (x, y)
                        if loc in self.space_ship.dots:
                            # self.space_ship.dots.remove(loc)
                            self.socket.sendto(f"CONFIRM-SAVE:{port}:{x},{y}".encode(), (ADDRESS, self.port))
                            for peer in self.peers:
                                self.socket.sendto(f"CONFIRM-SAVE:{port}:{x},{y}".encode(), peer)

                # -- CONFIRM-SAVE:{port}:x,y --
                elif data.startswith("CONFIRM-SAVE"):
                    port = int(data.split(":")[1])
                    x = int(data.split(":")[2].split(",")[0])
                    y = int(data.split(":")[2].split(",")[1])
                    loc = (x, y)
                    if loc in self.space_ship.dots:
                        self.space_ship.dots.remove(loc)
                    if port == self.port:
                        self.score += 1
                        self.space_ship.score += 1
                    else:
                        self.space_ship.peer_scores[port] += 1

                # -- PING --
                elif data.startswith("PING"):
                    sender_port = int(data.split(":")[1])
                    timestamp = float(data.split(":")[2])
                    self.socket.sendto(f"PONG:{sender_port}:{timestamp}".encode(), addr)

                # -- PONG --
                elif data.startswith("PONG"):
                    sender_port = int(data.split(":")[1])
                    timestamp = float(data.split(":")[2])
                    rtt = (time.time() - timestamp) * 1000
                    self.peer_pings[sender_port] = round(rtt, 2)
                    # Printed Pong Values in the Treminal
                    print(data)

            except Exception as e:
                print("Game listener error:", e)
                break

    def send_msg(self, msg):
        # -- STOP --
        if msg.strip() == "STOP":
            self.room_open = False
            msg = "CLOSE-ROOM"
            for peer in self.peers:
                self.socket.sendto(msg.encode(), peer)
            self.host_maker()
            self.start_game()

        # -- EXIT --
        elif msg.strip() == "EXIT":
            self.room_open = False

            msg = f"PEER-LEFT:{self.port}"
            if self.is_host:
                msg = f"HOST-LEFT:{self.port}"

            for peer in self.peers:
                self.socket.sendto(msg.encode(), peer)

            self.socket.sendto(b"SHUTDOWN", (ADDRESS, self.port))

        # -- MOVE-[PORT]:(delta(x), delta(y)) --
        elif msg.strip().startswith("MOVE"):
            pass

        # -- LOCATION-[PORT]:x,y --
        elif msg.strip().startswith("LOCATION"):
            for peer in self.peers:
                self.socket.sendto(msg.encode(), peer)

        else:
            for peer in self.peers:
                self.socket.sendto(msg.encode(), peer)

    def broadcast_location(self):
        while self.is_host:
            if self.game_on:
                loc = location_generator()
                self.space_ship.dots.append(loc)
                loc_str = f"MONKEY-LOCATION:{loc[0]},{loc[1]}"
                for peer in self.peers:
                    self.socket.sendto(loc_str.encode(), peer)
                time.sleep(3)

    def listener(self):
        sock = make_discovery_socket()
        while self.room_open:
            data, addr = sock.recvfrom(1024)
            data = data.decode()
            if data.startswith("ROOM-ANNOUNCE"):
                peer_port = int(data.split(":")[1].split("-")[0])
                peer_username = data.split(":")[1].split("-")[1]
                if not self.port == peer_port and not self.peers.__contains__((ADDRESS, peer_port)):
                    self.peers.add((ADDRESS, peer_port))
                    append_waiting_room(peer_username, peer_port)
            elif data.startswith("ROOM-CLOSE"):
                break
        print("Listener closed")

    def announcer(self, game_port, game_username):
        sock = make_discovery_socket()
        while self.room_open:
            msg = f"ROOM-ANNOUNCE:{game_port}-{game_username}".encode()
            sock.sendto(msg, (BROADCAST_IP, DISCOVERY_PORT))
            time.sleep(1)
        msg = f"ROOM-CLOSE".encode()
        sock.sendto(msg, (BROADCAST_IP, DISCOVERY_PORT))
        print("Announcer closed")


if __name__ == '__main__':
    Peer()
