(function() { // wrapper to avoid variable override between files

var width = 400,
    height = 300;

var svg = d3.select("#force")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")"),
    radius = 4,
    linkedByIndex = {},
    toggle = 0;

var simulation = d3.forceSimulation()
  .force("link", d3.forceLink().id(function(d) { return d.id; }))
  .force("charge", d3.forceManyBody().strength(-18))
  .force("center", d3.forceCenter(460 / 2, 400 / 2));

d3.json("data/miserables.json", function(error, graph) {
  if (error) throw error;

  var link = svg.append("g")
      .attr("class", "links")
    .selectAll("line")
    .data(graph.links)
    .enter().append("line")
    .attr('class','link');

  var node = svg.append("g")
      .attr("class", "nodes")
    .selectAll(".node")
    .data(graph.nodes)
    .enter().append("g")
      .attr('class', 'node')
      .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended))
          .on('click', connectNodes)

  var circle = node.append('circle')
      .attr("r", radius)

  var label = node.append("text")
      .attr('class', 'label')
      .attr("dy", ".35em")
      .text(function(d) { return ""; });

  simulation
      .nodes(graph.nodes)
      .on("tick", ticked);

  simulation.force("link")
      .links(graph.links);

  function ticked() {
    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    circle
        //.attr("cx", function(d) { return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
        //.attr("cy", function(d) { return d.y = Math.max(radius, Math.min(height - radius, d.y)); })
        .attr('fill', function(d) { return mat(d.group); })
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });

    label
        .attr("x", function(d) { return d.x + 8; })
        .attr("y", function(d) { return d.y; });
  }

  for (i = 0; i < graph.nodes.length; i++) {
      linkedByIndex[i + "," + i] = 1;
  };

  graph.links.forEach(function (d) {
      linkedByIndex[d.source.index + "," + d.target.index] = 1;
  });

});

function neighboring(a, b) {
  return linkedByIndex[a.index + "," + b.index];
}

function connectNodes() {
  node = svg.selectAll(".node");
  link = svg.selectAll(".link");
  label = svg.selectAll(".label");

  /*d = d3.select(this).node().__data__;
  label.text(function(o) {
    return o.id==d.id ? o.group+': '+o.id : "";
  });*/

  if (toggle===0) {
    d = d3.select(this).node().__data__;
    node.style("opacity", function (o) {
      return neighboring(d, o) | neighboring(o, d) ? 1 : 0.1;
    });
    link.style("opacity", function (o) {
      return d.index==o.source.index | d.index==o.target.index ? 1 : 0.1;
    });
    node.style('fill', function(o) {
      return (neighboring(d, o)|neighboring(o, d))&&o.group!='Field'&&o.id!=d.id ? material[3] : 'black';
    });
    d3.select(this).style('fill', material[2]);
    label.text(function(o) { 
      return (neighboring(d, o)|neighboring(o, d))&&(o.group!='Field'|o.id==d.id) ? o.group+': '+o.id : ""; 
    });
    toggle = 1;
  } else {
    node = svg.selectAll(".node");
    link = svg.selectAll(".link");
    label = svg.selectAll(".label");

    node.style("opacity", 1);
    node.style('fill', 'black');
    link.style("opacity", 1);
    label.text("")
    toggle=0;
  }
}

function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}

function dragended(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}
  
})();