#General Logic:

## Server side:

The server is a Flask - Socket IO server, it communicates with client via HTTP requests
and websocket messages - each message contains an event.

The server will keep a list of all registered (existing) users (in DB)
and a list of all users, that are currently active (connected).

### Connection Establishing Flow ###

When a user connects, his name is paired with each existing username and a new set of rooms is created 
on the server side - the name of each room consists of the name of the newly joined user 
and a name of an existing one, for example: 'avi&lisa', 'avi&era'.

When the user wishes to send a message to another user, the message is published to the room that
the user shares with the person he would like to speak to.   
 
On connection the client send an HTTP request and receives from the server a list of 
all existing contacts, room names and a list of contacts, that are currently online.

After that the client emits a 'join' event for each room from the list - it contains the room name
and the username. 

The server handles each 'join' event - the new user is:
+ Joined to the rooms
+ Added to the list of 'active users'  

Once a user has connected, the server will publish the 'new_user_online' event for all clients.
 
### Message Sending Flow 

User must be connected to send a message. 
User can send a message to every existing user from the list provided by the server on connection. 
The message sent to another user will be available only to the sender and to the receiver.

After the message destination is selected, the client emits the 'client_sends_message' event 
that contains the sender name, the message and the room it is published to - 
only the sender and the receiver are in that room.

The server will parse the 'client_sends_message' event and publish the 'received_message'
event to the selected room - the former will be received bt the target user, and the message
will reach its destination. 

### Disconnection Flow 
...
...
...




## Events :

### Client - to - server:

1. 'join' - client sends a connection request, tries to join the chat rooms
2. 'client_sends_message' - client sends a message to the selected chat room (destination in message content)
3. 'client_disconnection' - client terminates connection

### Server - to - client:

1. 'received_message' - a message was received fro one of the clients, will be published by the server to the selected chat room
2. 'new_user_online' - new client has connected, all clients that are currently online are notified
3. 'user_has_gone_offline' - user has decided to disconnect (deliberately) or lost connection






