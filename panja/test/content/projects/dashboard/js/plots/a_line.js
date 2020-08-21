material = ['#d1e4f1', '#f7f00a', '#EE4266', '#540D6E'],
mat = d3.scaleOrdinal(material);
var margin = {top: 10, right: 10, bottom: 30, left: 50},
    width = 1.0*window.innerWidth/3.5 - margin.left - margin.right,
    height = 1.0*window.innerHeight/4 - margin.top - margin.bottom,
    full_width = width + margin.left + margin.right,
    full_height = height + margin.top + margin.bottom;
var parseTime = d3.timeParse("%B %d, %Y");

// generate random data
/*function generate() {
  var data = [];
  for (var j=0; j<20; j++) {
    data.push({'x':j, 'y':d3.randomNormal(0,1)()});
  }
  return data;
}*/

// d3
var svg = d3.select("#stock-line")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x = d3.scaleTime()
  .range([0,width]);

var y = d3.scaleLinear()
  .range([height,0]);

// define line
var line = d3.line()
    .defined(function(d) { return d; })
    //.curve(d3.curveBasis)
    .x(function(d) { return x(d.time); })
    .y(function(d) { return y(d.price); });

var x_axis = g.append("g")
  .attr("class", "x-axis")
  .attr("transform", "translate(0," + height + ")");

var y_axis = g.append("g")
  .attr("class", "y-axis")
  .attr("transform", "translate(0,0)");

var ry_axis = g.append("g")
  .attr("class", "y-axis")
  .attr("transform", "translate(" + width + ",0)");

g.append('path')
	.attr('class', 'line')
	.attr('fill', 'none')
  .attr('stroke', '#003cff')
  .attr('stroke-width', '1.5px');
  
function update_chart(data) {
  t = d3.transition()
        .duration(250);
  data = data['BTC'];
  data.forEach(d => {
    d.time = new Date(d.time);
  })

  x.domain([
    d3.min(data, function(d) { return d.time; }),
    d3.max(data, function(d) { return d.time; })
  ]);

  y.domain([
    d3.min(data, function(d) { return d.price; }),
    d3.max(data, function(d) { return d.price; })
  ]);
  
  // render all following loops w/ transitions
  g.selectAll('.line')
    .datum(data)
    //.transition(t) // set transition; applied to following change
    .attr('d', line);
  
  y_axis.transition(t).call(d3.axisLeft(y));
  x_axis.call(d3.axisBottom(x));
}