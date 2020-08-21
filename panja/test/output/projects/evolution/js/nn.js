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
    //  this.err += msum(mpow(this.w[i],2).x(this.lambda/(2*m)));
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

//neural = new NN([2,3,1], 1.0, 0.1, 1.0);

//xor data
X = Matrix.create([[0,0],[0,1],[1,0],[1,1]]);
y = Matrix.create([[0],[1],[1],[0]]);

//X = Matrix.create([[1,1,1,1,1],[2,2,2,2,2],[3,3,3,3,3],[4,4,4,4,4],[5,5,5,5,5],[6,6,6,6,6],[7,7,7,7,7],[8,8,8,8,8]]);
//X = X.x(1/8);
//y = Matrix.create([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]);
//y = X;
//neural = new NN([2,3,1], 1.0, 0.1, 1.0);
/*for (var i=0; i<10000; i++) {
    neural.run(X,y,4,1);
    console.log(i);
}*/