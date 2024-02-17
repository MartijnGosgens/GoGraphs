import networkx as nx
import itertools as it
import numpy as np

def generate_grid(width,length):
    grid = nx.Graph()
    grid.add_nodes_from(it.product(range(width),range(length)))
    grid.add_edges_from([
        [(i,j),(i,j+1)]
        for i,j in it.product(range(width),range(length-1))
    ])
    grid.add_edges_from([
        [(i,j),(i+1,j)]
        for i,j in it.product(range(width-1),range(length))
    ])
    grid_pos = {
        (i,j): [i/width,j/length]
        for i,j in it.product(range(width),range(length))
    }
    return grid,grid_pos

def karate_network():
    G = nx.karate_club_graph()
    return G, nx.spring_layout(G,seed=0)

def dodecahedral_graph():
    G = nx.dodecahedral_graph()
    return G, nx.spring_layout(G,seed=0)

def random_regular(n=20,d=4):
    G = nx.random_regular_graph(d, n)
    return G, nx.spring_layout(G,seed=0)

def random_communities():
    G = nx.planted_partition_graph(3, 10,  1/3, 1/60)
    if not nx.is_connected(G):
        print('not connected')
        return random_communities()
    return G, nx.spring_layout(G,seed=0) # TODO: Normalize pos

def random_geometric(n=20,d=4):
    r = (d/(np.pi*n-np.pi))**0.5
    G = nx.random_geometric_graph(n=20, radius=r)
    print('RGG with mean deg',sum(dict(G.degree).values())/n,'is' if nx.is_connected(G) else 'is not','connected')
    if not nx.is_connected(G):
        return random_geometric(n=n,d=d)
    return G, {
        i: G.nodes[i]['pos']
        for i in G.nodes
    }


