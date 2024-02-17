var game_key,state,graph,animation;
var gameMode = "GRID 5 5";
var blackPlayer = "you";
var whitePlayer = "MiniMax 3";

const EMPTY = -1;
const BLACK = 0;
const WHITE = 1;

const colors = {
  EMPTY: 'orange',
  BLACK: 'black',
  WHITE: 'white'
};

const names = ['Black','White'];

const data = {
    'nodes': [],
    'links': [],
};

const gameModeDisplay = {
  "GRID 5 3": "5x3 Grid",
  "GRID 4 4": "4x4 Grid",
  "GRID 5 5": "5x5 Grid",
  "GRID 7 7": "7x7 Grid",
  "GRID 9 9": "9x9 Grid",
  "USA": "USA Map",
  "VORONOI CELLS": "Random Voronoi Cells",
  "VORONOI RIDGES": "Random Voronoi Ridges",
  "KARATE": "Karate Network",
  "DODECAHEDRAL": "Dodecahedral Graph"
};

function switchGameMode(newGameMode) {
  gameMode = newGameMode;
  document.getElementById('game-type-label').innerHTML = gameModeDisplay[gameMode];
}

function switchOpponent(color,player) {
  if (color=='black') {
    blackPlayer = player;
  } else {
    whitePlayer = player;
  }
  
  document.getElementById(color+'-player-label').innerHTML = player;
}

document.getElementById("button-start").addEventListener("click", () => start_game(), false);
document.getElementById("button-pass").addEventListener("click", () => make_move('pass'), false);

function start_game() {
    var graphType = document.getElementById("graphtype-dropdown").value;
    blackPlayer = document.getElementById("black-dropdown").value;
    whitePlayer = document.getElementById("white-dropdown").value;
    document.getElementById('container').innerHTML = '';
    eel.start_game(graphType,blackPlayer,whitePlayer);
}


async function get_graph() {
    graph = await eel.get_graph(game_key)();
}


function make_move(move) {
    console.log('Making move '+move)
    eel.make_move(game_key, move)();
}

// TODO: when game_key is undefined, it should
function updateGui(info) {
  console.log(info)
  if (info.key!=game_key) {
    // Initialize
    game_key = info.key;
    //graph = await eel.get_graph(game_key)();
    //animation = chart();
    //document.getElementById('container').appendChild(animation.svg);
  }
  animation.update(info);
  if (info.ended) {
    var win = info.score[BLACK]>info.score[WHITE] ? BLACK : WHITE;
    var lose = info.score[BLACK]>info.score[WHITE] ? WHITE : BLACK;
    var dif = info.score[win]-info.score[lose];
    document.getElementById('status-label').innerHTML = names[win]+' won with '+dif+' points (Black: '+info.score[BLACK]+', White: '+info.score[WHITE]+')'
    document.getElementById('score-label').innerHTML = '';
  } else {
    document.getElementById('status-label').innerHTML = names[info.turn]+"'s turn.";
    document.getElementById('score-label').innerHTML = 'Black: '+info.captures[BLACK]+' captures, White: '+info.captures[WHITE]+' captures + '+info.komi+' komi.';
  }
}
eel.expose(updateGui);

function setGraph(newgraph) {
  graph = newgraph;
  animation = chart();
  document.getElementById('container').appendChild(animation.svg);
}
eel.expose(setGraph);

function chart() {
    // Specify the dimensions of the chart.
    const width = document.getElementById('container').clientWidth;
    const height = 550;
    const minDim = Math.min(width,height);
    console.log(width+' '+height);


    // The force simulation mutates links and nodes, so create a copy
    // so that re-evaluating this cell produces the same result.
    const links = graph.edges.map(e => ({
       'source': e[0],
       'target': e[1]
    }));

    const nodes = graph.pos.map((xy, i) => ({
        'id': i,
        'x': width/2+minDim*(xy[0]-0.5),
        'y': height/2+minDim*(xy[1]-0.5),
        'status': EMPTY
    }));
    console.log(nodes.map(n=>([n['x'],n['y']])))
    

    // Create a simulation with several forces.
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).distance(0.3*minDim/Math.sqrt(nodes.length)).id(d => d.id))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2))
        .on("tick", ticked);

    // Create the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;");

    
    

    // Add a line for each link, and a circle for each node.
    const link = svg.append("g")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
      .selectAll()
      .data(links)
      .join("line")
        .attr("stroke-width", 3);

    const node = svg.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 3)
      .selectAll()
      .data(nodes)
      .join("circle")
        .attr("r", 12)
        .classed("empty", true);

    node.append("title")
        .text(d => d.id);

    // Add a drag behavior.
    node.call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended))
          .on("click", function(e,v) {
            make_move(v.id);
          });

    // Set the position attributes of links and nodes each time the simulation ticks.
    function ticked() {
      link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

      node
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
    }

    // Reheat the simulation when drag starts, and fix the subject position.
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    // Update the subject (dragged node) position during drag.
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    // Restore the target alpha so the simulation cools after dragging ends.
    // Unfix the subject position now that it’s no longer being dragged.
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      // Freeze after dragging
      //event.subject.fx = null;
      //event.subject.fy = null;
    }

    function update(info) {
      console.log(info);
      newstate = info['state'];
      node.classed('empty', v=>(newstate[v.id]==EMPTY));
      node.classed('black', v=>(newstate[v.id]==BLACK));
      node.classed('white', v=>(newstate[v.id]==WHITE));
    }

    return {
      'svg': svg.node(),
      'node': node,
      'link': link,
      'update': update,
      'nodes': nodes
    };
  }

function prompt_alerts(description) {
  alert(description);
}
eel.expose(prompt_alerts);