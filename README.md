# Music Bingo: mingo
This is a Python implementation of the Music Bingo bar game, aka MINGO. 

- It is command-line oriented. 
- It requires a subscription to the
Spotify music service. A Spotify application that is configured using the Spotify Developer API web page is necessary.
- Access to the Spotify API is done using the Spotipy library that wraps the actual Spotify APIs.

Before running the code you need to set some environment variables that Spotipy uses
for access to the Spotify API. These are obtained from the Spotify API dashboard after
you sign on.

The environment variables can be set from a script. For example, save the following in set_env.sh.

`export SPOTIPY_CLIENT_ID="your-app-client-id"`

`export SPOTIPY_CLIENT_SECRET="your-app-client-secret"`

`export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8080"`

Run this script as follows so it sets the values in the current shell where it is being executed:

`. ./set_env.sh`
