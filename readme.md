# General Logic:

Chat application, a simplified version of the 'legendary' well known chat.
It consists of a Chat Server based on Flask - Socket IO and a desktop client
implemented on Python. 

Chatting with another user:
https://www.youtube.com/watch?v=dk44vgkKfPY

Chatting with OpenAI model:
https://www.youtube.com/watch?v=iOxp3ZvDWnw

Version 1.2

After the connection is established user is presented with a list that contains 
all other users and can start a chat with any of them. Users that are currently online are 
colored with green - a message that is sent to such user will be rerouted immediately.
Users that are offline at the moment are colored with red - a message that is sent will
be stored an sent to the user once he is back online. Cached messages for offline users
are stored in Redis.

User needs to log in with his credentials before he can connect. The credentials are 
verified against those that are stored in Postgres SQL DB and the server responds with JWT
generated for the user - all requests sent to the server contain that JWT, and it is verified on 
the server side. JWT's are also stored in Redis. 

The application supports integration with OpenAI ChatGPT model - if OpenAI key
is provided (as a value of 'OPENAI_API_KEY' environment variable) the 'ChatGPT' user
will become online, and all messages sent to that user will be rerouted to ChatGPT API
by the server. 

## Local Run - How To Use:

The PC must have a Docker app installed and running. 
To run the desktop client you must have Python 3.6 or above installed on your machine.

1. Clone the 'ISeeCubes' repository.

2. Run the 'docker-compose up' command - the Postgres and the Redis containers 
   will be fetched from Docker repo and the 'chat server' container will be built and start.
   Once you see the server is running you can launch the client.
   
   If you want to have a conversation with ChatGPT, modify the 'docker-compose.yml' - insert your
   OpenAI API key as the value of 'OPENAI_API_KEY' environment variable of 'chat_messenger' service. 
   
3. Open the 'client_side' folder and install the client requirements (pip install -r requirements.txt)
4. Run the 'chat_client_skin_launcher.py' (python chat_client_skin_launcher.py)

5. Once the chat client skin has appeared click on "Log In" and enter the credentials of one of the 
   test users (can be found in users.json file). Providing the log in was successfully performed 
   the header will change from 'Disconnected' to 'Hello, %your username%!' and the 'Connect' button
   will become enabled.
   
6. Click on the connect button. The client will try to connect. Once the connection is successful
   the 'Connection status' will change to 'Online' and a list of all other users will be fetched 
   from the server. If the current user was addressed by other users earlier, while he was offline
   all those messages will be fetched and presented. 
   
7. If you want to test the app locally you can start one of the test clients 
   (select one from folder 'additional_test_clients' and launch the chat_client_skin_launcher.py).
   As an alternative, you can:
   + Clone the repo to another machine that is connected to your local network
   + Check the internal network IP of the machine the 'I See Cubes' server is running on 
     (can be done with 'ipconfig' command on Windows).
   + Open the 'client_side' folder, install the requirements (on the second machine) and modify the 
     'local_client_config.py' - replace the 'localhost' (CHAT_SERVER_BASE_URL) with the internal IP 
     of the machine that runs the chat server. 
     
   + Now run the client on the second machine - you should be able to log in, connect and send messages 
     to your first user. 
     
     
## Chat Bot integration 

I've added an integration with my other project, Leonid the Chat Bot.
It is based on Vicuna, an Open-Source Large Language Model - now you can 
chat with it via I See Cubes chat (you just need to download the model) - 
all the details can be found here: https://github.com/EvgeniyJeka/Leonid_The_Chatbot

If you run the project with docker-compose, the chat bot container will be started
automatically (unless you comment it out in the yml file).

Messages sent to Leonid The Chat Bot are redirected to it's API as POST requests,
and the responses are brought back.

<b>Please note:</b> Chat Server code was modified, and you can add integrations 
with your chat bots in the similar way, in case you are interested. 
The code is relatively simple, and it may be nice to have an option 
to chat with several chat bots simultaneously. 


