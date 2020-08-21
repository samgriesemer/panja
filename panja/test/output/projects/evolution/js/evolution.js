// parameter variables
let m = 50;
let max_o = 50;
let max_vx = 10;
let max_vy = 10;
let organisms = [];
let foods = [];
let count = 0;
let gen = 0;
let range = 20;
let diameter = 16;

var main = function(cnv) {
  // main setup
  cnv.setup = function() {
    // main canvas
    cnv.createCanvas(cnv.round(innerWidth/1.6), cnv.round(innerHeight/1.5));
    cnv.frameRate(60);

    // populate organisms
    for (i=0; i<max_o; i++) {
      organisms.push(new Organism());
      //foods.push(new Food());
    }
  }

  // main draw
  cnv.draw = function() {
    cnv.background(255);
    for (var t=0;t<organisms.length;t++) {
      org = organisms[t];
      food = foods[t]
      org.move(organisms, t);
      org.update(false, null, organisms);
      org.display(t);
      //food.display();
    }
    balance(organisms);
    count++;    
  }
}

var net = function(cnv) {
  // net setup
  cnv.setup = function() {
    // net canvas
    cnv.createCanvas(cnv.round(innerWidth/6), cnv.round(innerHeight/6));
    batch_size = X.rows();
    iters = 1;
    act = 1;
    clrs = [[
        [216,216,216],
        [40,40,40],
        [0,0,0]
      ]];
    clr = clrs[Math.floor(Math.random()*clrs.length)]
  }

  // net draw
  cnv.draw = function() {
    cnv.background(255);
    if (count > 5) {
      draw_network(organisms[0],organisms[0].layers,act,0,0,cnv.round(innerWidth/6),cnv.round(innerHeight/6));
    }
  }
}

var main_p5 = new p5(main, "main-container");
var net_p5 = new p5(net, "net-container");

// Organism class definitions
function Organism() {
  this.size = main_p5.random(20, 30);
  this.pos = main_p5.createVector(main_p5.random(this.size/2, main_p5.width-this.size/2), main_p5.random(this.size/2, main_p5.height-this.size/2));
  this.vel = main_p5.createVector(main_p5.random(-max_vx,max_vx), main_p5.random(-max_vy,max_vy));
  this.clr = main_p5.color(main_p5.random(255), main_p5.random(255), main_p5.random(255));
  //this.layers = [4,28,12,2];
  this.layers = [4,8,8,2];
  this.brain = new NN(this.layers, 10.0, 0.01, 1.0, true);
  this.time_alive = 0;
  this.vel_list = [this.vel.x,this.vel.y];
}

Organism.prototype.move = function(orgs, t) {
  this.pos.x += this.vel.x;
  this.pos.y += this.vel.y;
  if (this.pos.x - this.size/2 > main_p5.width || this.pos.x + this.size/2 < 0) { 
    orgs.splice(t,1);
  }
  if (this.pos.y - this.size/2 > main_p5.height || this.pos.y + this.size/2 < 0) { 
    orgs.splice(t,1);
  }
  if (this.vel.mag() < 0.1) { 
    orgs.splice(t,1);
    console.log("killed for slowness");
  }
  if (this.time_alive > 5000) { 
    orgs.splice(t,1); 
    console.log("killed for time");
  }
}

Organism.prototype.display = function(t) {
  main_p5.noFill();
  main_p5.stroke(this.clr)
  main_p5.strokeWeight(4);
  if (t === 0) { 
    main_p5.ellipse(this.pos.x, this.pos.y, 70);
  } else {
    main_p5.ellipse(this.pos.x, this.pos.y, this.size);
  }
  n_vel = main_p5.createVector(this.vel.x, this.vel.y);
  n_vel.normalize();
  main_p5.line(this.pos.x, this.pos.y, this.pos.x+n_vel.x*this.size/2, this.pos.y+n_vel.y*this.size/2);
}

