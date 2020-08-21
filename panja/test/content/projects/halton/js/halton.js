// halton function
function halton(n, b) {
    out = [];
    for (var i=1; i<=n; i++) {
        j = i;
        f = 1;
        r = 0;
        while (j>0) {
            f = f/b;
            r = r+f*(j%b);
            j = Math.floor(j/b);
        }
        out.push(r);
    }
    return out;
}

// tooltip
var div = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("display", "none");

function mouseover() {
    div.style("display", "inline");
}

function mouseout() {
    div.style("display", "none");
}

// generate halton data
n = document.getElementById('slider').valueAsNumber;
p0 = 2;
p1 = 3;
hx = halton(n, p0);
hy = halton(n, p1);
seq = [];

for (var i=0; i<n; i++) {
    seq.push({ x:hx[i], y:hy[i] });
}

// d3
var margin = {top: 30, right: 30, bottom: 30, left: 50},
    width = 520 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;
    
var material = ['#F44336','#E91E63','#9C27B0','#673AB7','#3F51B5','#2196F3','#03A9F4','#00BCD4','#009688','#4CAF50','#8BC34A','#CDDC39','#FFEB3B','#FFC107','#FF9800','#FF5722','#795548','#9E9E9E','#607D8B','#000000'],
    mat = d3.scaleOrdinal(material);

var svg = d3.select("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom),
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x = d3.scaleLinear()
  .domain([0,1])
  .range([0,width]);

var y = d3.scaleLinear()
    .domain([0,1])
    .range([height,0]);

g.append("g")
  .attr("class", "x-axis")
  .attr("transform", "translate(0," + height + ")")
  .call(d3.axisBottom(x));

g.append("g")
  .attr("class", "y-axis")
  .attr("transform", "translate(0," + 0 + ")")
  .call(d3.axisLeft(y));

circles = g.selectAll('circle')
    .data(seq)
    .enter().append('circle')
        .attr('cx', d => x(d.x))
        .attr('cy', d => y(d.y))
        .attr('r', 3)
        .attr('fill', (d,i) => d3.interpolateMagma(i/n));

circles        
    .on("mouseover", mouseover)
    .on("mousemove", function(d) {
        div
            .style("left", (d3.event.pageX - 34) + "px")
            .style("top", (d3.event.pageY - 12) + "px")
            .text(Math.round(d.x*100)/100 + ', ' + Math.round(d.y*100)/100)
        })
    .on("mouseout", mouseout);

d3.select('#slider')
    .on('input', function() {
        update(+this.value, 1);
        d3.select('#length-value').text(this.value);
})

d3.select('#p0-slider')
    .on('input', function() {
        update(+this.value, 2);
        d3.select('#p0-value').text(this.value);
})

d3.select('#p1-slider')
    .on('input', function() {
        update(+this.value, 3);
        d3.select('#p1-value').text(this.value);
})

        
function update(val,pos) {
    if (pos==1) {n = val;}
    if (pos==2) {p0 = val;}
    if (pos==3) {p1 = val;}
    hx = halton(n, p0);
    hy = halton(n, p1);
    seq = [];
    for (var i=0; i<n; i++) {
        seq.push({ x:hx[i], y:hy[i] });
    }
    circles.remove();
    circles = g.selectAll('circle')
        .data(seq)
        .enter().append('circle')
            .attr('cx', d => x(d.x))
            .attr('cy', d => y(d.y))
            .attr('r', 3)
            .attr('fill', (d,i) => d3.interpolateMagma(i/n));
}