## Server side logic:

The server is a Flask - Socket IO server, it communicates with client via HTTP requests
and web socket messages - each message contains an event.

<img src="https://github.com/EvgeniyJeka/ISeeCubes/blob/documentation_27_2_23/i_see_cubes_server_chart.jpg" alt="Screenshot" width="1000" />

### Log In Procedure

User must be logged in before he connects. The client sends a HTTP <b>login request</b>, that 
contains the user's credentials. Those are verified on server side against the user
credentials stored in Postgres SQL. If the credentials are valid a JWT is generated - 
it is stored in Redis and returned to the client in HTTP response. 

All HTTP requests the client sends must contain the JWT in request headers ("Authorization").

All web socket messages, events sent from the client to the server (except for 'connection_alive')
must contain the JWT. 

Once the client disconnects, the JWT is terminated.

### Connection Establishing Flow ###

When a user connects, his name is paired with each existing username and a new set of Rooms is created 
on the server side - the name of each room consists of the name of the newly joined user 
and a name of an existing one, for example: 'Avi&Lisa', 'Avi&Era'.

When the user wishes to send a message to another user, the message is published to the room that
the user shares with the person he would like to speak to.   
 
The connection procedure performed by the client includes:

   - connection to chat server web socket
   
   - contacts list HTTP request (the response includes all existing contacts, those that are currently online
                                 and a list of room names that the specified user is a member of)
                                 
   - emitting a 'join' event (web socket message) to each room on the rooms list


The server handles each 'join' event - the new user is:

+ Joined to the rooms
+ Added to the list of 'active users'  

Once a user has connected, the server will publish the 'new_user_online' event for all clients.
 
### Message Sending Flow 

User must be connected to send a message. 
User can send a message to every existing user from the list provided by the server on connection. 
The message sent to another user will be available only to the sender and to the receiver.

After the message destination is selected, the client emits the <b>'client_sends_message'</b> event 
that contains the sender name, the auth. JWT and the message and the room it is published to - 
only the sender and the receiver are in that room.

The server will parse the 'client_sends_message' event and verify the auth. JWT is valid. 

- If the message destination is ChatGPT user - the message will be forwarded to OpenAI API.

- If the message destination is another user, that is currently offline - the message will be cached 
  in Redis  and forwarded to the user once he is online 
  
- In other cases the message will be immediately delivered to the target, the server will publish 
  the 'received_message' event to the Room that contains the target user and the message sender and the message
  will reach its destination. 
  

### Connection Health Check

User is considered to be 'online' after he connected until he performs the disconnection procedure - 
once the client emits <b>'client_disconnection'</b> event he is removed from the 'online users' list
and the server publishes the <b>'user_has_gone_offline'</b> event to notify all other clients.

Yet the connection can be terminated by client without publishing the 'client_disconnection' event. 
Therefore the chat server expects each client (that is currently online) to emit 
the <b>'connection_alive'</b> event every X seconds (configurable on the server side, 
set to 6 seconds by default).

The chat server keeps a dictionary, that maps the user name to the last time the 'connection_alive'
event was received from that user. Each time a new 'connection_alive' event is received, the dictionary
is updated.

In a separate thread every N seconds the server verifies, for each user, that the delta between
the current server time and the last time the the 'connection_alive'
event was received doesn't exceed X seconds - if it does, the user is considered to be disconnected, 
the JWT token is deleted, messages from that user won't be forwarded to other users (until he re login)
and 'user_has_gone_offline' event will be emitted to all other users. 


## Events :

### Client - to - server:

1. 'join' - client sends a request to join the specified chat room
2. 'client_sends_message' - client sends a message to the selected chat room (destination in message content)
3. 'connection_alive' - event used for connection health check validation 
4. 'client_disconnection' - client terminates connection

### Server - to - client:

