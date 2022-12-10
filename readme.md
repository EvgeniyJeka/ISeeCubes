Logic:
..


Events:

Client - to - server:

1. 'join' - client sends a connection request, tries to join the chat rooms
2. 'client_sends_message' - client sends a message to the selected chat room (destination in message content)
3. 'client_disconnection' - client terminates connection

Server - to - client:

1. 'received_message' - a message was received fro one of the clients, will be published by the server to the selected chat room
2. 'new_user_online' - new client has connected, all clients that are currently online are notified
3. 'user_has_gone_offline' - user has decided to disconnect (deliberately)






