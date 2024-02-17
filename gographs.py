import networkx as nx
import matplotlib.pyplot as plt
#from networks import generate_grid,usa_network

from enum import Enum
class Status(Enum):
    EMPTY = -1
    BLACK = 0
    WHITE = 1
    
    def opponent(self):
        if self==BLACK:
            return WHITE
        elif self==WHITE:
            return BLACK
    
    def color(self):
        if self==EMPTY:
            return 'orange'
        if self==BLACK:
            return 'black'
        if self==WHITE:
            return 'white'
        
    def __str__(self):
        if self==EMPTY:
            return 'Empty'
        if self==BLACK:
            return 'Black'
        if self==WHITE:
            return 'White'
        
    def __int__(self):
        if self==EMPTY:
            return -1
        if self==BLACK:
            return 0
        if self==WHITE:
            return 1
Status.EMPTY,
EMPTY=Status.EMPTY
BLACK = Status.BLACK
WHITE = Status.WHITE

def group_graph(G):
    blacks = [i for i in G if G.nodes[i]['status']==BLACK]
    whites = [i for i in G if G.nodes[i]['status']==WHITE]
    empties = [i for i in G if G.nodes[i]['status']==EMPTY]
    black_groups = list(nx.connected_components(nx.induced_subgraph(G,blacks)))
    white_groups = list(nx.connected_components(nx.induced_subgraph(G,whites)))
    empty_groups = list(nx.connected_components(nx.induced_subgraph(G,empties)))
    node_label = {}
    for i_group,group in enumerate(empty_groups):
        for node in group:
            node_label[node] = f'e{i_group}'
    for i_group,group in enumerate(black_groups):
        for node in group:
            node_label[node] = f'b{i_group}'
    for i_group,group in enumerate(white_groups):
        for node in group:
            node_label[node] = f'w{i_group}'
    gg = nx.Graph()
    gg.add_nodes_from({
        f'e{i}': {'size': len(group), 'status': EMPTY, 'ids': list(group)} 
        for i,group in enumerate(empty_groups)
    }.items())
    gg.add_nodes_from({
        f'b{i}': {'size': len(group), 'status': BLACK, 'ids': list(group)} 
        for i,group in enumerate(black_groups)
    }.items())
    gg.add_nodes_from({
        f'w{i}': {'size': len(group), 'status': WHITE, 'ids': list(group)} 
        for i,group in enumerate(white_groups)
    }.items())
    gg.add_edges_from([
        (node_label[i],node_label[j])
        for i,j in G.edges
        if (G.nodes[i]['status'] == EMPTY or G.nodes[j]['status'] == EMPTY) and (node_label[i]!=node_label[j])
    ])
    return gg


# Returns a list of nodes that are captured
def compute_captures(gg):
    captures = []
    for i in gg:
        if gg.nodes[i]['status']==EMPTY:
            continue
        neigh_statuses = set([
            gg.nodes[n]['status']
            for n in gg[i]
        ])
        if EMPTY in neigh_statuses:
            continue # i has at least one freedom, it is not captured
        # i does not neighbor an unoccupied group, it is captured
        captures+=gg.nodes[i]['ids']
    return captures

# Returns a dictionary with two keys ('white' and 'black') containing the territory of each. Does not compute captures
def compute_territory(gg):
    territory = {
        BLACK: 0,
        WHITE: 0
    }
    for i in gg:
        if gg.nodes[i]['status']!=EMPTY:
            continue
        neigh_statuses = set([
            gg.nodes[n]['status']
            for n in gg[i]
        ])
        if len(neigh_statuses)==1 and EMPTY not in neigh_statuses:
            territory[neigh_statuses.pop()]+=gg.nodes[i]['size']
    return territory
         

