function update(el=null, d=null, type='a') {

  if (type == 'm') {
    body = {'action':d.idx, 'action_type':'m'};
  } else if (type == 'a') {
    body = {'action_type':'a'};
  }

  // make post request
  console.time('post');
  console.log(JSON.stringify(body))
  var url = 'https://api.smgr.io/engine/rl/monte_carlo/update';
  fetch(url, {
    method: 'POST',
    body: JSON.stringify(body),
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    console.timeEnd('post');
    if (response.status == 400) {
      response.json().then(data => {
        throw new Error(data.message);
        d3.select('#note').text(data.message);
      });
    } else {
      d3.select('#note').text("");
      return response.json().then(data => {
        // get data
        console.log(data);
        children = data['children'];
        winner = data['winner'];
        state = data['state'];

        if (winner === 0 || winner === 1) {
          d3.select('#note').text('Winner is player #' + winner);
        }

        black = state[0];
        red   = state[1];
        render_board(black,red,d);

        /*for (var i=0; i<children.length; i++) {
          c = children[i];
          black = c.state[0];
          red   = c.state[1];
          render_board(black, red, d);
        }*/

        if (type == 'm') {
          update()
        }
      });
    }
  });
}

function render_board(black, red, d) {
  for (var i=0; i<rows; i++) {
    for (var j=0; j<cols; j++) {
      if (black[i][j]==1) {
        d3.selectAll('.cell')
          .filter(function(e) {
            return e.idx[0]==i && e.idx[1]==j;
          })
          .style('fill','black')
      } else if (red[i][j]==1) {
        d3.selectAll('.cell')
          .filter(function(e) {
            return e.idx[0]==i && e.idx[1]==j;
          })
          .style('fill','blue')
      }
    }
  }
}
