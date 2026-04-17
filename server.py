import communication as c

conns = c.handling_connections(("127.0.0.1", 6000), 2, 10)
c.send_to(conns['a'], "[a]Input Hi")
message = c.recv_from(conns['a'])
c.broadcast(conns.values(), message)
c.await_delivery(conns.values())