class GoGame:
    def __init__(self,G,komi=3.5,pos=None):
        newG = nx.Graph()
        # We want a graph with indices 0,...,n-1, and set each status to 'empty'
        newG.add_nodes_from([
            (i, {
                'name': name,
                'status': EMPTY # TODO: Change this class so that the status is an object separate from the graph
            })
            for i,name in enumerate(G)
        ])
        name2idx = dict([(name,i) for i,name in enumerate(G)])
        newG.add_edges_from([
            (name2idx[n1],name2idx[n2])
            for n1,n2 in G.edges
        ])
        self.G = newG
        self.komi=komi
        self.turn = BLACK
        self.states = {self.current_state()}
        self.captures = {BLACK: 0, WHITE: 0}
        self.moves = []
        self.ended = False
        self.final_score = {}
        self.gamenode = GameNode(state=self.current_gamestate(),game=self)
        
        if pos is None:
            pos=nx.spring_layout(G)
        self.pos={
            idx: pos[name]
            for name,idx in name2idx.items()
        }
        
    def current_state(self):
        return tuple(self.G.nodes[i]['status'] for i in self.G)
    def current_gamestate(self):
        return GameState(tuple(self.G.nodes[i]['status'] for i in self.G),self.captures[BLACK],self.captures[WHITE])
    
    def next_turn(self):
        self.turn = self.turn.opponent()
    
    def process_move(self,move):
        if self.gamenode.state.boardstate()!=self.current_state():
            print('inconsistent states:')
            print(self.gamenode.state.boardstate())
            print(self.current_state())
        self.gamenode.appendNode(move)
        if move in self.gamenode.childNodes:
            self.gamenode = self.gamenode.childNodes[move]
        if move=='pass':
            # Check if the last move was also a pass
            if self.moves[-1]=='pass':
                self.end_game()
            # Register move and do nothing
            self.moves.append(move)
            self.next_turn()
            return
        if move not in self.G.nodes or self.G.nodes[move]['status']!=EMPTY:
            # Move not allowed
            raise Exception("This move does not correspond to an empty node")
        
        # We change the state, but might revert it if this move causes ko
        self.G.nodes[move]['status'] = self.turn
        
        # Process captures
        gg = group_graph(self.G)
        captures = compute_captures(gg)
        
        # Check suicide rule
        if {self.G.nodes[i]['status'] for i in captures} == {self.turn}:
            # Revert and raise exception
            self.G.nodes[move]['status'] = EMPTY
            raise Exception("This move would lead to self-capture without capturing enemy stones, which is not allowed.")
        # If it is a legit capture, then it will only capture stones of the opponent
        captures = [i for i in captures if self.G.nodes[i]['status'] != self.turn]
        
        # Process captures
        for i in captures:
            self.G.nodes[i]['status'] = EMPTY
        # Add score
        self.captures[self.turn]+=len(captures)
        
        # Check Ko rule
        if self.current_state() in self.states:
            # Revert and raise exception
            self.G.nodes[move]['status'] = EMPTY
            opponent = self.turn.opponent()
            for i in captures:
                self.G.nodes[i]['status'] = opponent
            raise Exception("This move brings the board back to a previous state and therefore violates the Ko rule.")
            
        # Add the new state and add the move
        self.states.add(self.current_state())
        self.moves.append(move)
        
        # Proceed to the next turn
        self.next_turn()
        
    def draw_state(self,pos=None):
        if pos is None:
            pos = self.pos
        nx.draw_networkx(self.G,
                         pos=pos,
                         node_color=[
                             self.G.nodes[i]['status'].color()
                             for i in self.G.nodes
                         ],
                         with_labels=False,
                         edgecolors=['white' if self.G.nodes[i]['status']==BLACK else 'black' for i in self.G.nodes])
        nx.draw_networkx_labels(self.G,
                               pos=pos,
                               font_size=10,
                               font_color='black',
                               labels = {
                                   i: str(i)
                                   for i in self.G.nodes
                                   if self.G.nodes[i]['status']==EMPTY
                               })
        plt.axis('off')
        
    
    def end_game(self):
        self.ended = True
        self.final_score = self.compute_score()
        scores = self.final_score
        win = BLACK if scores[BLACK]>scores[WHITE] else WHITE
        print(f'{win} wins with {scores[win]-scores[win.opponent()]} points (Black: {scores[BLACK]}, White: {scores[WHITE]})')
        print(self.gamenode.preceding_moves())
        
    
    '''
        Return the state that follows after applying the move. We do this without modifying the state or game. If the state is illegal, this will return a string describing the violation.
    '''
    def apply_move(self,move,game_node):
        state = game_node.state
        color = game_node.turn
        if not isinstance(state,GameState):
            return "One cannot perform a move from an illegal game node."
        if move=="pass" and state.passed:
            # End the game
            captures = state.captures()
            return GameState(state.boardstate(),
                             black_captures=captures[BLACK],
                             white_captures=captures[WHITE],
                             passed=True,
                             ended=True)
        elif move=="pass" and not state.passed:
            captures = state.captures()
            return GameState(state.boardstate(),
                             black_captures=captures[BLACK],
                             white_captures=captures[WHITE],
                             passed=True,
                             ended=False)

        # Convert to list
        state_list = list(state)
        move = int(move)
        if move>=len(state) or move<0 or state[move] != EMPTY:
            return f"Move {move} does not correspond to an empty place."
        state_list[move] = color
        captures = self.find_captures(state_list)

        # Check suicide rule
        if {state_list[i] for i in captures} == {color}:
            return "This move would lead to self-capture without capturing enemy stones, which is not allowed."
        # If it is a legit capture, then it will only capture stones of the opponent
        captures = [i for i in captures if state_list[i] != color]
        
        # Process captures
        for i in captures:
            state_list[i] = EMPTY
        # Add score
        newcaptures = state.captures()
        newcaptures[color] +=len(captures)
        newstate = GameState(state_list,newcaptures[BLACK],newcaptures[WHITE])
        
        # Check Ko rule
        if newstate.boardstate() in game_node.previous_boardstates:
            return "This move brings the board back to a previous state and therefore violates the Ko rule."
        
        return newstate
    
    def compute_score(self):
        scores = {
            BLACK: self.captures[BLACK],
            WHITE: self.komi+self.captures[WHITE]
        }
        gg = group_graph(self.G)
        for color,territory in compute_territory(gg).items():
            scores[color]+=territory
        return scores
    
    def group_graph(self,state=None):
        if state is None:
            state = self.current_gamestate()
        G = self.G
        blacks = [i for i in G if state[i]==BLACK]
        whites = [i for i in G if state[i]==WHITE]
        empties = [i for i in G if state[i]==EMPTY]
        black_groups = list(nx.connected_components(nx.induced_subgraph(G,blacks)))
        white_groups = list(nx.connected_components(nx.induced_subgraph(G,whites)))
        empty_groups = list(nx.connected_components(nx.induced_subgraph(G,empties)))
        node_label = {}
        for i_group,group in enumerate(empty_groups):
            for place in group:
                node_label[place] = f'e{i_group}'
        for i_group,group in enumerate(black_groups):
            for place in group:
                node_label[place] = f'b{i_group}'
        for i_group,group in enumerate(white_groups):
            for place in group:
                node_label[place] = f'w{i_group}'
        gg = nx.MultiGraph()
        gg.add_nodes_from({
            f'e{i}': {'size': len(group), 'status': EMPTY, 'ids': list(group)} 
            for i,group in enumerate(empty_groups)
        }.items())
        gg.add_nodes_from({
            f'b{i}': {'size': len(group), 'status': BLACK, 'ids': list(group)} 
            for i,group in enumerate(black_groups)
        }.items())
        gg.add_nodes_from({
            f'w{i}': {'size': len(group), 'status': WHITE, 'ids': list(group)} 
            for i,group in enumerate(white_groups)
        }.items())
        gg.add_edges_from([
            (node_label[i],node_label[j])
            for i,j in G.edges
            if (state[i] == EMPTY or state[j] == EMPTY) and (node_label[i]!=node_label[j])
        ])
        return gg
    
    def find_captures(self,state):
        captures = []
        gg = self.group_graph(state)
        for i in gg:
            if gg.nodes[i]['status']==EMPTY:
                continue
            neigh_statuses = set([
                gg.nodes[n]['status']
                for n in gg[i]
            ])
            if EMPTY in neigh_statuses:
                continue # i has at least one freedom, it is not captured
            # i does not neighbor an unoccupied group, it is captured
            captures+=gg.nodes[i]['ids']
        return captures
            
