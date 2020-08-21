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
	cnv = createCanvas(800,575);
	cnv.parent("holder");
	//noLoop();
	clrs = [
		/*[
			[209,228,241],
			[255,252,1],
			[0,0,0]
		],*/
		[
			[255,0,0],
			[0,0,255],
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
	  nodes = create_network(0,10,750,550,layers,true,act);
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
		w_pad = 40;
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
