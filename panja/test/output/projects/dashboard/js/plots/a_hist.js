(function() { // wrapper to avoid variable override between files

var svg = d3.select("#a_hist")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x_axis = g.append("g")
  .attr("class", "x-axis")
  .attr("transform", "translate(0," + height + ")");

var y_axis = g.append("g")
  .attr("class", "y-axis")
  .attr("transform", "translate(0," + 0 + ")");

var x = d3.scaleLinear()
  .domain([-5,5])
  .range([0,width]);

var histogram = d3.histogram()
  .domain(x.domain())
  .thresholds(x.ticks(50))

var normal = [],
    bins = histogram(normal);
  
var y = d3.scaleLinear()
    .range([height,0]);

var bar = g.selectAll('.bar')
  .data(bins)
  .enter().append('g')
      .attr('class','bar')

bar.append('rect')
  .attr('x',1)
  .attr("width", x(bins[0].x1) - x(bins[0].x0) - 1)
  .attr("fill", material[0]);

var sec = 0,
    sample = d3.randomNormal();

d3.timer(function(d) {

  if (normal.length >= 5000) {
    normal = [];
  } else {
    for (var i=0; i<10; i++) {
      normal.push(sample());
    }
  }

  bins = histogram(normal);
  y.domain([0,d3.max(bins, function(d) { return d.length; })]);
  
  g.selectAll('.bar')
        .data(bins)
        .attr('transform', function(d) { return "translate(" + x(d.x0) + "," + y(d.length) + ")"; })
  
  g.selectAll('rect')
        .data(bins)
        .attr("height", function(d) { return height - y(d.length); })

  x_axis.call(d3.axisBottom(x));
  y_axis.call(d3.axisLeft(y));
})

})();