function time_parser() {
  let months = [ 'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  let days =   ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']

  let d = new Date();
  let t = d.toLocaleTimeString();
  t = t.slice(0,-2);
  let dt = d.toLocaleDateString();
  let el_time = document.querySelector('#time-content');
  let el_date = document.querySelector('#date-content');
  let day = days[d.getDay()];
  let month = months[d.getMonth()];
  el_time.innerHTML = t;
  el_date.innerHTML = day+', '+month+'. '+d.getDate()+', '+d.getFullYear();
  el_date.innerHTML += '<br>'+dt;

  setTimeout(time_parser, 250);
}

function weather_parser(data) {
  console.log('Weather packet: ', data);
  let cur = data[0]
  let temp = document.querySelector('#weather-temp');
  let aptemp = document.querySelector('#weather-aptemp');
  let summary = document.querySelector('#weather-summary');
  let precip = document.querySelector('#weather-precip');

  temp.innerHTML = Math.round(cur.temperature)+'&deg;';
  aptemp.innerHTML = Math.round(cur.apparent_temperature)+'&deg;';
  summary.innerHTML = cur.summary;

  if (cur.precip_type != null) {
    precip.innerHTML = cur.precip_probability*100+'% chance of '+cur.precip_type;
  } else {
    precip.innerHTML = '0% chance of precipitation'
  }
}

function news_parser(data) {
  console.log('News packet: ', data);
  let news = document.querySelector('#news-content');

  // clear news articles if present
  while (news.firstChild) {
    news.removeChild(news.firstChild);
  }

  let ul = document.createElement("ul");
  for (var i=0; i<5; i++) {
    li = document.createElement("li");
    li.className = 'article'+i;
    li.innerHTML = data[i].title;
    li.innerHTML += ' (<a href=' + data[i].url + '>link</a>)';
    ul.appendChild(li);
  }
  news.appendChild(ul);
}

function crypto_parser() {
  let data = {};
  let chart = {};
  let promises = [];
  let assets = ['BTC', 'ETH']
  let base_url = 'https://api.smgr.io/stream/crypto/{}/120';

  for (let asset of assets) {
    let url = base_url.replace('{}', asset);
    let promise = get(url);
    promises.push(promise);
    promise.then(result => {
      data[asset] = result[0];
      chart[asset] = result.map(x => ({'time':x.query_time, 'price':x.price}));
    });
  }

  Promise.all(promises).then(() => {
    console.log('Crypto packet: ', data);
    let eth_price = document.querySelector('#crypto-eth-price');
    let eth_change = document.querySelector('#crypto-eth-change');
    eth_price.innerHTML = '$'+data['ETH']['price'].toFixed(2);
    eth_change.innerHTML = '$'+data['ETH']['change_24h'].toFixed(2);

    let btc_price = document.querySelector('#crypto-btc-price');
    let btc_change = document.querySelector('#crypto-btc-change');
    btc_price.innerHTML = '$'+data['BTC']['price'].toFixed(2);
    btc_change.innerHTML = '$'+data['BTC']['change_24h'].toFixed(2);

    update_chart(chart);
  })

  setTimeout(crypto_parser, 1*1000);
}

function stock_parser() {
  let data = {};
  let chart = {};
  let promises = [];
  let assets = ['AAPL']
  let base_url = 'https://api.smgr.io/stream/stocks_realtime/{}/120';

  for (let asset of assets) {
    let url = base_url.replace('{}', asset);
    let promise = get(url);
    promises.push(promise);
    promise.then(result => {
      data[asset] = result[0];
      chart[asset] = result.map(x => ({'time':x.query_time, 'price':x.last_sale_price}));
    });
  }

  Promise.all(promises).then(() => {
    console.log('Stock packet: ', data);
    let aapl_price = document.querySelector('#stocks-aapl-price');
    let aapl_change = document.querySelector('#stocks-aapl-change');
    eth_price.innerHTML = '$'+data['ETH']['price'].toFixed(2);
    eth_change.innerHTML = '$'+data['ETH']['change_24h'].toFixed(2);

    update_chart(chart);
  })

  setTimeout(crypto_parser, 1*1000);
}

function get(url) {
  return fetch(url, {
    method:'GET',
    //credentials: 'include' // to include cookies across domains
  }).then(response => {
    return Promise.all([response, response.json()]);
  }).then(([response, body]) => {
    if (response.ok) {
      return body;
    }
    if (body.message != null) {
      throw Error(body.message);
    } else {
      throw Error(response.statusText);
    }
  }).then(data => {
    return data;
  }).catch(error => {
    return error.message;
  });
}

function scheduler(url, callback, interval) {
  get(url).then(data => callback(data));
  setTimeout(function() { 
    return scheduler(url, callback, interval); 
  }, interval);
}

function countdown(el, n) {
  var interval = setInterval(function() {
    el.innerHTML = n;
    if (n == 0) {
      clearInterval(interval);
    } else {
      n -= 1;
    }
  }, 1000)
}

let weather_url = 'https://api.smgr.io/stream/weather/5';
scheduler(weather_url, weather_parser, 60*1000);

let news_url = 'https://api.smgr.io/stream/news/5';
scheduler(news_url, news_parser, 3*60*1000);

//scheduler(crypto_url, crypto_parser, 3*60*1000);

// initialize cells
time_parser();
crypto_parser();