class GameNode:
    '''
        State may be None. At least one of game or parent should be given.
        When parent is None, we assume it is the initial state of the game.
    '''
    def __init__(self,state=None,parent=None,game=None):
        self.state = state # state may be None if the preceding move is illegal
        self.is_start = (parent is None)
        self.parent = parent
        self.game = game if self.is_start else parent.game
        self.turn = BLACK if self.is_start else parent.turn.opponent()
        self.previous_boardstates = set() if self.is_start else parent.previous_boardstates|{parent.state.boardstate()}
        self.childNodes = dict() # A dictionary from move to child node
        self.appended = False

    def appendNode(self,move,verbose=False):
        if self.state.ended or move in self.childNodes:
            return
        if not isinstance(self.state,GameState):
            print("Trying to append a node from a node with illegal state",self.state)
            return # Don't do anything if this is an illegal state
        newstate = self.game.apply_move(move,game_node=self)
        if isinstance(newstate,tuple):
            self.childNodes[move] = GameNode(newstate,parent=self)
        elif verbose: 
            print(f"Move {move} is illegal")

    def appendAll(self,verbose=False):
        if self.state.ended or self.appended:
            return
        if 'pass' not in self.childNodes:
            self.appendNode('pass',verbose=verbose)
        for move in self.state.places_with_status(EMPTY):
            if move not in self.childNodes:
                self.appendNode(move,verbose=verbose)
        self.appended = True

    def last_move(self):
        if self.parent is None:
            return "pass" # When it doesn't have a preceding move (i.e., beginning of the game), we return pass
        for move,child in self.parent.childNodes.items():
            if child==self:
                return move


    def preceding_moves(self):
        if self.parent is None:
            return []
        return self.parent.preceding_moves()+[self.last_move()]

    @classmethod
    def FromGame(cls,game):
        state = GameState(game.current_state(),game.captures[BLACK],game.captures[WHITE])
        return GameNode(state=state,game=game)


'''
    Immutable object, state[BLACK],game[WHITE] give the captures of black and white respectively
'''
class GameState(tuple):
    def __new__ (cls, state, black_captures=0, white_captures=0, **kwargs):
        return super(GameState, cls).__new__(cls, tuple(state))
    
    def __init__ (self, state, black_captures=0, white_captures=0,passed=False,ended=False):
        self._captures = (black_captures,white_captures)
        self.passed = passed
        self.ended = ended

    def __getitem__(self,key):
        if key==BLACK:
            return self._captures[0]
        if key==WHITE:
            return self._captures[1]
        return tuple.__getitem__(self,key)
    
    def captures(self):
        return dict(zip([BLACK,WHITE],self._captures))
    
    def boardstate(self):
        return tuple(self)
    
    def places_with_status(self,status):
        return [i for i,s in enumerate(self) if s==status]
    
    def empties(self):
        return [i for i,s in enumerate(self) if s==EMPTY]
    
    def blacks(self):
        return [i for i,s in enumerate(self) if s==BLACK]
    
    def whites(self):
        return [i for i,s in enumerate(self) if s==WHITE]

        
            