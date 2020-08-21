(function() { // wrapper to avoid variable override between files

var svg = d3.select("#bar")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

d3.csv('data/pie.csv', function(d) {
    d.count = +d.count;
    return d;
}, function(error, data) {
    if (error) throw(error);
  
  var x = d3.scaleBand().range([0, width]).padding(0.1),
      y = d3.scaleLinear().range([height, 0]);
  
  x.domain(data.map(function(d) { return d.animal; }));
  y.domain([0, d3.max(data, function(d) { return d.count; })]);

  var bars = g.selectAll(".bar")
    .data(data)
    .enter().append("rect")
      .attr("class", "bar")
      .attr("x", function(d) { return x(d.animal); })
      .attr("y", function(d) { return y(d.count); })
      .attr("width", x.bandwidth())
      .attr("height", function(d) { return height - y(d.count); })
      .attr("fill", function(d) { return mat(d.animal); });
  
  g.append("g")
      .attr("class", "x-axis")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x));
  
  g.append("g")
      .attr("class", "y-axis")
      .attr("transform", "translate(0," + 0 + ")")
      .call(d3.axisLeft(y));
  
  bars      
      .on("mouseover", mouseover)
      .on("mousemove", function(d){
          div
              .style("left", (d3.event.pageX - 34) + "px")
              .style("top", (d3.event.pageY - 12) + "px")
              .text('count : ' + format(d.count));
        })
      .on("mouseout", mouseout);
});

})();