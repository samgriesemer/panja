// margin = {top: 0, right: 0, bottom: 0, left: 0}
// width = innerWidth - margin.left - margin.right;
// height = innerHeight - margin.top - margin.bottom;

// var svg = d3.select("svg")
//     .attr("width", width + margin.left + margin.right)
//     .attr("height", height + margin.top + margin.bottom),
//     g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// var x = d3.scaleLinear().range([0, width]).domain([0,width]),
//     y = d3.scaleLinear().range([height, 0]).domain([height,0]);

// var valueline = d3.line()
//     .defined(function(d) { return d; })
//     .curve(d3.curveLinear)
//     .x(function(d) { return x(d.x); })
//     .y(function(d) { return y(d.y); });

// /////////

// max_o = 20;
// max_vx = 20;
// max_vy = 20;
// organisms = [];
// count = 0;
// gen = 0;
// range = 20;
// fadeInterval = 50;
// only_top = false;
// do_fade = true;

// diameter = 12;
// batch_size = X.rows();
// iters = 1;
// act = 1;
// clrs = [[
// 		[1,176,240],
// 		[174,238,0],
// 		[0,0,0]
// 	]];
// clr = clrs[Math.floor(Math.random()*clrs.length)]

// //////////

// function Organism() {
// 	this.size = rand(0,1.5);
// 	this.pos = createVector(rand(this.size/2, width-this.size/2), rand(this.size/2, height-this.size/2));
// 	this.vel = createVector(rand(-max_vx,max_vx), rand(-max_vy,max_vy));
// 	this.clr = d3.rgb(rand(0,255), rand(0,255), rand(0,255));
// 	this.layers = [4,22,12,2];
// 	this.brain = new NN(this.layers, 20.0, 0.01, 1.0, true);
// 	this.time_alive = 0;
// 	this.vel_list = [this.vel.x,this.vel.y];
// 	this.pos_log = [];
// 	this.log = false;
// }

// Organism.prototype.move = function(orgs, t) {
// 	this.pos.x += this.vel.x;
// 	this.pos.y += this.vel.y;
// 	//if (this.log) {
// 	this.pos_log.push(createVector(this.pos.x, this.pos.y));
// 	//}
// 	if (this.pos.x - this.size/2 > width || this.pos.x + this.size/2 < 0) { 
// 		orgs.splice(t,1);
// 	}
// 	if (this.pos.y - this.size/2 > height || this.pos.y + this.size/2 < 0) { 
// 		orgs.splice(t,1);
// 	}
// 	if (mag(this.vel) < 0.1) { 
// 		orgs.splice(t,1);
// 		console.log("killed for slowness");
// 	}
// 	if (this.time_alive > 5000) { 
// 		orgs.splice(t,1); 
// 		console.log("killed for time");
// 	}
// }

// Organism.prototype.update = function(run, Y, orgs) {
// 	// create X and Y for training if run
// 	X = Matrix.create([[this.pos.x/width, this.pos.y/height,
// 											this.vel.x/max_vx, this.vel.y/max_vy]]);
// 	if (run) { this.brain.run(X,Y,1,1); }

// 	// feed X through node brain & set output to velocity
// 	out = this.brain.fit(X,Y,true);
// 	this.vel.x = out.e(1,1);
// 	this.vel.y = out.e(1,2);
// 	this.vel_list.push(this.vel.x);
// 	this.vel_list.push(this.vel.y);
// 	if (this.vel_list.length > 4) {
// 		this.vel_list.splice(0,2);
// 	}
// 	this.time_alive++
// } 

// function balance(orgs) {
// 	fitness(orgs);
// 	orgs.sort(compare).reverse();
// 	while (orgs.length < max_o) {
// 		r1 = Math.floor(Math.pow(Math.random(),2)*orgs.length);
// 		r2 = Math.floor(Math.pow(Math.random(),2)*orgs.length);
// 		while (r1==r2) { r2 = Math.floor(Math.pow(Math.random(),2)*orgs.length); }
// 		parent1 = orgs[r1];
// 		parent2 = orgs[r2];
// 		o = new Organism();
// 		crossover(parent1, parent2, o);
// 		mutate(o, 0.06, 1.0);
// 		o.brain.fit(X,null,true);
// 		orgs.push(o);
// 		gen++;
// 	}
// }

// function crossover(node1, node2, child) {
// 	w1 = node1.brain.w;
// 	w2 = node2.brain.w;
// 	for (var i=0; i<w1.length; i++) {
// 		// random layer crossover
// 		layer = Math.floor(rand(0,w1[i].rows()-1))+1;
// 		m1 = w1[i].minor(1,1,layer,w1[i].cols());
// 		m2 = w2[i].minor(layer+1,1,w1[i].rows()-layer,w1[i].cols());
// 		child.brain.w[i] = Matrix.create(m1.transpose().augment(m2.transpose())).transpose();

// 		/*clrs = [node1.clr.levels,node2.clr.levels];
// 		child.clr = color(clrs[Math.floor(random()*clrs.length)][0],
// 						  clrs[Math.floor(random()*clrs.length)][1],
// 						  clrs[Math.floor(random()*clrs.length)][2]);*/

// 		// random weight crossover (to be coded)
// 		//bin_m = Matrix.Random(w1[i].rows(), w1[i].cols());
// 		//bin_m = bin_m.map(function(x) { return Math.round(x); });
// 		//child_w = ewise_mult(w1[i],bin_m).add(ewise_mult(w2[i],comp(bin_m)));
// 		//child.brain.w[i] = child_w;

// 		//single point crossover (to be coded)
// 	}
// }