Organism.prototype.update = function(run, Y, orgs) {
  // create X and Y for training if run
  X = Matrix.create([[this.pos.x/main_p5.width, this.pos.y/main_p5.height,
                      this.vel.x/max_vx, this.vel.y/max_vy]]);
  if (run) { this.brain.run(X,Y,1,1); }

  // feed X through node brain & set output to velocity
  out = this.brain.fit(X,Y,true);
  this.vel.x = out.e(1,1);
  this.vel.y = out.e(1,2);
  this.vel_list.push(this.vel.x);
  this.vel_list.push(this.vel.y);
  if (this.vel_list.length > 4) {
    this.vel_list.splice(0,2);
  }
  this.time_alive++

  // update food
  for (var i=0; i<foods.length; i++) {
    distance = main_p5.dist(this.pos.x,this.pos.y,foods[i].pos.x,foods[i].pos.y)
    if (distance<this.size/2) {
      foods.splice(i,1)
      foods.push(new Food())
    }
  }
} 

function balance(orgs) {
  fitness(orgs);
  orgs.sort(compare).reverse();
  if (orgs.length < max_o) {
    r1 = Math.floor(Math.pow(Math.random(),2)*orgs.length);
    r2 = Math.floor(Math.pow(Math.random(),2)*orgs.length);
    while (r1 == r2) {
      r2 = Math.floor(Math.pow(Math.random(),2)*orgs.length); 
    }
    parent1 = orgs[r1];
    parent2 = orgs[r2];
    o = new Organism();
    crossover(parent1, parent2, o);
    mutate(o, 0.06, 1.0);
    o.brain.fit(X,null,true);
    orgs.push(o);
    gen++;
  }
  document.getElementById("fitness").innerHTML = "Fitness: "+Math.round(orgs[0].fitness*100)/100;
  document.getElementById("vel").innerHTML = "Velocity: "+Math.round(orgs[0].vel.mag()*100)/100;
  document.getElementById("time").innerHTML = "Time alive: "+orgs[0].time_alive;
  document.getElementById("gen").innerHTML = "Generation: "+gen;
}

function crossover(node1, node2, child) {
  w1 = node1.brain.w;
  w2 = node2.brain.w;
  for (var i=0; i<w1.length; i++) {
    // random layer crossover
    layer = Math.floor(main_p5.random(w1[i].rows()-1))+1;
    m1 = w1[i].minor(1,1,layer,w1[i].cols());
    m2 = w2[i].minor(layer+1,1,w1[i].rows()-layer,w1[i].cols());
    child.brain.w[i] = Matrix.create(m1.transpose().augment(m2.transpose())).transpose();

    clrs = [node1.clr.levels,node2.clr.levels];
    child.clr = main_p5.color(clrs[Math.floor(Math.random()*clrs.length)][0],
                              clrs[Math.floor(Math.random()*clrs.length)][1],
                              clrs[Math.floor(Math.random()*clrs.length)][2]);
    // random weight crossover (to be coded)
    //bin_m = Matrix.Math.Random(w1[i].rows(), w1[i].cols());
    //bin_m = bin_m.map(function(x) { return Math.round(x); });
    //child_w = ewise_mult(w1[i],bin_m).add(ewise_mult(w2[i],comp(bin_m)));
    //child.brain.w[i] = child_w;
    //single point crossover (to be coded)
  }
}

function mutate(child, rate, val) {
  if (main_p5.random() <= rate) {
    console.log("mutate!");
    rand_layer = Math.floor(main_p5.random(child.brain.w.length));
    rand_i     = Math.floor(main_p5.random(child.brain.w[rand_layer].rows()))+1;
    rand_j     = Math.floor(main_p5.random(child.brain.w[rand_layer].cols()))+1;
    child.brain.w[rand_layer] = child.brain.w[rand_layer].map(function(x,i,j) { 
      return (rand_i==i && rand_j==j) ? x+main_p5.random(-val,val) : x;
    });
  }
}

function fitness(orgs) {
  for (var i=0; i<orgs.length; i++) {
    org = orgs[i];
    avg_vel = org.vel_list.reduce(function(a,b) { return a+b; }, 0);
    org.fitness = org.vel.mag()*44 + 30*Math.log(org.time_alive) - (1/Math.pow(org.vel.mag(),8)) - (4000/Math.pow(avg_vel,2));
    //org.fitness = (30*Math.log(org.time_alive)-60) - (Math.pow(10,6) / Math.pow(org.vel.mag()+avg_vel,6));
  }
}

// helper functions
function comp(m) {
  r = m.map(function(x) { return 1-x; });
  return r;
}

