#!/bin/zsh

# The Spotipy library requires the following information. This info can be passed directly in the 
# program code but it should be isolated from source code by scripting it as
# shell environment variables.
export SPOTIPY_CLIENT_ID="your-app-id-goes-here"
export SPOTIPY_CLIENT_SECRET="your-client-secret-goes-here"
export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8080"

./python mingo.py
