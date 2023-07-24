# I See Cubes - Server Side STP 

This Test Plan covers the vast majority of the server side features.
Most of the Test Scenarios are automated (work is in progress at the moment) - the emphasis 
is on regression and e2e tests, that are needed for future development. 

The tests are implemented on Python and based on PyTest framework. 

The general approach is 'Black Box' testing - the tests emulate a client, they send 
HTTP requests and web socket messages to Chat Server, parse it's responses and emitted messages
in the same way the desktop client does and verify the output against the expected. 

NOTE: The goal of this STP is to maximize the test coverage.  At the moment not all features 
that are covered in this STP are implemented - there is no error handling for databases crash, for example. 
Future versions of the project are to provide solutions for those issues.



### 1. Authorization
    1.1 Sign in - Happy Path
    1.2 Sign out - verify authorization token expired after user signs out and can't be reused (JWT expires after sign out)
    1.3 Negative - verify user can't sign in with incorrect password or with other user password 
    1.4 Expired token - verify messages sent with expired authorization token are declined 
    1.5 Invald token (including blank token) - verify messages sent with invalid token are declined 
    1.6 Initiating connection - verify client can connect to Chat Server websocket only with a valid JWT
    1.7 Verifying valid JWT is required to get server data (contacts list e.t.c.) from the Chat Server
      
### 2. Getting initial data from the server 
    2.1 Verifying the list of all existing users provided by Chat Server upon request
    2.2 Verifying the list of list of Room Names provided by Chat Server upon request
    2.3 Verifying the list of users that are currently online provided by Chat Server upon request
     
### 3. Sending messages from one user to another 
    3.1   Sending a single message from user A to user B while both are online 
    3.2   Sending several messages from user A to user B while both are online 
    3.3   Verifying only the user that the message was sent to gets the message 
    3.4   Sending one message from user A to user B and sending two messages from user A to user C 
    3.5   Verifying messages sent to a users that are currently offline are cached
    3.5.1 Sending a message to a user while he is offline, sending another one when he is online - verifying both are received  
    3.6   Verifying messages can be sent after relogin 
    3.7   Verifying messages sent to non-existing users doesn't disrupt the server workflow (negative) 

### 4. Status updates 
    4.1 Verifying that all connected users receive an update via a web socket message when a new user is online
    4.2 Verifying that all connected users receive an update via a web socket message when a user goes offline
   
### 5. Keep Alive signals 
    5.1 Verifying client that are not sending the signal for more then X seconds is automatically disconnected
    5.2 Verifying client that is sending the signal every X seconds remains connected 
    
### 6. Chat Server restarted (recovery flow) - T.B.D.
    6.1 Verify all users that are currently connected are logged out when the Chat Server is restarted 
    6.2 Verify users can relogin after Chat Server restart 
    6.3 Verify users can message each other after Chat Server restart (covers reconnection to databases) 
    6.4 Verify messages that were cached in Redis aren't lost after Chat Server restart
    
    (T.B.D.: Recovery flow - consider to LOG OUT ALL USERS when the Chat Server starts)
    
### 7. Databases unavailable (critical error handling) - T.B.D.
    7.1 Verify all users that are currently connected are logged out when Postgress SQL DB becomes unavailable
    7.2 Verify all users that are currently connected are logged out when Redis DB becomes unavailable 
    7.3 Verify users get a relevant error message when trying to relogin while databases are unavailble 
    
### 8. Third party integration (ChatGPT and other integrated chat bots) - T.B.D.
    8.1 Verify messages sent to ChatGPT by end users are forwarded to ChatGPT API 
    8.2 Verify messages sent by ChatGPT to end users are forwarded to end users by Chat Server
    8.3 Verify each user gets a response for his prompt from ChatGPT API (when several users 
    are writing to ChatGPT simultaneously).


    