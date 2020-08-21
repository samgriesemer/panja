(function() { // wrapper to avoid variable override between files

var svg = d3.select("#hist")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var sample = d3.randomNormal(),
    normal = [];

for (var i=0; i<2000; i++) {
  normal.push(sample());
}

var x = d3.scaleLinear()
  .domain([-5,5])
  .range([0,width]);

var histogram = d3.histogram()
  .domain(x.domain())
  .thresholds(x.ticks(50))

var bins = histogram(normal);
  
var y = d3.scaleLinear()
    .range([height,0])
    .domain([0,d3.max(bins, function(d) { return d.length; })]);

g.append("g")
  .attr("class", "x-axis")
  .attr("transform", "translate(0," + height + ")")
  .call(d3.axisBottom(x));

g.append("g")
  .attr("class", "y-axis")
  .attr("transform", "translate(0," + 0 + ")")
  .call(d3.axisLeft(y));


var bar = g.selectAll('.bar')
  .data(bins)
  .enter().append('g')
      .attr('class','bar')
      .attr('transform', function(d) { return "translate(" + x(d.x0) + "," + y(d.length) + ")"; });

bar.append('rect')
  .attr('x',1)
  .attr("width", x(bins[0].x1) - x(bins[0].x0) - 1)
  .attr("fill", material[0])
  .attr("height", function(d) { return height - y(d.length); })

})();