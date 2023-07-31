# 1 General Description

<b>QaService</b> - a framework and a set of automated tests that cover
the server side of the "I See Cubes" application, the Chat Server. 

The purpose of the "QaService" is to perform automated testing of the Chat Server for the "I See Cubes" 
application.

The tests are not part of the "I See Cubes" project (since those aren't unit tests), but a set of 'black box' 
tests - each test generates an <b>INPUT</b> for the Chat Server and verifies the produced <b>OUTPUT</b>.

The general approach is 'Black Box' testing - the tests emulate a client, they send 
HTTP requests and web socket messages to Chat Server, parse it's responses and emitted messages
in the same way the desktop client does and verify the output against the expected. 

In some tests several instances of client emulators are running simultaneously in several threads   
while the tested features are verified - messages are delivered to the right client, 
status updates and other events are published via web socket by Chat Server as expected e.t.c.
 
The tests are based on <b>Pytest</b> framework and an run in a <b>Docker</b> container, 
"i_see_cubes_tests_container". Test results are saved into the 'test_results_report.txt' 
file that is created during the test run and saved in "i_see_cubes_tests_container" volumes. 

Test container configuration and env. variables are written in the 'yml' files. The docker image is built 
(if missing) and test container is started together with Chat Server container when one of the 'yml' files 
is executed by the Docker Compose tool.

The tests can be integrated into Jenkins based CI flow - for example, the following command will
initiate an execution of all "sanity" tests, and the docker container exit code '0' will indicate,
that all tests passed :

<b>docker-compose -f docker-compose-sanity_tests_executed.yml up -d</b>


# 2 Test Groups and Server Side STP 

The tests are divided into several groups according to the STP below.

Each test group can be executed separately. For example - in order to execute
all tests marked as 'sanity' we can either use the yml file 'docker-compose-sanity_tests_executed.yml'
or use the following CMD command in  "i_see_cubes_tests_container" configuration:

<b>command: ["pytest", "-v", "-m", "sanity"]</b>

#### Available Test Groups (listed in pytest.ini):
    sending_messages: sending messages from one user to other users, caching messages for offline users
    status_updates: getting notifications on other users statuses (online/offline) via web socket
    authorization: authorization mechanisms are verified
    keep_alive_signals: verifying client remains connected only as long as he sends 'keep alive' signals
    server_data_provided: verifying server provides to client all the relevant data upon request
    sanity: sanity tests
    end2end: end to end tests, full flow
    regression: full regression test run, most of all existing automated test cases


The Test Plan below covers the vast majority of the server side features.
Most of the Test Scenarios are automated (work is in progress at the moment) - the emphasis 
is on regression and e2e tests, that are needed for future development. 

<b>Tests that are already automated</b>:

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
  
  
<b>Tests that are can be performed manually only at the moment:</b>  
    
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


    