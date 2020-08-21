function NN(layers, epsilon, lambda, _alpha, regression) {
	this.regression = regression;
	this.layers     = layers;
	this.epsilon    = epsilon;
	this.lambda     = lambda;
	this._alpha     = _alpha;
	this.w          = [];
	this.err        = 0;

	for (var i=0;i<layers.length-1;i++) {
		m = Matrix.Random(layers[i+1], layers[i]+1);
		m = add_s(m.x(2).x(epsilon), epsilon*(-1));
		this.w.push(m);
	}
}

NN.prototype.sigmoid = function(z) {
	return z.map(function(x) { return 1/(1+Math.exp(-x)); });
}

NN.prototype.s_prime = function(z) {
	return ewise_mult(z, add_s(z.x(-1), 1));
}

NN.prototype.fit = function(X, Y, predict) {
	a = X;
	A = [];
	this.acts = [];
	w_grad = [];
	for (var i=0; i<this.w.length; i++) {
		w_grad.push(Matrix.Zero(this.w[i].rows(), this.w[i].cols()));
	}

	// forward propagate
	for (var i=0; i<this.w.length; i++) {
		ones = add_s(Matrix.Zero(X.dimensions().rows, 1), 1);
		a = ones.augment(a);
		A.push(a);
		z = a.multiply(this.w[i].transpose());
		a = this.sigmoid(z);
		if (this.regression && i == this.w.length-1) {
			a = z;
		}
		this.acts.push(a);
	}
	if (predict) { return a; }

	// backpropagate
	delta = a.subtract(Y);
	w_grad[w_grad.length-1] = w_grad[w_grad.length-1].add(delta.transpose().x(A[A.length-1]));
	for (var i=this.w.length-1; i>0; i--) {
		delta = (i != this.w.length-1) ? delta.minor(1,2,delta.rows(),delta.cols()-1) : delta
		delta = ewise_mult(delta.x(this.w[i]), this.s_prime(A[i]));
		w_grad[i-1] = w_grad[i-1].add(delta.minor(1,2,delta.rows(),delta.cols()-1).transpose().x(A[i-1]));
	}
	
	for (var i=0; i<this.w.length; i++) {
		w_grad[i] = w_grad[i].x(1/X.rows());
		// w_grad[i] = this.lambda   ///   regularization
	}
	
	return w_grad;
}

NN.prototype.cost = function(X, Y) {
	this.err = 0;
	m = X.rows();
	h = this.fit(X, Y, true);
	if (this.regression) {
		this.err += (1.0/(2*m))*msum(mpow(Y.add(h.x(-1)), 2));
	} else {
		this.err += (1.0/m)*msum(ewise_mult(Y.x(-1),mlog(h)).add(
							ewise_mult(add_s(Y.x(-1),1),mlog(add_s(h.x(-1),1))).x(-1)));
	}
	//for (var i=0; i<this.w.length; i++) {
	//	this.err += msum(mpow(this.w[i],2).x(this.lambda/(2*m)));
	//}
}

NN.prototype.run = function(X, Y, batch_size, iters) {
	//this.cost(X, Y, false);
	//cost_list = [this.err];
	//console.log("Initial Cost:", this.err);
	
	for (var i=0; i<iters; i++) {

		//set batch indicies
		ind = (batch_size * i) % X.rows() + 1;
		
		// initialize batches
		X_b = X.minor(ind,1,batch_size,X.cols());
		Y_b = Y.minor(ind,1,batch_size,Y.cols());

		grad = this.fit(X_b, Y_b, false)
		for (var j=0; j<this.w.length; j++) {
			this.w[j] = this.w[j].add(grad[j].x(this._alpha).x(-1));
		}
	}
}

////////

function add_s(m, s) {
	r = m.map(function(x) { return x+s; });
	return r;
}

function ewise_mult(m1, m2) {
	r = m1.map(function(x,i,j) { return x * m2.e(i,j); });
	return r;
}

function mlog(z) {
	r = z.map(function(x) { return Math.log(x); });
	return r;
}

function msum(m) {
	total = 0;
	m.map(function(x) { total += x; });
	return total;
}

function mpow(m, p) {
	r = m.map(function(x) { return Math.pow(x,p); });
	return r;
}

////////

//xor data
X = Matrix.create([[0,0],[0,1],[1,0],[1,1]]);
y = Matrix.create([[0],[1],[1],[0]]);

//X = Matrix.create([[1,0,1,0],[1,0,0,1],[1,1,0,1],[0,1,0,0],[0,0,1,0]]);
//y = Matrix.create([[1],[1],[1],[0],[0]]);
//p = Matrix.create([[1,0,0,0]]);

// visualnet.js

layers     = [X.cols(),5,y.cols()];
epsilon    = 1.0;
lambda     = 0.1;
_alpha     = 1.0;
batch_size = X.rows();
iters      = 10;
regression = false;

neural = new NN(layers, epsilon, lambda, _alpha, regression);
diameter = 90;
count = 0

function setup() {
  cnv = createCanvas(770,575);
  cnv.parent("holder");
  //noLoop();
  clrs = [
    [
      [209,228,241],
      [247,240,10],
      [0,0,0]
    ]
  ];

  clr = clrs[Math.floor(Math.random()*clrs.length)]
  
  // create activation options
  for (var i=0; i<X.rows(); i++) {
    opt = document.createElement("OPTION");
    opt.innerHTML = X.row(i+1).inspect();
    d_act = document.getElementById("act");
    d_act.appendChild(opt);
  }
  update_doc();
}