1. 'received_message' - a message was received from one of the clients, will be published by the server to the selected chat room
2. 'new_user_online' - new client has connected, all clients that are currently online are notified
3. 'user_has_gone_offline' - user has decided to disconnect (deliberately) or lost connection
4. 'ai_response_received' - a message was received from ChatGPT AI



### Client Side Structure

<img src="https://github.com/EvgeniyJeka/ISeeCubes/blob/documentation_27_2_23/chat_client_chart.jpg" alt="Screenshot" width="1000" />

The client consists of:

1. <b>ChatClient</b> - application main GUI. Contains the app skin - the contacts list, the buttons and all the methods
    that are used to handle button clicks. Opens secondary windows on request - 
    MessageBox (when user initiates a conversation with another user) and LoginWindow (when user wishes to log in).
    
    Note - each conversation is handled in a separate thread, so the user will be able to have several conversations
    simultaneously, to each time the 'Chat With' button is clicked a new thread starts and a new MessageBox window opens. 
    
    One of the properties of the ChatClient is an instance of ClientAppCore, so the ChatClient will be able to use
    all the App Core methods and pass the instance to other components, if required. 

2. <b>ClientAppCore</b> - application core methods. This class contains the methods required to communicate with the 
    server side - send a log in request, send a connection request and receive feeds from the server in response.
    When the 'start_listening_loop' method is called the ClientAppCore starts to listen to all the incoming 
    events (web socket messages) in a separate thread and handle each event accordingly. 
    
    The ChatClient calls <b>'start_listening_loop'</b> method when the 'connect' button is clicked. 
    
    Note - one of the events that can be handled in ClientAppCore is 'received_message' - in that case 
    ClientAppCore opens an instance of MessageBox in a separate thread (it happens when another user sends a message
    to the current user).
    
    While handling the events ClientAppCore is responsible to make the required adjustments in ChatClient UI elements - 
    to color user names of  users that are currently online in green, to enable/disable buttons e.t.c. 

3. <b>MessageBox</b> - the MessageBox class is responsible for the Message Box UI component. 
   Message box opens each time the user receives a message or wishes to send one. 
   It contains the 'Send' button - once the button is clicked, the 'client_sends_message' event is emitted
   and the text that the user has entered is sent to the destination 

4. <b>LoginWindow</b> - the LoginWindow class is responsible for Login Window UI component. 
   Login Window opens each time the 'Login' button is clicked. It contains the 'Confirm' button,
   once it is clicked an HTTP 'log in' request is sent.
   
   
### Recovery Flow

The system has the ability to recover after a failure. 
The handling for the cases that are supported at the moment is described bellow:

1. <b>Chat Server crash</b> - handled on the client side. The client is continuously  sending the <b>'connection_alive'</b>
   event while connected. When Chat Server is down the client fails to send the event (since websocket session is terminated)
   and <b>BadNamespaceError</b> exception is raised. For the client it means that the Chat Server is down.  
   
   Once the Chat Server is down the user is logged out, 'Connection status' label changes from 'Online'
   to 'Server Error', the Contacts List is cleared and the user is presented with the relevant error message.
   The user is asked to re login ('Login' button is enabled) and reconnect.
   Note - while the server is down the option to send messages is blocked on the client side to prevent data loss. 
   
2. <b>Redis DB crash</b> - handled on server side and on the client side.
   The main goal is to prevent a situation in which the end users sending messages that can't be saved to Redis
   (when required) and even forwarded, since the sender's identity can't be validated using JWT. 
   
   Chat Server won't start if Redis DB is unavailable. In case Redis DB becomes unavailable while Chat Server 
   is running the Chat Server process is terminated, as a result client fails to send the 'connection_alive' event 
   via websocket (since the session is terminated). Client notifies the user about the situation with an error message -
   <b>"Error: Chat Server is temporary down. Please re login and re connect."</b>
   Once Redis DB is available the Chat Server needs to be restarted.
    
    
     








