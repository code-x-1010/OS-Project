from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import threading
import queue
import time


class _ThreadingXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True
    allow_reuse_address = True


class _Hub:
    """Server-side shared state. One queue per direction, per player."""

    def __init__(self):
        self.lock = threading.Lock()
        self.to_client = {}
        self.from_client = {}

    def join(self, name):
        with self.lock:
            if name in self.to_client:
                return "Give a different name, already in use:"
            self.to_client[name] = queue.Queue()
            self.from_client[name] = queue.Queue()
        return "Connected"

    def push(self, name, msg):
        with self.lock:
            q = self.from_client.get(name)
        if q is None:
            return False
        q.put(msg)
        return True

    def fetch(self, name, block_seconds=25):
        with self.lock:
            q = self.to_client.get(name)
        if q is None:
            return None
        try:
            return q.get(timeout=block_seconds)
        except queue.Empty:
            return None


class ConnHandle:
    """Server-side handle for one connected client, emulating multiprocessing.Connection."""

    def __init__(self, name, hub):
        self.name = name
        self._hub = hub

    def send(self, msg):
        self._hub.to_client[self.name].put(msg)

    def recv(self):
        return self._hub.from_client[self.name].get()


def handling_connections(addr, min_conn=1, timeout=0):
    host, port = addr
    hub = _Hub()
    server = _ThreadingXMLRPCServer((host, port), allow_none=True, logRequests=False)
    server.register_function(hub.join, "join")
    server.register_function(hub.push, "push")
    server.register_function(hub.fetch, "fetch")
    threading.Thread(target=server.serve_forever, daemon=True).start()

    conns = {}
    start_time = 0
    time_taken = 0
    print("Accepting Connections")
    while time_taken < timeout:
        if len(conns) >= min_conn:
            if not start_time:
                print(f"The connecting phase will end in {timeout} seconds")
                start_time = time.time()
            else:
                time_taken = time.time() - start_time

        with hub.lock:
            new_names = [n for n in hub.to_client if n not in conns]
        for n in new_names:
            conns[n] = ConnHandle(n, hub)
            print(f"Connection Successful for player [{n}]")

        time.sleep(0.05)

    print(list(conns.keys()))
    return conns


def send_to(conn, msg):
    conn.send(msg)


def recv_from(conn):
    return conn.recv()


def broadcast(conns, msg):
    for conn in conns:
        send_to(conn, msg)


def await_delivery(conns, timeout=5.0):
    """Block until every connected client has fetched all pending outbound messages.
    XML-RPC is pull-based, so without this the server may exit before clients
    fetch their last message, and they will see a dropped connection instead."""
    deadline = time.time() + timeout
    for conn in conns:
        q = conn._hub.to_client[conn.name]
        while not q.empty() and time.time() < deadline:
            time.sleep(0.05)