function mat_2_list(m) {
  l = [];
  m.map(function(x) { l.push(x); });
  return l;
}

function ewise_mult(m1, m2) {
  r = m1.map(function(x,i,j) { return x * m2.e(i,j); });
  return r;
}

function compare(a,b) {
  if (a.fitness < b.fitness)
     return -1;
  if (a.fitness > b.fitness)
    return 1;
  return 0;
}

// network visualization
function node(x,y) {
  this.pos = main_p5.createVector(x,y);
}

node.prototype.draw_node = function(i,j,act,org) {
  nog = org.brain;
  net_p5.stroke(255);
  net_p5.strokeWeight(0.5);
  net_p5.fill(clr[2][0],clr[2][1],clr[2][2]);
  net_p5.ellipse(this.pos.x,this.pos.y,diameter);
  net_p5.fill(255);
  // find max velocity
  top_vx = net_p5.max(organisms.map(function(o) { return Math.abs(o.vel.x); }));
  top_vy = net_p5.max(organisms.map(function(o) { return Math.abs(o.vel.y); }));

  if (i !== 0 && i < nog.layers.length-1) {
    net_p5.ellipse(this.pos.x,this.pos.y,nog.acts[i-1].e(act,j+1)*(diameter-4));
  }
  else if (i == nog.layers.length-1) {
    sum = 0;
    for (var p=0; p<nog.acts[i-1].cols(); p++) { 
      sum += Math.abs(nog.acts[i-1].e(act,p+1)); 
    }
    net_p5.ellipse(this.pos.x,this.pos.y,(nog.acts[i-1].e(act,j+1)/sum)*(diameter-4));
  }
  else if (i == 0) {
    sum = 0;
    X = Matrix.create([[org.pos.x/main_p5.width, org.pos.y/main_p5.height,
                      org.vel.x/top_vx, org.vel.y/top_vy]]);
    net_p5.ellipse(this.pos.x,this.pos.y,X.e(1,j+1)*(diameter-4));
  }
}

function create_network(sx,sy,w,h,layers,init,act,org) {
  if (init) {
    w_pad = 0;
    h_pad = 10;
    w_space = (w-2*w_pad) / layers.length;
    h_space = (h-2*h_pad);
    nodes = [];
  }
  for (var i=0; i<layers.length; i++) {
    temp_nodes = [];
    for (var j=0; j<layers[i]; j++) {
      if (init) {
        temp = new node(w_pad+(w_space/2)+w_space*i,h_pad+((h_space/(layers[i]+1))*(j+1)));
        temp.pos.x += sx;
        temp.pos.y += sy;
        temp_nodes.push(temp);
      }
      if (!init) {
        nodes[i][j].draw_node(i,j,act,org);
      }
    }
    if (init) { nodes.push(temp_nodes); }
  }
  return nodes;
}

function draw_network(org,layers,act,p1,p2,w,h) {
  nodes = create_network(p1,p2,w,h,layers,true,act,org);
  for (var i=0; i<nodes.length; i++) {
    for (var j=0; j<nodes[i].length; j++) {
      if (i != nodes.length-1) {
        for(var k=0; k<nodes[i+1].length; k++) {
          w_temp = org.brain.w[i].minor(1,2,org.brain.w[i].rows(),
                           org.brain.w[i].cols()-1);
          weight = w_temp.e(k+1,j+1);
          if (weight>=0) { 
            net_p5.stroke(clr[0][0],clr[0][1],clr[0][2]); 
          } else { 
            net_p5.stroke(clr[1][0],clr[1][1],clr[1][2]);
            weight *= -1;
          }
          net_p5.strokeWeight(weight/8);
          net_p5.line(nodes[i][j].pos.x,nodes[i][j].pos.y,
             nodes[i+1][k].pos.x,nodes[i+1][k].pos.y);
        }
      }
    }
  }
  create_network(0,0,0,0,layers,false,act,org);
}

/*
function Food() {
  this.size = 5
  this.pos = createVector(Math.random(this.size/2, width-this.size/2), Math.random(this.size/2, height-this.size/2))
}

Food.prototype.display = function() {
  stroke(255);
  strokeWeight(0.5);
  fill(0,0,0);
  ellipse(this.pos.x,this.pos.y,4);
}
*/