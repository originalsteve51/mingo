"""
MIT License

Copyright (c) 2021 Stephen Harding
Copyright (c) 2019 Floris den Hengst

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

import random
import cmd
import webbrowser
from pprint import pprint

import csv
import math
from sys import stdout
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Initial global settings
numbersheets = 6
gridsize = 5
stepping = 16
save_path = './cards.html'
input_file = './mingo_input1.csv'

class Spotify():
    def __init__(self):
        ascope = 'user-read-currently-playing,\
                playlist-modify-private,\
                user-read-playback-state,\
                user-modify-playback-state'
        ccm=SpotifyOAuth(scope=ascope, open_browser=True)
        self.sp = spotipy.Spotify(client_credentials_manager=ccm)

class Playlist():
    def __init__(self, sp):
        self.sp = sp

    def get_playlists(self):
        results = self.sp.current_user_playlists(limit=50)
        lists = {}
        for i, item in enumerate(results['items']):
            lists[str(i)] = [item['name'], item['id']]
        return lists

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
                # track_id = track['id']
                # track_urn = f'spotify:track:{track_id}'
                # track_info = sp.track(track_urn)
                # artist_name = track_info['album']['artists'][0]['name']
                print(track['name'], track['id'], artist_name)
                if m_writer:
                    m_writer.writerow([idx+offset, idx+offset, track['name'], track['id'], artist_name])
            
            offset = offset + len(response['items'])
            print(f'Wrote {offset} records so far...')
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

class Player():
    def __init__(self, track_ids, sp):
        self.macbook_player = '9f2e02f26803b9fa62a12fc3c6ffe904c8115005'
        self.echo_show_player = 'f40ca59011ba5f2e7c9f45e350d218ca9a517cda'
        self.track_ids = track_ids
        self.sp = sp

    def show_available_players(self):
        res = self.sp.devices()
        pprint(res)

    def play_track(self, track_index):
        try:
            self.sp.start_playback(uris=[f'spotify:track:{self.track_ids[track_index]}'], 
                            device_id=self.macbook_player)
        except Exception as error:
            print('Make sure the device you intend to play the track on is available and try again.')

    def resume_track(self, track_index, position_ms):
        try:
            self.sp.start_playback(uris=[f'spotify:track:{self.track_ids[track_index]}'], 
                            device_id=self.macbook_player, 
                            position_ms=position_ms)
        except Exception as error:
            print('Make sure the device you intend to play the track on is available and try again.')

    def set_volume(self, volume_pct):
        self.sp.volume(volume_pct)

    def pause_playback(self):
        self.sp.pause_playback()


class Card():
    def __init__(self, sheet, playlist_name):
        # sheet is a 25 element list with 24 track numbers and a url. These
        # represent 5 x 5 element rows of the Mingo board. The center element
        # is the url, which represents a free square.
        self.sheet = sheet
        self.playlist_name = playlist_name

        # The sheet has rows, columns, diagonals, and corners. Game progress will
        # be recorded as tracks are played by marking tracks in these places.
        self.rows = dict()
        self.cols = dict()
        self.diags = dict()
        self.corners = dict()

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
                columnstring = '<td>' + cell + "</td>" + newline
                f.write(columnstring)
            f.write("</tr>\n")
        f.write("</table>"+newline)

    def view_html(self):
        filename = 'file:///Users/stephenharding/mycode/Python/spotify_3.9/mingo/cards.html'
        webbrowser.open_new_tab(filename)


class CardFactory():
    def __init__(self, input_file) -> None:
        self.center_figure = '<img src="https://raw.githubusercontent.com/florisdenhengst/music-bingo/master/center-img-small.png"/>'
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
                self.input_titles.append(row[2])
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
        print('Creating mingo card from: ' + str(len(self.titles)) + ' song titles')
        sheet = random.sample(self.titles, gridsize**2 - 1)
        sheet.insert(math.ceil(len(sheet)/2), self.center_figure) 
        return Card(sheet, self.playlist_name)

    def get_track_ids(self):
        return self.track_ids

               
class Game():
    def __init__(self, n_cards, sp):
        self.n_cards = n_cards
        self.sp = sp
        card_factory = CardFactory(input_file)
        self.playlist_name = card_factory.playlist_name
        self.cards = dict()
        for _ in range(n_cards):
            self.cards[_] = card_factory.make_card()
        self.track_ids = card_factory.get_track_ids()
        self.track_info = card_factory.track_info
        self.track_artists = card_factory.input_artists
        self.player = Player(self.track_ids, sp)
        self.played_tracks = []
        self.unplayed_tracks = []
        self.paused_at_ms = None
        self.current_track_idx = None
        for idx in range(len(self.track_ids)):
            self.unplayed_tracks.append(idx)
        print(f'Created a Mingo game with {n_cards} cards')

    def get_card(self, card_num):
        if card_num > self.n_cards-1:
            raise Exception(f'There are only {self.n_cards} cards in this game. Try again.')
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
        with open(save_path, 'w') as f:
            f.write("<html>")

            # First write a css that provides a good table rendering for mingo cards.
            # This also will cause two cards per page when printing the browser
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
                        font-size: 19pt;
                        font-family: Arial, Helvetica, sans-serif;
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
                    card = self.get_card(i)
                    f.write(f"<h3>{card.playlist_name}, Card number {i}  </h3>")
                    card.as_html(f, False)
                    f.write("<br class='page'/>")
                    """
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

        filename = 'file:///Users/stephenharding/mycode/Python/spotify_3.9/mingo/cards.html'
        browser = webbrowser.get('firefox')
        browser.open(filename)
        # The call below was originally used. It opened the cards in the default browser,
        # which is Chrome on my machine. But Chrome has problems with the css print definition
        # for br.page that is used to insert a page break when printing. Firefox works, so
        # I needed to specify non-default browser firefox as seen above...
        #webbrowser.open_new_tab(filename)


