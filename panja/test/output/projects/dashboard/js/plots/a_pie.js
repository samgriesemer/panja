(function() { // wrapper to avoid variable override between files

// generate random data
function generate() {
  var tags = ['dog', 'cat', 'bird', 'fish'];
  return tags.map(function(d) {
    return {
      'animal': d,
      'count' : d3.randomUniform(0,10)()
    }
  });
}

// d3
var svg = d3.select("#a_pie")
    .attr("width", full_width)
    .attr("height", full_height),
    g = svg.append("g").attr("transform", "translate(" + full_width / 2 + "," + full_height / 2 + ")"),
    radius = height/2.7,
    data = generate();

var pie = d3.pie()
    .sort(null) // comment out for auto switching
    .value(function(d) { return d.count })

var arc = d3.arc()
    .outerRadius(radius)
    .innerRadius(radius/2);

var legend = svg.append("g")
    .style("font-family", "sans-serif")
    .attr("font-size", 10)
    .attr("text-anchor", "end")
    .attr("transform", function(d, i) { return "translate(" + (full_width/2+radius+40) + "," + (full_height/2-40) + ")"; })
    .selectAll("g")
    .data(pie(data))
        .enter().append("g")
        .attr("transform", function(d, i) { return "translate(0," + i*20 + ")"; });

legend.append("rect")
    .attr("x", 5)
    .attr("width", 15)
    .attr("height", 15)
    .attr("fill", function(d, i) { return mat(i); });

legend.append("text")
    //.attr("x", radius*2.5-5)
    .attr("y", 7.5)
    .attr("dy", "0.32em")
    .text(function(d) { return d.data.animal; });

redraw(generate());

d3.interval(function() {
  redraw(generate());
}, 3000);
  
function redraw(data) {
  var arcs = g.selectAll('.arc')
      .data(pie(data), function(d) { return d.data.animal; });

  arcs.transition()
      .duration(1000)
      .delay(function(d, i) { return i*250; })
      .attrTween('d', arcTween)

  arcs.enter().append('path')
      .attr('class', 'arc')
      .attr('fill', function(d, i) { return mat(i); })
      .attr('d', arc)
      .each(function(d) { this._current = d; })
}

function arcTween(a) {
  //console.log(this._current);
  var i = d3.interpolate(this._current, a);
  this._current = i(0);
  return function(t) {
    return arc(i(t));
  };
}

})();