// initialize plot
let margin = {top: 0, right: 0, bottom: 0, left: 0};
let width = window.innerWidth - margin.left - margin.right;
let height = window.innerHeight - margin.top - margin.bottom;

let svg = d3.select('.simulation')
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom),
  g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

let n = 4;
let maxr = 20;
let minr = 5;
let ticks = 0;
let nodes = [];
let groups = [];
let color = d3.scaleSequential(d3.interpolateRainbow)
    .domain(d3.range(n));
color = ['#003CFF','#ff524d','#fffc01', '#000'];
color = ['#ff524d']
color = ['#000']

// populate nodes
for (let i=0; i<n; i++) {
  nodes.push({
    x: width*(1-Math.random()/2.3),
    y: height*Math.random(),
    r: (maxr-minr)*Math.random()+minr,
    w: (maxr-minr)*Math.random()+minr,
    h: (maxr-minr)*Math.random()+minr,
    tx: width*Math.random(),
    ty: height*Math.random(),
    vx: 0.05*Math.random(),
    vy: 0.05*Math.random()
  });
}

// let circles = g.selectAll('circle')
//   .data(nodes)
//   .enter()
//     .append('circle');

let simulation = d3.forceSimulation()
  .alpha(0.1).alphaTarget(0.2)
  .velocityDecay(0)
  //.force('x', d3.forceX(width*Math.random()).strength(0.001))
    //.x(d => d.tx))
  //.force('y', d3.forceY(height*Math.random()).strength(0.001))
    //.y(d => d.ty))
  //.force('move', move())
  .force('charge', d3.forceManyBody().strength(10))
  .force('center', d3.forceCenter(window.innerWidth*3/4, window.innerHeight/2))
    //.distanceMax(400).distanceMin(20))
  //.force('collide', d3.forceCollide(d => d.r).iterations(1))
  .on('tick', tick)
  .nodes(nodes);

// make mouse an element in the simulation
// document.addEventListener('mousemove', function(event) {
//   nodes[1].x = event.clientX;
//   nodes[1].y = event.clientY;
//   nodes[1].vx = 0;
//   nodes[1].vy = 0;
// })

function tick() {
//   nodes[nodes.length-1].x = window.innerWidth*2/3;
//   nodes[nodes.length-1].y = window.innerHeight/2;
//   nodes[nodes.length-1].vx = 0;
//   nodes[nodes.length-1].vy = 0;
  
  let holder = g.append('g');
  let circles = holder.selectAll('rect')
    .data(nodes)
    .enter()
      .append('rect');

  circles
    .attr('x', d => d.x)
    .attr('y', d => d.y)
    .attr('width', d => d.w)
    .attr('height', d => d.h)
    //.attr('r', d => d.r)
    .style('fill', 'white')
    .style('stroke', (d,i) => color[i%color.length])
    .style('stroke-width', 0.5);

  if (g.selectAll('g').size() > 250) {
    g.selectAll('g').nodes()[0].remove();
  }
}

function move() {
  let strength = 1;

  function force(alpha) {
    for (let i = 0; i < n; ++i) {
      let k = strength;
      let node = nodes[i];
      //node.vx = Math.random()*3;
      //node.vy = Math.random()*3;
      //node.x -= node.vx * k;
      //node.y -= node.vy * k;
      //node.vx -= (node.x - node.tx) * k;
      //node.vy -= (node.y - node.ty) * k;
    }
  }

  force.strength = function(s) {
    strength = (s == null) ? strength : s;
    return force;
  }

  return force;
}
