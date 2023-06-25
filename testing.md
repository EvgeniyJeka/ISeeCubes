# I See Cubes - Server Side STP :

### 1. Authorization
    1.1 Sign in - Happy Path
    1.2 Sign out - verify authorization token expired after user signs out and can't be reused
    1.3 Negative - verify user can't sign in with incorrect password or with other user password 
    1.4 Status Change - verify user's status is set to 'online' after he signs in and published to all other users
    1.5 Status Change - verify user's status is set to 'offline' after he signs out and published to all other users
    1.6 Expired token - verify messages sent with expired authorization token are declined (token expires after sign out)
    1.6 Invald token (including blank token) - verify messages sent with invalid token are declined 
    
    
    