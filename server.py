import communication_multiprocessing as c

conns = c.handling_connections(("127.0.0.1",6000), 2, 10)
conns['a'].send("[a]Input hi")
print(conns['a'].recv())
