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



### Client Side Structure

The client consists of:

1. ChatClient - application main GUI. Contains the app skin - the contacts list, the buttons and all the methods
that are used to handle button clicks. Opens secondary windows on request - 
MessageBox (when user initiates a conversation with another user) and LoginWindow (when user wishes to log in).

Note - each conversation is handled in a separate thread, so the user will be able to have several conversations
simultaneously, to each time the 'Chat With' button is clicked a new thread starts and a new MessageBox window opens. 

One of the properties of the ChatClient is an instance of ClientAppCore, so the ChatClient will be able to use
all the App Core methods and pass the instance to other components, if required. 


2. ClientAppCore - application core methods. This class contains the methods required to communicate with the 
server side - send a log in request, send a connection request and receive feeds from the server in the response.
When the 'start_listening_loop' method is called the ClientAppCore starts to listen to all the incoming events (websocket messages)
in a separate thread and handle each event accordingly. The ChatClient calls 'start_listening_loop' method
when the 'connect' button is clicked. 

Note - one of the events that can be handled in ClientAppCore is 'received_message' - in that case 
ClientAppCore opens an instance of MessageBox in a separate thread (it happens when another user sends a message
to the current user).

While handling the events ClientAppCore is responsible to make the required adjustments in ChatClient UI elements - 
to color usernames of  users that are currently online in green, to enable/disable buttons e.t.c. 

3. MessageBox...

4. LoginWindow...
 