class CommandProcessor(cmd.Cmd):
    prompt = '(no active game)'
    def __init__(self):
        super(CommandProcessor, self).__init__()
        self.active_game = None
        spotify = Spotify()
        self.sp = spotify.sp
        self.pl = Playlist(spotify.sp)


    """Process commands related to Spotify playlist management for the game of MINGO """
    def do_playlists(self, sub_command):
        """Display all Spotify playlists for the authorized Spotify user."""
        playlists = self.pl.get_playlists()
        for k in playlists.keys():
            print(f'{k}: {playlists[f"{k}"][0]}')
        print('\nNext you can save a list using the "savelist" command.\nAfter saving a list, you can make a set of Mingo cards with the listed songs.')

    def do_savelist(self, list_number):
        """Save the names and ids of tracks from a Spotify playlist to a csv file. The number of the playlist must be supplied."""
        if list_number:
            self.pl.process_playlist(list_number, True)
            print('\nNext you can make a set of Mingo cards using the songs in the list you just saved.')
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
            self.prompt = f'({self.active_game.playlist_name})'
            print(f'A new game has been made with {num_cards} cards.')
            print('\nYou can use the "gamecards" command to display and print the Mingo cards for this game.')
            print('You can begin playing tracks in random order by using the "playtrack" command for each track.')
        except Exception as error:
            print(error)

    def do_view(self, card_num):
        """View a single Mingo card from the active Mingo game."""
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
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_pause(self, _):
        if self.active_game:
            self.active_game.pause()
            resume_at = self.active_game.currently_playing()[0]
            print(f'Paused after {resume_at} msec')
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  
    
    def do_resume(self,_):
        if self.active_game:
            self.active_game.resume()
        else:
               print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_showplayers(self, _):
        if self.active_game:
            self.active_game.player.show_available_players()
        else:
            print('There is not an active game, so players cannot be listed.')

    def do_currentlyplaying(self, _):
        if self.active_game:
            progress = self.active_game.currently_playing()[0]
            print(f'The track has been playing for {progress} msec')
        else:
           print('There is not an active game. Create one using "'"makegame"'" and try again.')  

    def do_EOF(self, line):
        """Press ctrl-d to exit this program"""
        try:
            if self.active_game and self.active_game.currently_playing()[1]:
                self.active_game.pause()
        except:
            pass
        return True

if __name__ == '__main__':
    CommandProcessor().cmdloop()