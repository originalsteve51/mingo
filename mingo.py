"""
MIT License

Copyright (c) 2019 Floris den Hengst
Copyright (c) 2021 Stephen Harding

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import random
import cmd
import webbrowser

import csv
import math
import sys
from sys import stdout
from pathlib import Path
import pickle

import spotipy
from spotipy.oauth2 import SpotifyOAuth

#-----------------------------------
# A few global settings follow below
# @TODO Get rid of global values
#-----------------------------------
gridsize = 5
stepping = 16
save_path = './cards.html'
input_file = './mingo_input1.csv'
current_dir = os.getcwd()
game_state_pathname = './game_state.bin'



#-----------------------------------------------------------
# Spotify is a class that provides access to the Spotify API
# The spotipy library performs its magic here by using values
# found in the environment to authenticate the user. Once
# authenticated, the api can be called.
#-----------------------------------------------------------
class Spotify():
    def __init__(self):
        ascope = 'user-read-currently-playing,\
                playlist-modify-private,\
                user-read-playback-state,\
                user-modify-playback-state'
        ccm=SpotifyOAuth(scope=ascope, open_browser=True)
        self.sp = spotipy.Spotify(client_credentials_manager=ccm)

#-------------------------------------------------------------------
# Playlist class
#-------------------------------------------------------------------
class Playlist():
    def __init__(self, sp):
        self.sp = sp
        self.track_set = set(())

    def get_playlists(self):
        results = self.sp.current_user_playlists(limit=50)
        lists = {}
        for i, item in enumerate(results['items']):
            lists[str(i)] = [item['name'], item['id']]
        return lists

    def duplicate_detect(self, track_name):
        is_duplicate = False
        if track_name in self.track_set:
            is_duplicate = True
        else:
            self.track_set.add(track_name)
        return is_duplicate


    def playlist_processing(self, pl_id, m_writer=None):
        offset = 0
        while True:
            response = self.sp.playlist_items(pl_id,
                                        offset=offset,
                                        fields='items.track.name, items.track.id, items.track.artists.name, total',
                                        additional_types=['track'])

            if len(response['items']) == 0:
                break

            for idx in range(0, len(response['items'])):
                track = response['items'][idx]['track']
                artist_name = response['items'][idx]['track']['artists'][0]['name']
                if not self.duplicate_detect(track['name']):
                    # track_id = track['id']
                    # track_urn = f'spotify:track:{track_id}'
                    # track_info = sp.track(track_urn)
                    # artist_name = track_info['album']['artists'][0]['name']
                    # print(track['name'], track['id'], artist_name)
                    if m_writer:
                        m_writer.writerow([idx+offset, idx+offset, track['name'], track['id'], artist_name])
                else:
                    print(f"The track named {track['name']} by {artist_name} was not used because its name is very similar to another track already used.")
            offset = offset + len(response['items'])
            print(f'Processed {offset} records so far...')
        print(f'Total number of records processed: {offset}')


    def process_playlist(self, pl_index, save_to_file):
        playlist = self.get_playlists()[f"{pl_index}"]
        print(f'{playlist[0]}')
        pl_id = f'spotify:playlist:{playlist[1]}'

        if save_to_file:
            with open('mingo_input1.csv', mode='w') as mingo_file:
                m_writer = csv.writer(mingo_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                m_writer.writerow([f'{playlist[0]}', 'track name', 'track id'])
                self.playlist_processing(pl_id, m_writer)
        else:
            self.playlist_processing(pl_id)

#-------------------------------------------------------------------
# Player class
#-------------------------------------------------------------------
class Player():
    def __init__(self, track_ids, sp):
        self.active_player = None
        self.track_ids = track_ids
        self.sp = sp

    def show_available_players(self, list_all_players=True):
        res = self.sp.devices()
        player_count = len(res['devices'])
        print(f'Your account is associated with {player_count} players.')
        for idx in range(player_count):
            if list_all_players:
                player_data = f"{res['devices'][idx]['name']},{res['devices'][idx]['type']}"
                active_msg = 'Inactive'
                if res['devices'][idx]['is_active']:
                    active_msg = 'Active'
                print(f'{idx}: {player_data}, {active_msg}')
            if res['devices'][idx]['is_active'] and self.active_player is None:
                self.active_player = res['devices'][idx]['id']
                print(f'Selected active music player: ', {res['devices'][idx]['name']})

    def play_track(self, track_index):
        try:
            print(f'Playing track on music player id: {self.active_player}')
            self.sp.start_playback(uris=[f'spotify:track:{self.track_ids[track_index]}'], 
                            device_id=self.active_player)
        except Exception as e:
            display_player_exception(e)

    def resume_track(self, track_index, position_ms):
        try:
            self.sp.start_playback(uris=[f'spotify:track:{self.track_ids[track_index]}'], 
                            device_id=self.active_player, 
                            position_ms=position_ms)
        except Exception as e:
            display_player_exception(e)

    def set_volume(self, volume_pct):
        self.sp.volume(volume_pct)

    def pause_playback(self):
        self.sp.pause_playback()


#-------------------------------------------------------------------
# Card class
#-------------------------------------------------------------------
class Card():
    def __init__(self, sheet, playlist_name):
        # sheet is a 25 element list with 24 track numbers and a url. These
        # represent 5 x 5 element rows of the Mingo board. The center element
        # is the url, which represents a free square.
        self.sheet = sheet
        self.playlist_name = playlist_name

        # @TODO The sheet has rows, columns, diagonals, and corners. Game progress will
        # be recorded as tracks are played by marking tracks in these places.
        #self.rows = dict()
        #self.cols = dict()
        #self.diags = dict()
        #self.corners = dict()

    def as_html(self, f=stdout, readable=True):
        if readable:
            newline = '\n'
        else:
            newline = ''
        f.write("<table>"+newline)
        f.write("<tr>"+newline)
        bingo = ["<th>{}</th>".format(l) for l in list('MINGO')]
        for th in bingo:
            f.write(th)
        f.write("</tr>"+newline)
        for r in range(gridsize):
            f.write("<tr>"+newline)
            for c in range(gridsize):
                cell = r * gridsize + c
                cell = self.sheet[cell]
                # Check length of cell string. apply a smaller fontsize if it's
                # too long, this tries to keep a card short enough to fit on a page
                # without running to the top of the next page.
                if len(cell) > 25:
                    font_size = 'class="long-text-cell"'
                else:
                    font_size = ""
                columnstring = f'<td {font_size}>' + cell + "</td>" + newline
                f.write(columnstring)
            f.write("</tr>\n")
        f.write("</table>"+newline)

    def view_html(self):
        filename = 'file://'+current_dir+'/cards.html'
        webbrowser.open_new_tab(filename)


#-------------------------------------------------------------------
# CardFactory class
#-------------------------------------------------------------------
class CardFactory():
    def __init__(self, input_file) -> None:
        self.center_figure = '<img src="center-img-small.png"/>'
        self.input_titles = []
        self.input_ids = []
        self.input_track_ids = []
        self.input_artists = []
        with open(input_file, 'r') as f:
            r = csv.reader(f, delimiter=',', quotechar='"')
            playlist_name_row = next(r)
            self.playlist_name = playlist_name_row[0]
            for row in r:
                self.input_artists.append(row[4])
                self.input_track_ids.append(row[3])
                # Shorten title by removing stuff after a hyphen that is preceded by
                # a space. Spotify titles often include meta-info like when a song
                # was remastered, and we don't want this on the gamecard. They seem
                # to always delimit the meta-info with a space-hyphen-space pattern. Some
                # song titles include hyphens, but they typically are not preceded
                # with a space.
                short_title = row[2].split(' - ', 1)[0]
                self.input_titles.append(short_title)
                self.input_ids.append(row[1])

        self.n_titles = len(self.input_titles)
        self.titles = []
        self.track_ids = []
        self.track_info = dict()
        for i, w in enumerate(self.input_titles):
            self.titles.append(f'{w}')
            self.track_ids.append(self.input_track_ids[i])
            self.track_info[i] = f'{w}'

    def make_card(self):
        # print('Creating mingo card from: ' + str(len(self.titles)) + ' song titles')
        sheet = random.sample(self.titles, gridsize**2 - 1)
        sheet.insert(math.ceil(len(sheet)/2), self.center_figure) 
        return Card(sheet, self.playlist_name)

    def get_track_ids(self):
        return self.track_ids

               
#-------------------------------------------------------------------
# Game class
#-------------------------------------------------------------------
class Game():
    def __init__(self, n_cards, sp):
        self.n_cards = n_cards
        self.sp = sp
        # self.make_cards()

        card_factory = CardFactory(input_file)
        self.playlist_name = card_factory.playlist_name
        self.cards = dict()
        for _ in range(n_cards):
            self.cards[_] = card_factory.make_card()
        self.track_ids = card_factory.get_track_ids()
        self.track_info = card_factory.track_info
        self.track_artists = card_factory.input_artists
        self.player = Player(self.track_ids, sp)

        # The state of a game is determined by played_tracks and unplayed_tracks
        # To restore a suspended game, these lists are populated from a file named
        # game_state.bin. This file is updated every time a track is played. 
        # Also, game_state.bin is re-initialized with empty played_tracks
        # and a full unplayed_tracks every time a makegame command is
        # issued to make a new game. 
        self.played_tracks = []
        self.unplayed_tracks = []
        self.state = []
        
        self.paused_at_ms = None
        self.current_track_idx = None
        for idx in range(len(self.track_ids)):
            self.unplayed_tracks.append(idx)
        print(f'Created a Mingo game with {n_cards} cards')

    def make_cards(self):
        pass


    def write_game_state(self):
        path = Path(game_state_pathname)
        with open(path, 'wb') as fp:
            pickle.dump(self, fp)


    def get_card(self, card_num):
        if card_num > self.n_cards-1 or card_num < 0:
            raise Exception(f'There are {self.n_cards} cards in this game, \
numbered 0 through {self.n_cards - 1}. Try again.')
        else:
            return self.cards[card_num] 
    

    def show_status(self):
        if self.played_tracks:
            unordered_tracks = list(self.played_tracks)
            self.played_tracks.sort()
            print(f'Played {self.played_tracks} so far...')
            self.played_tracks = unordered_tracks
        else:
            print('No tracks have been played yet')

    def play_track(self):
        if len(self.unplayed_tracks) == 0:
            print('The game is over. All tracks have been played.')
            return

        track_idx = random.choice(self.unplayed_tracks)
        self.unplayed_tracks.remove(track_idx)
        self.played_tracks.append(track_idx)
        print(f'Played so far: {self.played_tracks}')
        now_playing = self.track_info[track_idx]
        artist = self.track_artists[track_idx]
        self.current_track_idx = track_idx
        print(f'Now playing: "{now_playing}" by "{artist}"')
        self.player.play_track(track_idx)

    def pause(self):
        self.player.pause_playback()
        self.paused_at_ms = self.currently_playing()[0]

    def resume(self):
        if self.paused_at_ms:
            self.player.resume_track(self.current_track_idx, self.paused_at_ms)
            self.paused_at_ms = None
        else:
            print('Nothing was paused, so cannot resume!')


    def currently_playing(self):
        track = self.sp.current_user_playing_track()
        is_playing = track['is_playing']
        progress = track['progress_ms']
        return progress, is_playing

    def view_in_browser(self, card_num=None):
        '''
        Renders a mingo card using html, saves the html to a file, and shows it in the default browser.

            parameters:
                card_num: The index of a mingo card to render. If None, show all cards.

            returns:
                None
        '''
        try:
            with open(save_path, 'w') as f:
                f.write("<html>")

                # First write a css that provides a good table rendering for mingo cards.
                # This also will cause one card per page when printing the browser
                # display of the cards.
                f.write("""
                <head>
                    <style>
                        td {
                            width: 120px;
                            height: 50px;
                            padding: 2px;
                            overflow: hidden;
                            text-align: center;
                            vertical-align: middle;
                            border: 1px solid black;
                            font-size: 18pt;
                            font-family: Arial, Helvetica, sans-serif;
                        }
                        .long-text-cell{
                            font-size: 15pt;
                        }
                        img {
                            max-height: 50px;
                        }
                        br.space{
                            margin-top: 70px;
                        }
                        @media print{
                            br.page{
                                page-break-before: always;
                            }
                        }
                    </style>
                </head>
                <body>
                """)
                if not card_num:
                    for i in range(self.n_cards):
                        # Following prints one card per page. The css 'page' provides
                        # a page-break when printed. But this only actually works
                        # with Firefox, according to my testing. So use Firefox with
                        # this program.
                        card = self.get_card(i)
                        f.write(f"<h3>{card.playlist_name}, Card number {i}  </h3>")
                        card.as_html(f, False)
                        f.write("<br class='page'/>")
                        """
                        # Following prints two cards per page. This needs a very small
                        # font that old people like me cannot see well.
                        if (i+1) % 2 == 0:
                            f.write("<br class='page'/>")
                        else:
                            f.write("<br class='space'/>")
                        """
                else:
                    card = self.get_card(int(card_num))
                    f.write(f"<h3>{card.playlist_name}, Card number {card_num} </h3>")
                    card.as_html(f, False)
                    f.write("<br class='page'/>")

                f.write("\n")

            filename = 'file://'+current_dir+'/cards.html'
            browser = webbrowser.get('firefox')
            browser.open(filename)
            # The call below was originally used. It opened the cards in the default browser,
            # which is Chrome on my machine. 
            # But Chrome has problems with the css print definition
            # for br.page that is used to insert a page break when printing. Firefox works, so
            # I needed to specify non-default browser firefox as seen above...
            # @TODO Remove Firefox and test to see what happens.
            #webbrowser.open_new_tab(filename)
        except Exception as error:
            # @TODO Untested below. I think if I remove Firefox I will get an exception.
            # The line of code below will use the default browser in the absence of Firefox,
            # I think. I should check the specific exception and only display the default
            # browser when Firefox is not available. Then I should inform the user that
            # Firefox should be made available.
            webbrowser.open_new_tab(filename)
            print(error)


#-------------------------------------------------------------------
# ExitCmdException class - Just so we have a good name when breaking
# out of the command loop with an Exception
#-------------------------------------------------------------------
class ExitCmdException(Exception):
    pass 


#-------------------------------------------------------------------
# CommandProcessor class - Define the command language here. This
# extends the Python Cmd class, which brilliantly handles keyboard
# input by recognizing commands and dispatching them.
#-------------------------------------------------------------------
class CommandProcessor(cmd.Cmd):
    prompt = '(No active game)'
    def __init__(self):
        super(CommandProcessor, self).__init__()
        self.active_game = None
        spotify = Spotify()
        self.sp = spotify.sp
        self.pl = Playlist(spotify.sp)

        # Start by displaying the available playlists
        self.do_playlists()


    """Process commands related to Spotify playlist management for the game of MINGO """
    def do_playlists(self, sub_command=None):
        """Display all Spotify playlists for the authorized Spotify user."""
        playlists = self.pl.get_playlists()
        print('\nThese are your playlists:')
        for k in playlists.keys():
            print(f'{k}: {playlists[f"{k}"][0]}')
        print('\nSave a list using the "savelist" command followed by a list number.\nAfter saving a list, you can make a set of Mingo cards with the listed songs.')

    def do_savelist(self, list_number):
        """Save the names and ids of tracks from a Spotify playlist to a csv file. The number of the playlist must be supplied."""
        if list_number:
            self.pl.process_playlist(list_number, True)
            print('\nNow you can make a set of Mingo cards using the songs in the list you just saved.')
            print('Use the "makegame" command to make a set of Mingo cards.')
        else:
            print('You must enter the number of a playlist to save its tracks')
    
    def do_showlist(self, list_number):
        """Show the names of tracks in a Spotify playlist."""
        if list_number:
            self.pl.process_playlist(list_number, False)
        else:
            print('You must enter the number of a playlist to show its tracks')
    
    def do_status(self, line):
        """Show a list of track ids played so far."""
        if self.active_game:
            self.active_game.show_status()
        else:
            print('There is not an active game, so no status is available')

    def do_userinfo(self, line):
        """Show the name of the signed-on Spotify user whose playlists are to be used to generate Mingo games."""
        print(self.pl.sp.me()['display_name'])

    def do_makegame(self, num_cards):
        """Use the currently active playlist to generate a specified number of Mingo cards."""
        if not num_cards:
            num_cards = '10'

        try:
            self.active_game = Game(int(num_cards), self.sp)
            self.active_game.write_game_state()
            self.prompt = f'({self.active_game.playlist_name})'
            print(f'A new game has been made with {num_cards} cards.')
            print('\nYou can use the "gamecards" command to display and print the Mingo cards for this game.')
            print('You can begin playing tracks in random order by using the "nexttrack" command for each track.')
        except Exception as error:
            print(error)

    def do_continuegame(self, _):
        """If you stopped playing a game and exited this program, its state is
        saved. Use this command to resume playing a stopped game from when you stopped it.
        """
        
        try:
            self.active_game = restore_game_state()
            self.prompt = f'({self.active_game.playlist_name})'

        except Exception as error:
            print(error)    

    def do_view(self, card_num=None):
        """Specify a card number to view a single Mingo card from the active Mingo game. 
        If no number is specified, all cards are displayed."""
        if self.active_game:
            self.active_game.view_in_browser(card_num)
        else:
            print('There is not an active game. Create one using "makegame" and try again.')  

    def do_getinfo(self, _):
        """Display info about the currently active game."""
        if self.active_game:
            print(f'The currently active game has {self.active_game.n_cards} cards.')
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_gamecards(self, _):
        """Open a browser and display all gamecards, ready for printing."""
        if self.active_game:
            self.active_game.view_in_browser()
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_nexttrack(self, _):
        """Play a randomly selected track from the active Mingo game."""
        if self.active_game:
            self.active_game.play_track()
            self.active_game.write_game_state()
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_pause(self, _):
        """Pause the song that is currently playing. Use resume to resume playing."""
        if self.active_game:
            self.active_game.pause()
            resume_at = self.active_game.currently_playing()[0]
            print(f'Paused after {resume_at} msec')
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  
    
    def do_resume(self,_):
        """If a song has been paused, this command resumes playing the song."""
        if self.active_game:
            self.active_game.resume()
        else:
               print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_musicplayers(self, _):
        """List the music players that Spotify can use to play tracks. The first such player
        that is marked 'Active' in Spotify is selected to play your songs."""
        if self.active_game:
            self.active_game.player.show_available_players()
        else:
            print('There is not an active game, so players cannot be listed.')

    def do_currentlyplaying(self, _):
        """Shows the progress info for the currently playing track."""
        if self.active_game:
            progress = self.active_game.currently_playing()[0]
            print(f'The track has been playing for {progress} msec')
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    # I removed the exit via ctrl-d in favor of the quit command or ctrl-c. These are 
    # both handled in a way that they are sort of quiet.  
    #def do_EOF(self, line):
    #    """Press ctrl-d to exit this program"""
    #    try:
    #        if self.active_game and self.active_game.currently_playing()[1]:
    #            self.active_game.pause()
    #    except:
    #        pass
    #    return True


    def do_quit(self, args):
        """ 
        Quits the game, stopping the player if it's running and
        cleaning up as necessary
        """
        cleanup_before_exiting(self)
        raise ExitCmdException()

#-----------------------------------------
# Global function definitions follow below
#-----------------------------------------
def display_player_exception(e):
    exception_name = e.__class__.__name__
    if exception_name == 'SpotifyException':
        print(f'\n{exception_name}: \nMake sure the device you intend to play the track on is available and try again.')
    else:
        display_general_exception(e)

def display_general_exception(e):
    exception_name = e.__class__.__name__
    if exception_name == 'ReadTimeout' or exception_name == 'ConnectionError':
        print(f'\n{exception_name}:\nAn error occurred that indicates that you are not connected to the internet.')
    else:
        print(f'\n{exception_name}:\nAn unexpected error occurred.')

def cleanup_before_exiting(command_processor):
    if command_processor.active_game and command_processor.active_game.currently_playing()[1]:
        command_processor.active_game.pause()

def restore_game_state():
    path = Path(game_state_pathname)
    with open (path, 'rb') as fp:
        restored_game = pickle.load(fp)
    return restored_game

#-----------------------------------------
# The main processing is declared below
#-----------------------------------------
if __name__ == '__main__':
    continue_running = True
    cp = None
    while continue_running:
        # Enter the command loop, handling Exceptions that break it. Some Exceptions
        # can be handled, like losing the network. We give the user a chance
        # to correct such errors. If the user believes an Exception
        # has been corrected, the command loop will restart.
        try:
            if cp is None:
                cp = CommandProcessor()
            cp.cmdloop()
        except KeyboardInterrupt:
            print('Interrupted by ctrl-C, attempting to clean up first')
            try:
                cleanup_before_exiting(cp)
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as e:
            exception_name = e.__class__.__name__
    
            if exception_name == 'ExitCmdException':
                continue_running = False
                print('\nExiting the program...')
                continue
            else:
                display_general_exception(e)
            
            choice = input('Try correcting this problem and press "Y" to try again, or any other key to exit. ')
            if choice.upper() != 'Y':
                continue_running = False
                print('Exiting the program')