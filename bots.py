from gographs import EMPTY,BLACK,WHITE,compute_territory,GameNode

class Bot:
    '''
        node is a GameNode, with a reference to the game. This returns an index representing the place that is being played, or the string "pass".
    '''
    def choose_move(self,node):
        pass

def heuristic_evaluate(node,freedom_to_value={1:0.1, 2: 0.2, 3: 0.4, 4: 0.5}):
    captures = node.state.captures()
    gg = node.game.group_graph(node.state)
    territory = compute_territory(gg)
    score = captures[BLACK]-captures[WHITE]+territory[BLACK]-territory[WHITE]-node.game.komi
    # If the game is ended, then we return the true score
    if node.state.ended:
        return score
    
    for i in gg.nodes:
        data = gg.nodes[i]
        if data['status']==EMPTY:
            continue
        sign = 1 if data['status']==BLACK else -1
        freedoms = gg.degree(i)
        alivefactor = 2 if len(list(gg.neighbors(i)))>1 else 1
        #print(i,data['size'],freedoms,sign * data['size'] * (freedom_to_value[freedoms] if freedoms in freedom_to_value else max(freedom_to_value.values())))
        score += alivefactor * sign * data['size'] * (freedom_to_value[freedoms] if freedoms in freedom_to_value else max(freedom_to_value.values()))
    return score

class MiniMaxBot(Bot):
    def __init__(self,depth=3,freedom_to_value={1:0.1, 2: 0.2, 3: 0.4, 4: 0.5}):
        super().__init__()
        self.freedom_to_value = freedom_to_value
        self.depth = depth

    def evaluate(self,node):
        return heuristic_evaluate(node,self.freedom_to_value)

    def minimax(self,node,depth=3):
        if node.state.ended or depth==0:
            return self.evaluate(node)
        opt = max if node.turn==BLACK else min
        node.appendAll(verbose=False)
        return opt(map(lambda child: self.minimax(child,depth=depth-1),node.childNodes.values()))
        

    def move_seq(self,recursive_dict,initial_move):
        next_tuple = recursive_dict[initial_move]
        if len(next_tuple)>1:
            return [initial_move]+self.move_seq(next_tuple[1],next_tuple[2])
        return [initial_move]


    def choose_move(self,node):
        node.appendAll(verbose=False)
        opt = max if node.turn==BLACK else min
        move_dict = {
            move: self.minimax(child,depth=self.depth-1)
            for move,child in node.childNodes.items()
        }
        print(move_dict)
        move = opt(move_dict,key=move_dict.get)
        return move

class AlphaBetaBot(MiniMaxBot):
    def __init__(self, depth=3, freedom_to_value={ 1: 0.1,2: 0.2,3: 0.4,4: 0.5 }, game=None,no_sort = False):
        import networkx as nx
        super().__init__(depth, freedom_to_value)
        self.game = game
        self.shortest_paths = dict(nx.shortest_path_length(game.G))
        self.no_sort = no_sort

    def sort_moves(self,node):
        # Sort lexigraphically by distance to last move (if the last move isn't "pass") and degree, 
        # so that high-degree nodes close to the last move are considered first. 
        # This way, when exploring moves, it will more easily encounter " obvious answers" to moves.
        node.appendAll(verbose=False)
        if self.no_sort:
            return list(node.childNodes.keys())
        last_move = node.last_move()
        degree_key = lambda move: 0 if move=="pass" else -self.game.G.degree(move)
        distance_key = lambda move: float('inf') if move=="pass" or last_move=="pass" else self.shortest_paths[last_move][move]
        
        key = lambda move: (float("inf"),0) if move=="pass" else (self.shortest_paths[last_move][move],-self.game.G.degree(move))
        if last_move == "pass":
            key = lambda move: 0 if move=="pass" else -self.game.G.degree(move)
        sorted_moves = sorted(node.childNodes.keys(), key=key)
        return sorted_moves


    def minimax(self,node,alpha,beta,depth=3):
        if node.state.ended or depth==0:
            return self.evaluate(node),None
        best_val = float('-inf') if node.turn==BLACK else float('inf')
        best_move = None

        for move in self.sort_moves(node):
            child = node.childNodes[move]
            val = self.minimax(child,alpha,beta,depth=depth-1)[0] # Ignore the move return
            # Update alpha/beta
            if node.turn==BLACK:
                if val>best_val:
                    best_val = val
                    best_move = move
                alpha=max(alpha,best_val)
            else:
                if val<best_val:
                    best_val= val
                    best_move = move
                beta=min(beta,best_val)
            if beta <= alpha:
                break
        return best_val,best_move
    
    def choose_move(self,node):
        print("move order:")
        print(self.sort_moves(node))
        return self.minimax(node,float('-inf'),float('inf'),depth=self.depth)[1]