// function mutate(child, rate, val) {
// 	if (Math.random() <= rate) {
// 		console.log("mutate!");
// 		rand_layer = Math.floor(rand(0,child.brain.w.length));
// 		rand_i     = Math.floor(rand(0,child.brain.w[rand_layer].rows()))+1;
// 		rand_j     = Math.floor(rand(0,child.brain.w[rand_layer].cols()))+1;
// 		child.brain.w[rand_layer] = child.brain.w[rand_layer].map(function(x,i,j) { 
// 			return (rand_i==i && rand_j==j) ? x+Math.random(-val,val) : x;
// 		});
// 	}
// }

// function fitness(orgs) {
// 	for (var i=0; i<orgs.length; i++) {
//     org = orgs[i];
// 		avg_vel = org.vel_list.reduce(function(a,b) { return a+b; }, 0);
// 		org.fitness = mag(org.vel)*44 + 30*Math.log(org.time_alive) - (1/Math.pow(mag(org.vel),8)) - (4000/Math.pow(avg_vel,2));
// 		//org.fitness = (30*Math.log(org.time_alive)-60) - (Math.pow(10,6) / Math.pow(org.vel.mag()+avg_vel,6));
// 	}
// }

// function createVector(x, y) {
// 	return { x:x, y:y };
// }

// function mag(vect) {
// 	return Math.sqrt(Math.pow(vect.x,2) + Math.pow(vect.y,2));
// }

// function rand(min,max)
// {
//     return Math.random()*(max-min)+min;
// }

// function comp(m) {
// 	r = m.map(function(x) { return 1-x; });
// 	return r;
// }

// function mat_2_list(m) {
// 	l = [];
// 	m.map(function(x) { l.push(x); });
// 	return l;
// }

// function ewise_mult(m1, m2) {
// 	r = m1.map(function(x,i,j) { return x * m2.e(i,j); });
// 	return r;
// }

// function compare(a,b) {
//   if (a.fitness < b.fitness)
//      return -1;
//   if (a.fitness > b.fitness)
//     return 1;
//   return 0;
// }

// /////////

// /*for (i=0; i<max_o; i++) {
// 	organisms.push(new Organism());
// 	if (i === max_o-1) {

// 		for (var i=0;i<1000;i++) {

// 			/*if (d/1000%fadeInterval == 0 && do_fade) {
// 				//noStroke();
// 			    //fill(255,255,255,5);
// 			    //rect(0,0,width,height);
// 			 }

// 			if (d/1000 == 4000) {
// 				//background(255);
// 				top_orgs = organisms.slice(0,3);
// 				//max_o = 4;
// 				only_top = true;
// 				do_fade = false;
// 			}

// 			for (var t=0;t<organisms.length;t++) {
// 				org = organisms[t];
// 				org.move(organisms, t);
// 				org.update(false, null, organisms);
// 				//if (only_top) { continue; }
// 			}

// 			// generate with replacement
// 			/*if (only_top) {
// 				for (i=0;i<top_orgs.length;i++) {
// 					org_idx = organisms.indexOf(top_orgs[i]);
// 					if (org_idx === -1) {
// 						new_idx = Math.floor(random()*random()*organisms.length)
// 						top_orgs[i] = organisms[new_idx];
// 					} else {
// 						top_orgs[i] = organisms[org_idx];
// 					}
// 					top_orgs[i].display(i);
// 				}
// 			}

// 			balance(organisms);
// 			count++;

// 			if (i === 999) {
// 				var color = d3.scaleOrdinal(d3.schemeCategory20)
// 				g.selectAll('.line')
// 				    .data(organisms)
// 				    .enter()
// 				    	.append('path')
// 				    	.attr('class', 'line')
// 				    	.style('stroke', function(d) {
// 				     		return d.clr + '';
// 				    	})
// 				    	.data(organisms.map(function(x) { return x.pos_log; }))
// 							.attr('d', valueline);
// 			}
// 		}
// 	}
// }*/

// total_orgs = [];
// log_list = []

// var t = d3.timer(function(d) {

// 	if (organisms.length === 0) {
// 		for (i=0; i<max_o; i++) {
// 			organisms.push(new Organism());
// 		}

// 		top_orgs = organisms.slice(0);
// 	}

// 	for (i=0;i<top_orgs.length;i++) {
// 		org_idx = organisms.indexOf(top_orgs[i]);
// 		if (org_idx === -1) {
// 			new_idx = Math.floor(Math.random()*Math.random()*organisms.length)
// 			top_orgs[i] = organisms[new_idx];
// 			//top_orgs[i].log = true;
// 			if (d>10000) { total_orgs.push(organisms[new_idx]) };
// 		} else {
// 			top_orgs[i] = organisms[org_idx];
// 		}
// 	}

// 	top_orgs = organisms.slice(0)

// 	/*g.selectAll('.line')
// 	    .data(top_orgs)
// 	    .enter()
// 	    	.append('path')
// 	    	.attr('class', 'line')

// 	d3.selectAll('.line')
// 		.style('stroke', function(d) {
//      		return d.clr + '';
//     	})
//     	.data(top_orgs.map(function(x) { return x.pos_log; }))
// 			.attr('d', valueline);*/

// 	for (var t=0;t<organisms.length;t++) {
// 		org = organisms[t];
// 		org.move(organisms, t);
// 		org.update(false, null, organisms);
// 		org.log = false;
// 	}

// 	balance(organisms);
// 	count++;

// 	g.selectAll('.line')
//     .data(total_orgs)
//     .enter()
//     	.append('path')
//     	.attr('class', 'line')

// 	d3.selectAll('.line')
// 		.style('stroke', function(d) {
//      		return d.clr + '';
//     	})
//     	.data(total_orgs.map(function(x) { return x.pos_log; }))
// 			.attr('d', valueline);

// })