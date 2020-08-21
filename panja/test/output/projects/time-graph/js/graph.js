var margin = {top: 30, right: 100, bottom: 30, left: 30},
    width = innerWidth - margin.left - margin.right,
    height = innerHeight - margin.top - margin.bottom,
    n1 = 4889,
    n2 = 4156,
    n1 = 200,
    n2 = 170,
    c = 0.02,
    win = 1.7,
    limit = 10
    frame = parseInt(window.location.search.replace(/\D/g, ''));

// set svg size and create padded group
var svg = d3.select("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// create x, y scales and axes
var x = d3.scaleTime().range([0, width]),
    y = d3.scaleLinear().range([height, 0]),
    xAxis = d3.axisTop(x).tickSize(height).ticks(7),
    yAxis = d3.axisRight(y).tickSize(width);

// create group to move x-axis
var xAxisG = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", "translate(0," + height + ")");

// create group to move y-axis and call it
var yAxisG = g.append("g")
    .attr("class", "y-axis")
    .attr("transform", "translate(" + "0" + ",0)")

// set line properties
var valueline = d3.line()
    .defined(function(d) { return d; })
    .curve(d3.curveBasis)
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.rank); })

g.append("clipPath")
      .attr("id", "clip")
    .append("rect")
      .attr("width", width/win)
      .attr("height", height);

// set date parsing
var parseTime = d3.timeParse("%Y-%m");
var formatTime = d3.timeFormat("%b %Y");

// get data from csv
d3.csv('/projects/time-graph/data/animals.csv', function(error, data) {
  // parse each date
  data.forEach(function(d) {
      d.date = parseTime(d.date);
      d.rank = +d.rank;
  });
  //
  var groups = [];
  var values = [];
  var tags = ['dog','chicken','cat','horse','fish','bird','bear','gray wolf','duck','rabbit','lion'];

  for (var i=0; i<tags.length; i++) {
    temp = [];
    cur = data.filter(function(d) {
      return d.tag == tags[i];
    });
    cur = cur.slice(75,cur.length);
    groups.push(cur);
    cur.forEach(function(d) {
      temp.push(d.rank);
    });
    values.push(temp);
  }

  function compare(a,b) {
    if (a.rank<b.rank) { return 1; }
    if (a.rank>b.rank) { return -1; }
    return 0;
  }
  
  function softmax(values) {
    total = 0;
    soft_pos = [];
    soft_height = [];
    exp_list = values.map(function(x) { return Math.pow(1.3,x); });
    exp_sum = exp_list.reduce(function(a,b) { return a+b; });
    for (var i=0; i<values.length; i++) {
      soft_height.push(exp_list[i]/exp_sum);
      soft_pos.push(total);
      total += exp_list[i]/exp_sum;
    }
    return [soft_height, soft_pos];
  }

  // nullify values not in top: limit
  /*for (var i=0; i<groups[0].length; i++) {
    var temp = [];
    for (var j=0; j<groups.length; j++) {
      temp.push(groups[j][i]);
    }
    temp = temp.sort(compare).slice(0,limit);
    for (var j=0; j<groups.length; j++) {
      if (temp.indexOf(groups[j][i]) <= -1) {
        groups[j][i] = null;
      }
      //console.log(groups[j][i]);
    }
  }*/

  // interpolate all dates for smooth graph movement
  spread = d3.interpolate(groups[0][0].date, groups[0][groups[0].length-1].date);
  curves = []
  for (var i=0; i<values.length; i++) {
    curves.push(d3.interpolateBasis(values[i]));
  }

  // create paths with data
  var color = d3.scaleOrdinal(d3.schemeCategory20)
        //.range(['#FF358B', '#01B0F0', '#AEEE00']);
  g.selectAll('.line')
      .data(groups) // set data for entire visualization
      .enter()
        .append('path')
        .attr('class', 'line')
        .style('stroke', function(d) {
          return color(Math.random());
        })
  
  g.selectAll('.tags')
    .data(groups)
    .enter()
      .append('text')
      .attr('class', 'tags')
      .text(function(d) { if (d[0] !== null) { return d[0].tag; }});

  g.append('text').text('Animal Rank On')
    .attr('x', innerWidth*(6/8))
    .attr('y', innerHeight*(1/15))
    .style('font-size','25px')

  g.append('text')
      .attr('class','cur_date')
      .style('font-size','35px')
      .attr('x', innerWidth*(6/8))
      .attr('y', innerHeight*(2/15))
      .style('bottom', 0)
      .style('right', 0)
      .style('position', 'absolute')
 
  
  // initiate timer funciton to move graph over time
  d3.timer(function(d) {
    // set x domain d/n+c, where n/1000 is secs and c is 
    // axis window (with respect to interpolated spread)
    if (frame) {
      start = frame/12000;
      end = frame/10200;
    } else {
      start = d/(n1*1000);
      end = d/(n2*1000)+c;
    }
    x.domain([+spread(start), +spread(end)]);

    curves_map = curves.map(function(a) { return a(start+(end-start)/win+0.00035); })

    ext = d3.extent(curves_map);
    rng = ext[1] - ext[0];
    y.domain([ext[0]-rng*0.1, Math.min(100,ext[1]+rng*0.1)]);

    xAxisG.call(xAxis)
      .selectAll("text")
      .attr("y", 16)
      .attr("fill", "#444");

    yAxisG.call(yAxis)
      .selectAll("text")
      .attr("x", 4)
      .attr("dy", -4)
      .attr("fill", "#444")

    // update line every millisecond
    d3.selectAll('.line')
      .data(groups.map(function(x) { return x.slice(Math.max(1,Math.floor(start*x.length)-2),Math.floor((start+(end-start)/win)*x.length+4)); }))
      .attr('clip-path', 'url(#clip)')
      .attr('d', valueline)

    var color = d3.scaleOrdinal(d3.schemeCategory20)
    d3.selectAll('.tags')
      .data(curves_map)
      .attr('dy',function(d) { return y(d)+4; })
      .attr('dx',width/win+12)
      .style('fill', function(d) { return color(d); });

    //var color = d3.scaleOrdinal(d3.schemeCategory20)
    //.range(['#FF358B', '#01B0F0', '#AEEE00']);

    d3.select('.cur_date')
      .text(formatTime(spread(start+(end-start)/win)))
    
    /*//var color = d3.scaleOrdinal(d3.schemeCategory20)
    top3 = curves_map.sort().reverse().slice(0,5);
    g.selectAll('.bars')
      .data(curves_map)
      .enter()
        .append('circle')
        .attr('class', 'bars')
    
    d3.selectAll('.bars')
      .data(top3)
      //.attr('width',230)
      .attr('cx', width-200)
      .style('fill', function(d) { return color(d); })
      .style('stroke-width',0);
       
    d3.selectAll('.bars')
        .data(softmax(top3)[0])
        .attr('r', function(d) { return d*height/4.5; })
    
    d3.selectAll('.bars')
        .data(softmax(top3)[1])
        .attr('cy', function(d) { return d*110+300; })*/
    
    // full view smooth sliding
    //d3.selectAll('rect')
    //  .attr('width', x(+spread(start+(end-start)/1.5)));
  });
});
