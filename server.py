import communication_multiprocessing as c

conns = c.handling_connections(("127.0.0.1",6000), 2, 10)
c.send_to(conns[next(iter(conns))],f"[{next(iter(conns)).name}]Input Hi")
message = c.recv_from(conns[next(iter(conns))])
c.broadcast(conns.values(), message)