def usa_network():
    # Source: https://people.sc.fsu.edu/~jburkardt/datasets/states/state_neighbors.txt
    data = '''AL FL GA TN MS
        AK
        AZ NM UT NV CA
        AR LA MS TN MO OK TX
        CA AZ NV OR
        CO NM OK KS NE WY UT
        CT RI MA NY
        DE NJ PA MD
        DC MD VA
        FL GA AL
        GA SC NC TN AL FL
        HI
        ID WA OR NV UT WY MT
        IL WI IA MO KY IN
        IN IL KY OH MI
        IA MN SD NE MO IL WI
        KS OK MO NE CO
        KY TN VA WV OH IN IL MO
        LA MS AR TX
        ME NH
        MD DE PA WV VA DC
        MA NH VT NY CT RI
        MI WI IN OH
        MN ND SD IA WI
        MS AL TN AR LA
        MO AR TN KY IL IA NE KS OK
        MT ID WY SD ND
        NE KS MO IA SD WY CO
        NV AZ UT ID OR CA
        NH VT MA ME
        NJ NY PA DE
        NM TX OK CO AZ
        NY PA NJ CT MA VT
        NC VA TN GA SC
        ND MT SD MN
        OH MI IN KY WV PA
        OK TX AR MO KS CO NM
        OR CA NV ID WA
        PA OH WV MD DE NJ NY
        PR
        RI MA CT
        SC NC GA
        SD NE IA MN ND MT WY
        TN AL GA NC VA KY MO AR MS
        TX LA AR OK NM
        US
        UT AZ CO WY ID NV 
        VT NY MA NH
        VA MD DC WV KY TN NC
        WA OR ID
        WV VA MD PA OH KY
        WI MN IA IL MI
        WY CO NE SD MT ID UT'''
    lines = [ 
        line.strip() 
        for line in data.split('\n') 
        if len(line)>1
    ]
    nodes = []
    edges = []
    for line in lines:
        states = line.split(' ')
        if len(states)<2:
            continue
        i = states[0]
        nodes.append(i)
        for j in states[1:]:
            edges.append((i,j))
    usa = nx.Graph()
    usa.add_nodes_from(nodes)
    usa.add_edges_from(edges)
    posdata = '''AL  32.361538    -86.279118
AK  58.301935   -134.419740
AZ  33.448457   -112.073844
AR  34.736009    -92.331122
CA  38.555605   -121.468926
CO  39.7391667  -104.984167
CT  41.767      -72.677
DC  38.913      -77.013
DE  39.161921   -75.526755
FL  30.4518     -84.27277
GA  33.76       -84.39
HI  21.30895   -157.826182
ID  43.613739  -116.237651
IL  39.783250   -89.650373
IN  39.790942   -86.147685
IA  41.590939   -93.620866
KS  39.04       -95.69
KY  38.197274   -84.86311
LA  30.45809    -91.140229
ME  44.323535   -69.765261
MD  38.972945   -76.501157
MA  42.2352     -71.0275
MI  42.7335     -84.5467
MN  44.95       -93.094
MS  32.320      -90.207
MO  38.572954   -92.189283
MT  46.595805  -112.027031
NE  40.809868   -96.675345
NV  39.160949  -119.753877
NH  43.220093   -71.549127
NJ  40.221741   -74.756138
NM  35.667231  -105.964575
NY  42.659829   -73.781339
NC  35.771      -78.638
ND  48.813343  -100.779004
OH  39.962245   -83.000647
OK  35.482309   -97.534994
OR  44.931109  -123.029159
PA  40.269789   -76.875613
PR  18.2208     -66.5901
RI  41.82355    -71.422132
SC  34.000      -81.035
SD  44.367966  -100.336378
TN  36.165      -86.784
TX  30.266667   -97.75
US  38.913       77.013
UT  40.7547    -111.892622
VT  44.26639    -72.57194
VA  37.54       -77.46
WA  47.042418  -122.893077
WV  38.349497   -81.633294
WI  43.074722   -89.384444
WY  41.145548  -104.802042'''
    poslines = posdata.split('\n')
    pos = {}
    xs = []
    ys = []
    nodes = []
    for line in poslines:
        words = [w for w in line.split(' ') if len(w)>0]
        pos[words[0]] = (float(words[2])/200,float(words[1])/200)
    '''pos = nx.spring_layout(usa,pos=pos,seed=0,iterations=10,k=0.035)
    pos['VT'][0]+=0.1
    pos['NH'][0]+=0.2
    pos['VT'][1]+=0.1
    pos['NH'][1]+=0.1
    pos['ME'][0]+=0.2
    pos['MA'][0]+=0.1
    pos['RI'][0]+=0.2
    pos['CT'][0]+=0.07
    pos['GA'][0]+=0.07
    pos['GA'][1]-=0.03
    pos['SC'][0]+=0.07
    pos['CA'][1]-=0.1
    pos['AZ'][1]-=0.1'''
    # Renormalize coordinates to [0,1]
    xs = [xy[0] for xy in pos.values()]
    ys = [xy[1] for xy in pos.values()]
    max_x = max(xs)
    min_x = min(xs)
    max_y = max(ys)
    min_y = min(ys)
    return usa,{
        v: [(x-min_x)/(max_x-min_x),1-(y-min_y)/(max_y-min_y)]
        for v,(x,y) in pos.items()
    }

def random_voronoi(n=20,cells=True):
    from scipy.spatial import Voronoi
    import numpy as np
    coords = np.random.rand(n, 2)
    vor = Voronoi(coords)
    G = nx.Graph()
    if cells:
        G.add_nodes_from(range(n))
        G.add_edges_from([
            (int(i),int(j))
            for i,j in vor.ridge_points
        ])
        pos = dict(zip(range(n),coords))
    else:
        pos = dict(enumerate(vor.vertices))
        print(vor.vertices)
        print([(i,j) for i,j in vor.ridge_vertices if i>=0 and j>=0])
        G.add_edges_from([(i,j) for i,j in vor.ridge_vertices if i>=0 and j>=0])
    return G,pos