function draw() {
  background(255);
  neural.run(X,y,batch_size,iters);
  act = d_act.selectedIndex+1;

  /*fill(0);
  strokeWeight(0);
  textFont("Space Mono");
  textStyle(NORMAL);
  textSize(13);
  fill(0,0,0);
  text("Positive Weights", 785, 224);
  text("Negative Weights", 785, 274);

  fill(clr[0][0],clr[0][1],clr[0][2]);
  rect(755,215,20,8);
  fill(clr[1][0],clr[1][1],clr[1][2])
  rect(755,265,20,8);*/

  //for (var n=0; n<8; n++) {
    //var nodes = m_nodes[n];
    //act = (act%8)+1;
    //nodes = create_network((n%4)*315,Math.round(n/8)*260,360,300,layers,true,act);
    nodes = create_network(0,0,750,550,layers,true,act);
    for (var i=0; i<nodes.length; i++) {
      for (var j=0; j<nodes[i].length; j++) {
        if (i != nodes.length-1) {
          for(var k=0; k<nodes[i+1].length; k++) {
            w_temp = neural.w[i].minor(1,2,neural.w[i].rows(),
                               neural.w[i].cols()-1);
            weight = w_temp.e(k+1,j+1);
            if (weight>=0) { 
              stroke(clr[0][0],clr[0][1],clr[0][2]); 
            } else { 
              stroke(clr[1][0],clr[1][1],clr[1][2]);
              weight *= -1;
            }
            strokeWeight(Math.pow(weight*2,1));
            line(nodes[i][j].pos.x,nodes[i][j].pos.y,
               nodes[i+1][k].pos.x,nodes[i+1][k].pos.y);
          }
        }
          // display mouse hover
        var distance = dist(mouseX, mouseY, nodes[i][j].pos.x, nodes[i][j].pos.y);
        if (distance <= diameter/2) {
          fill(0,0,0);
          strokeWeight(0);
          textFont("Akkurat");
          textSize(15);
          textStyle(NORMAL);
          var val = (i == 0) ? X.e(act,j+1) : neural.acts[i-1].e(act,j+1)
          text(Math.round(val*10000)/10000, nodes[i][j].pos.x+((diameter/2)-
            Math.abs(mouseY-nodes[i][j].pos.y))+diameter/6, mouseY,40,20);
        }
      }
    }
  create_network(0,0,0,0,layers,false,act);
  //}

  
  if (count % 10 === 0) {
    loss = document.getElementById("loss");
    neural.cost(X,y,this.regression);
    loss.innerHTML = "<b>Loss:</b> " + Math.round(neural.err*10000)/10000;

    dcount = document.getElementById("dcount");
    dcount.innerHTML = "<b>Iterations:</b> " + count*iters;
    
    //guess = neural.fit(p,y,true).e(1,1);
  }
  if (count%250 == 0) { reset(); }
  count++;
}

function node(x,y) {
  this.pos = createVector(x,y);
}

node.prototype.draw_node = function(i,j,act) {
  stroke(255);
  strokeWeight(2.5);
  fill(clr[2][0],clr[2][1],clr[2][2]);
  ellipse(this.pos.x,this.pos.y,diameter);
  fill(255);
  if (i !== 0) {
    ellipse(this.pos.x,this.pos.y,neural.acts[i-1].e(act,j+1)*(diameter-20)+6);
  } else {
    ellipse(this.pos.x, this.pos.y, X.e(act, j+1)*(diameter-20)+6);
  }
  
  if (i == layers.length-1) {
    noFill();
    strokeWeight(2);
    stroke(clr[0][0],clr[0][1],clr[0][2]);
    ellipse(this.pos.x,this.pos.y,(y.e(act,j+1))*(diameter-20)+10);
  }
}

function create_network(sx,sy,w,h,layers,init,act) {
  if (init) {
    w_pad = -20;
    w_space = (w-2*w_pad) / layers.length;
    nodes = [];
  }
  for (var i=0; i<layers.length; i++) {
    temp_nodes = [];
    h_pad = 0;
    if (init) {
      if ((h/(layers[i]+1)) <= (diameter/2)) {
        h_pad = diameter/2 - h/(layers[i]+1);
      }
      h_space = (h-2*h_pad);
    }
    for (var j=0; j<layers[i]; j++) {
      if (init) {
        temp = new node(w_pad+(w_space/2)+w_space*i,h_pad+((h_space/(layers[i]+1))*(j+1)));
        temp.pos.x += sx;
        temp.pos.y += sy;
        temp_nodes.push(temp);
      }
      if (!init) {
        nodes[i][j].draw_node(i,j,act);
      }
    }
    if (init) { nodes.push(temp_nodes); }
  }
  return nodes;
}

function reset() {
  layers     = document.getElementById("layers").value.split(",").map(Number);
  epsilon    = document.getElementById("epsilon").value.split(" ").map(Number);
  _alpha     = document.getElementById("alpha").value.split(" ").map(Number);
  batch_size = document.getElementById("batch").value.split(" ").map(Number);
  iters      = document.getElementById("iters").value.split(" ").map(Number);
  
  layers[0] = X.cols();
  layers[layers.length-1] = y.cols();
  update_doc();
  neural = new NN(layers, epsilon, lambda, _alpha, regression);
  count = 0;
}

function update_doc() {
  document.getElementById("layers").value = layers;
  document.getElementById("epsilon").value = epsilon;
  document.getElementById("alpha").value = _alpha;
  document.getElementById("batch").value = batch_size;
  document.getElementById("iters").value = iters;
}

function add_data() {
  new_input = document.createElement("input");
  new_input.type = "text";
  data = document.getElementById("data");
  data.appendChild(new_input);
}