# OS-Project

# How to run
- Open a terminal and run server.py
- For each player open a different terminal and run client.py
- Then follow the instructions from the client screen
- Have fun!!!

# The directory structure
- server.py : contains the game logic
- client.py : listens and responds to server request 
- communication multiprocessing.py for *message passing* / communication.py for *RPC* : *communication library*

# Important methods in files
- client.py: connect() to connect to server, listen() to listen the connection endpoint for any messages
- communication multiprocessing.py / communication.py: 
    - player class - for each player process
    - handling connection(address) - lets the server wait and accept the client connections
    - send to(connection endpoint, msg) - sends the message to connection endpoint
    - recv from(connection) - recieves the message from the connection endpoint
    - broadcast(connections, message) - sends the message to all the connection endpoint present in the connections
- server.py: setup round() deals 5 cards to all the players, get_curr_player() requests and gets the current player object based on the connection, get_alive_number() gives the number of alive players, get_hand_number() gives the number of players with non- empty hands
