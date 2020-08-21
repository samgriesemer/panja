var margin = {top: 30, right: 30, bottom: 30, left: 30},
    width = d3.max([300,window.innerWidth/9]) - margin.left - margin.right,
    height = 200 - margin.top - margin.bottom,
    full_width = width + margin.left + margin.right,
    full_height = height + margin.top + margin.bottom;
    
var material = ['#F44336','#E91E63','#9C27B0','#673AB7','#3F51B5','#2196F3','#03A9F4','#00BCD4','#009688','#4CAF50','#8BC34A','#CDDC39','#FFEB3B','#FFC107','#FF9800','#FF5722','#795548','#9E9E9E','#607D8B','#000000'],
    material = ['#d1e4f1', '#13466b', '#f7f00a', '#e01c49', '#facc05'],
    //material = ['#F7F00A', '#EA638C', '#B33C86', '#190E4F', '#00000'],
    //material = ['#d1e4f1', '#FFD23F', '#EE4266', '#540D6E'],
    material = ['#d1e4f1', '#f7f00a', '#EE4266', '#540D6E'],
    //material = ['#fa4b4b', '#3ae4c5', '#0098d2', '#f7e87c'],
    //material = ['#000','#f7f00a'],
    mat = d3.scaleOrdinal(material);

var format = d3.format(',d');

var div = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("display", "none");

function mouseover() {
    div.style("display", "inline");
}

function mouseout() {
    div.style("display", "none");
}

(function() { // wrapper to avoid variable override between files
 
var svg = d3.select("#pie")
    .attr("width", full_width)
    .attr("height", full_height),
    g = svg.append("g").attr("transform", "translate(" + full_width / 2 + "," + full_height / 2 + ")"),
    radius = height/2.7;

d3.csv('/data/pie.csv', function(d) {
    d.count = +d.count;
    return d;
}, function(error, data) {
    if (error) throw(error);
    
    var pie = d3.pie()
        .value(function(d) { return d.count })

    var path = d3.arc()
        .outerRadius(radius)
        .innerRadius(radius/2);
  
    var arc = g.append('g')
        .selectAll('g')
        .data(pie(data))
        .enter().append('g')
            .attr('class','arc');
  
    arc.append('path')
        .attr('d', path)
        .attr('fill', function(d, i) { return mat(i); })
  
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
        .style("fill", function(d, i) { return mat(i); });

    legend.append("text")
        //.attr("x", radius*2.5-5)
        .attr("y", 7.5)
        .attr("dy", "0.32em")
        .text(function(d) { return d.data.animal; });
  
    arc      
        .on("mouseover", mouseover)
        .on("mousemove", function(d) {
            div
                .style("left", (d3.event.pageX - 34) + "px")
                .style("top", (d3.event.pageY - 12) + "px")
                .text(d.data.animal + ' : ' + d.data.count)
                .selectAll('rect').data(data)
                .enter().append('rect')
                        .attr("x", (d3.event.pageX - 38) + "px")
                        .attr("y", (d3.event.pageY - 16) + "px")
                        .attr("width", 15)
                        .attr("height", 15)
                        .attr("fill", mat(d.animal));
            })
        .on("mouseout", mouseout);
});
  
})();