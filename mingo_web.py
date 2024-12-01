from flask import Flask, render_template, render_template_string, request, jsonify, session, redirect, url_for
import os, json


# Create the Flask application
app = Flask(__name__)

# NOTE: The secret key is used to cryptographically-sign the cookies used for storing
#       the session data.
app.secret_key = 'MINGO_SECRET_KEY'

stop_requests = []

run_on_host = os.environ.get('RUN_ON_HOST') 
using_port = os.environ.get('USING_PORT')
update_interval = os.environ.get('MINGO_UPDATE_INTERVAL')
debug_mode = os.environ.get('MINGO_DEBUG_MODE')

songs = []
#songs2 = []
cards = {}

# A QR code on each MINGO sheet has the URL for that sheet signified with
# an integer passed in the URL string. That integer is the player id
# that is passed each time a 'Stop Playing' button is tapped by a user.
@app.route('/<int:player_id>', methods=['GET'])
def assign_player_id(player_id):
    session.permanent = True
    print('Assigning player id', player_id)
    session['player_id'] = player_id
    return redirect(url_for('index'))

@app.route('/', methods=['GET'])
def index():
    return render_template('main_page.html', 
        stop_requests=stop_requests, 
        run_on_host=run_on_host, 
        using_port=using_port,
        update_interval=update_interval) 

@app.route('/card', methods=['GET'])
def card():
    global cards
    card_number = session['player_id']
    titles = cards[str(card_number)]
    print('========> ', titles)
    return render_template('card_view_2.html', card_number=card_number, titles=titles)

@app.route('/debug', methods=['GET'])
def card_debug():
    print("-------------- card rendering")
    print(cards.keys())
    print("cards['0']")
    print(cards['0'])
    print("--------------")
    print("cards['1']")
    print(cards['1'])
    print("--------------")
    
    # Respond to the client
    return jsonify({"status": "success", "received": "debug"})


@app.route('/card_load', methods=['POST'])
def card_load():
    global cards

    # Get the JSON data from the request
    json_string = request.get_json()
    # print("Received data:", data)
    # print (json_to_songs(data))
    # Parse the JSON string into a Python dictionary
    data = json.loads(json_string)

    # Get the card number
    card_nbr = data["card_nbr"]
    print("Loading card number", card_nbr)

    #songs.clear()
    #songs2.clear()
    # Extract the list of song titles
    songs.append([])
    songs_temp = [song["title"] for song in data["songs"]]
    for song in songs_temp:
        print('adding ', song, ' ', card_nbr)
        songs[len(songs)-1].append(song)
    
    cards.update({str(card_nbr): songs[len(songs)-1]})

    print('\n\n\n========= Loaded: ',str(card_nbr),'\n',cards[str(card_nbr)])

    if card_nbr == 1:
        card_debug()

    # Respond to the client
    return jsonify({"status": "success", "received": data})

@app.route('/clear', methods=['GET'])
def clear_stop_requests():
    if request.method == 'GET':
        stop_requests.clear()
        return render_template_string("""
            <h1>Stop requests have been cleared</h1>
        """)

@app.route('/check', methods=['GET'])
def check_status():
    if request.method == 'GET':
        player_id = session['player_id']
        print('player id: ', player_id)
        return render_template_string("""
            <h1>Player id: {{player_id}}</h1>
        """, player_id=player_id)        

@app.route('/requeststop', methods=['POST'])
def add_stop_request():
    if request.method == 'POST':
        # Record the player's request to stop playing
        if (session['player_id'] not in stop_requests):
            stop_requests.append(session['player_id'])
        else:
            print('not recording a repeated request')
        return jsonify({'stoprequests': stop_requests})

@app.route('/stopdata', methods=['POST'])
def get_stop_data():
    return jsonify({'stoprequests': stop_requests})

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    if 'text' in data:
        text_value = data['text']
        return jsonify({'message': f'Text received: {text_value}'})
    else:
        return jsonify({'error': 'no text received'})

@app.route('/get_stop_count')
def get_stop_count():
    return str(len(stop_requests))

"""
def json_to_songs(json_string):
    # Parse the JSON string into a Python dictionary
    data = json.loads(json_string)

    # Get the card number
    card_nbr = data["card_nbr"]
    print("Loading card number", card_nbr)

    # Extract the list of song titles
    songs_temp = [song["title"] for song in data["songs"]]
    songs.clear()
    for song in songs_temp:
        songs.append(song)
    
    cards[str(card_nbr)] = songs;
    print('\n\n\n========= Loaded: ',str(card_nbr),'\n',cards[str(card_nbr)])
    return songs
"""

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=using_port, host='0.0.0.0')
#    app.run(debug=False, threaded=True, port=8080, host='127.0.0.1')
