(function() { // wrapper to avoid variable override between files

// generate random data
data = [];
for (var i=0; i<3; i++) {
  sample = [];
  for (var j=0; j<20; j++) {
	  sample.push({'x':j, 'y':d3.randomNormal(0,1)()});
  }
  data.push({'id':i, 'values':sample})
}

// d3
var svg_line = d3.select("#line")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom),
    g = svg_line.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x = d3.scaleLinear()
  .domain([
    d3.min(data, function(c) { return d3.min(c.values, function(d) { return d.x; }); }),
    d3.max(data, function(c) { return d3.max(c.values, function(d) { return d.x; }); })
  ])
  .range([0,width]);

var y = d3.scaleLinear()
  .domain([
    d3.min(data, function(c) { return d3.min(c.values, function(d) { return d.y; }); }),
    d3.max(data, function(c) { return d3.max(c.values, function(d) { return d.y; }); })
  ])
  .range([height,0]);

// define line
var line = d3.line()
    .defined(function(d) { return d; })
    .curve(d3.curveBasis)
    .x(function(d) { return x(d.x); })
    .y(function(d) { return y(d.y); });

g.append("g")
  .attr("class", "x-axis")
  .attr("transform", "translate(0," + height + ")")
  .call(d3.axisBottom(x));

g.append("g")
  .attr("class", "y-axis")
  .attr("transform", "translate(0," + 0 + ")")
  .call(d3.axisLeft(y));

series = g.selectAll('.series')
  .data(data)
  .enter().append('g')
    .attr('class', 'series')

series.append('path')
	.attr('class', 'line')
	.attr('fill', 'none')
  .attr('stroke', function(d) { return mat(d.id); })
  .attr('stroke-width', '1.5px')
	.attr('d', function(d) { return line(d.values) });

})();
