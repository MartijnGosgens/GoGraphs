import eel
import random
from datetime import datetime
import networks as nets
from gographs import *
from time import time

eel.init('web')

active_games = {}
active_bots = {}

def generate_random_key(N=20):
    import string
    import random
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

@eel.expose
def start_game(game_name,black_player="you",white_player="you",komi=3.5):
    words = game_name.split(' ')
    if words[0] == 'USA':
        G,pos = nets.usa_network()
    if words[0] == 'KARATE':
        G,pos = nets.karate_network()
    if words[0] == 'DODECAHEDRAL':
        G,pos = nets.dodecahedral_graph()
    if words[0] == 'COMMUNITIES':
        G,pos = nets.random_communities()
    if words[0] == 'GRID':
        G,pos = nets.generate_grid(int(words[1]),int(words[2]))
    if words[0] == 'VORONOI':
        G,pos = nets.random_voronoi(cells=(words[1]=='CELLS'))
    if words[0] == 'REGULAR':
        G,pos = nets.random_regular(int(words[1]),int(words[2]))
    if words[0] == 'GEOMETRIC':
        G,pos = nets.random_geometric(int(words[1]),int(words[2]))
    game_key = generate_random_key()
    active_games[game_key] = GoGame(G, komi=komi, pos=pos)
    if black_player!="you" or white_player!="you":
        active_bots[game_key] = {}
        black_player_words = black_player.split(" ")
        white_player_words = white_player.split(" ")
        from bots import MiniMaxBot,AlphaBetaBot
        if black_player_words[0]=="MiniMax":
            active_bots[game_key][BLACK] = MiniMaxBot(depth=int(black_player_words[1]))
        elif black_player_words[0]=="AlphaBeta":
            active_bots[game_key][BLACK] = AlphaBetaBot(depth=int(black_player_words[1]),game=active_games[game_key])
        if white_player_words[0]=="MiniMax":
            active_bots[game_key][WHITE] = MiniMaxBot(depth=int(white_player_words[1]))
        elif white_player_words[0]=="AlphaBeta":
            active_bots[game_key][WHITE] = AlphaBetaBot(depth=int(white_player_words[1]),game=active_games[game_key])
    eel.setGraph(get_graph(game_key))
    eel.updateGui(get_info(game_key))
    next_turn(game_key)
    
def get_game(game_key):
    if game_key not in active_games:
        raise Exception(f"Game {game_key} does not exist")
    return active_games[game_key]

@eel.expose
def make_move(game_key, move):
    print(move)
    game = get_game(game_key)
    try:
        game.process_move(move)
    except Exception as e:
        print(e)
        eel.prompt_alerts(str(e))
    finally:
        eel.updateGui(get_info(game_key))
        next_turn(game_key)

@eel.expose
def get_graph(game_key):
    game = get_game(game_key)
    return {
        'pos': [[float(x),float(y)] for x,y in game.pos.values()],
        'edges': [
            (i,j) for i,j in game.G.edges
        ],
    }

def get_info(game_key):
    game = get_game(game_key)
    return {
        'key': game_key,
        'state': [int(s) for s in game.current_state()],
        'komi': game.komi,
        'turn': int(game.turn),
        'captures': {
            int(BLACK): game.captures[BLACK],
            int(WHITE): game.captures[WHITE],
        },
        'ended': game.ended,
        'score': {
            int(BLACK): game.final_score[BLACK],
            int(WHITE): game.final_score[WHITE],
        } if game.ended else {},
    }

def next_turn(game_key):
    game = get_game(game_key)
    if game.ended:
        return
    if game_key in active_bots and game.turn in active_bots[game_key]:
        bot = active_bots[game_key][game.turn]
        start_time = time()
        print(f'{game.turn} bot is thinking')
        move = bot.choose_move(game.gamenode)
        print(f'{game.turn} took {time()-start_time}s to find a move')
        make_move(game_key,move)

eel.start('index.html')