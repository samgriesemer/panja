// connect to board
var url = 'https://api.smgr.io/engine/rl/monte_carlo/';
fetch(url, {
  method: 'GET',
  credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));

// d3 settings
var margin = {top: 30, right: 30, bottom: 30, left: 30},
    width = 300 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom,
    full_width = width + margin.left + margin.right,
    full_height = height + margin.top + margin.bottom;

var svg = d3.select('svg')
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// board settings
var rows = 3;
var cols = 3;
var stroke = 1;
var grid = [];

var cellw = width/cols;
var cellh = height/rows;

for (var i=0; i<rows; i++) {
  var cells = [];
  for (var j=0; j<cols; j++) {
    cells.push({
      x:j*cellw,
      y:i*cellh,
      w:cellw,
      h:cellh,
      idx:[i,j],
      _x:0,
      _o:0
    })
  }
  grid.push(cells);
}

var row = g.selectAll('.rows')
  .data(grid)
  .enter().append("g")
  .attr("class", "row");

var col = row.selectAll('.cell')
  .data(function(d) { return d; })
  .enter().append("rect")
  .attr("class", "cell")
  .attr("x", function(d) { return d.x; })
  .attr("y", function(d) { return d.y; })
  .attr("width", function(d) { return d.w; })
  .attr("height", function(d) { return d.h; })
  .style('fill','#FFF')
  .style('stroke','#000')
  .style('stroke-width',stroke)
  .on('click', function(d) {
    update(this,d,'m');
  })