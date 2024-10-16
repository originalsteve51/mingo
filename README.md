# Music Bingo: mingo
This is a Python implementation of the Music Bingo game, aka MINGO.
Credit goes to [Floris den Hengst](https://github.com/florisdenhengst), who proposed a design and wrote code that I used when I made this program.

Notes about this Mingo game:
- It is command-line oriented. 
- It requires a subscription to the
Spotify music service. A Spotify application that is configured using the Spotify Developer API web page is necessary.
- Access to the Spotify API is done using the Spotipy library that wraps the actual Spotify APIs.
- When you start the program, Spotipy creates a file named .cache that
contains information pertaining to your login to Spotify. When the first login
occurs, your terminal screen may flash briefly. Once the .cache file is present,
this flash does not occur again.

Before running the code you need to set some environment variables that Spotipy uses
for access to the Spotify API. These are obtained from the Spotify API dashboard after
you sign on.

The environment variables can be set from a script. For example, save the following in set_env.sh.

`export SPOTIPY_CLIENT_ID="your-app-client-id"`

`export SPOTIPY_CLIENT_SECRET="your-app-client-secret"`

`export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8080"`

Run this script as follows so it sets the values in the current shell where it is being executed:

`. ./set_env.sh`
