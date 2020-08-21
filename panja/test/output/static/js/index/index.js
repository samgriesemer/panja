// redirect to about page if on mobile
if (screen.width <= 699) {
  document.location = "/about";
}

/* HAVE TO RUN ON SERVER (CAN BE LOCAL) IF WANT CSSRULES TO WORK */
function highlight_title(pos) {
  var link = document.querySelector('.title > a');
  setTimeout(function() {
    link.style.backgroundPosition = 'left';
    link.style.backgroundSize = '100% 100%';
  }, 600);
  setTimeout(function() {
    link.style.backgroundPosition = 'right';
    link.style.backgroundSize = '0% 100%';
  }, 1050);
  setTimeout(function() {
    link.style.backgroundPosition = 'left';
  }, 1600);
}

function get_rule(animation_name) {
  var ss = document.styleSheets;
  for (var i=0; i<ss.length; i++) {
    for (var j=0; j<ss[i].cssRules.length; j++) {
      rule = ss[i].cssRules[j];
      if (rule.name == animation_name) {
        console.log('found rule');
        return rule;
      }
    }
  }
  console.log('rule not found');
  return false;
}

function change_rule(rule, start, mid) {
  // built around 3 tick floating animation
  console.log(rule);
  rule.deleteRule('0');
  rule.deleteRule('1');
  rule.deleteRule('2');
  rule.appendRule('0% { transform: translate(0, 0px) rotate('+start+'deg); }');
  rule.appendRule('50% { transform: translate(0, 15px) rotate('+mid+'deg); }');
  rule.appendRule('100% { transform: translate(0, 0px) rotate('+start+'deg); }');
}

function update_page(pos,data) {
  // get necessary page elements
  let tag = document.querySelector('.tag');
  let links = document.querySelectorAll('a');
  let title = document.querySelector('.title > a');
  let h1_title = document.querySelector('.title');
  let description = document.querySelector('.description');
  let content = document.querySelector('.grid');
  let svg = document.querySelector('svg');
  let pagenum = document.querySelector('.pagenum');
  let floating_rule = get_rule('floating');

  // these style changes are animated by .text_fade css transition
  h1_title.style.transform = "translateY(-10px)";
  h1_title.style.opacity = 0;
  //tag.style.transform = "translateY(-10px)";
  //tag.style.opacity = 0;
  description.style.transform = "translateY(-10px)";
  description.style.opacity = 0;
  //svg.className.baseVal = 'fill_fade';

  // wait 1ms before rotating to allow for changed svg class
  //setTimeout(function() {
    //svg.style.transform = 'rotate('+pos*560+'deg)';
    //svg.style.transform = 'scale(4,4)';
  //}, 50);

  // wait 0.4s until opacity transition is completed, then change information so invisible to user
  setTimeout(function() {
    // update page numbers
    pagenum.innerHTML = data.pagenums[pos];

    // update tag style and content
    //tag.innerHTML = data.tags[pos];
    //tag.style.color = data.tag_colors[pos]

    // update link colors
    for (let link of links) {
      //link.style.color = data.text_colors[pos];
      //link.style.backgroundImage = 'linear-gradient(transparent 65%, {} 4px)'.replace('{}',data.underline_colors[pos]);
    }

    // update card title
    title.innerHTML = data.titles[pos];
    title.href = data.urls[pos];

    // change card description
    description.innerHTML = data.descriptions[pos];
    //description.style.color = data.description_colors[pos];

    // global grid ans svg styles
    //content.style.backgroundColor = data.backgrounds[pos];
    //svg.style.fill = data.svg_colors[pos];
  }, 500);

  // wait 0.2s longer than page change to animate text back down, will complete at 1.2s after scroll, highlight after 2.1s
  setTimeout(function() {
    // wait a little after fill change before setting these back
    //change_rule(floating_rule, 200, 197);
    //svg.className.baseVal = 'floating';

    // these style changes are animated by .text_fade css transition, restore back to defaults
    h1_title.style.transform = "translateY(0px)";
    h1_title.style.opacity = 100;
    //tag.style.transform = "translateY(0px)";
    //tag.style.opacity = 100;
    description.style.transform = "translateY(0px)";
    description.style.opacity = 100;
    highlight_title(pos); // delayed from now by 0.6s
  }, 700)
}

// wheel listener function
function wheel_curry(pos,data) {
  return function wheel(e) {

    // orignal wheel listener is removed upon being called, add one back after 1.6s (time of animations)
    setTimeout(function() {
      window.document.addEventListener('wheel', wheel_curry(pos,data), {capture: true, passive:true, once:true});
      console.log('wheel listener added');
    }, 1600);

    console.log('scroll detected');
    valid_scroll = false;

    if (e.deltaY < 0 && pos > 0) {
      console.log('scrolling up');
      pos -= 1;
      valid_scroll = true;
    }

    if (e.deltaY > 0 && pos < data.titles.length-1) {
      console.log('scrolling down');
      pos += 1;
      valid_scroll = true;
    }

    // a valid scroll occurs if there is a new page to load in the scrolled direction
    if (valid_scroll) {
      update_page(pos,data);
    }
  }
}

// initial page actions
window.onload = function() {
  // set current page position
  var pos = 0;

  // inital link highlight on page load (actually make it page load listener)
  highlight_title(pos);

  setTimeout(function() {
    window.document.addEventListener('wheel', wheel_curry(pos, card_data), {capture: true, passive:true, once:true});
    console.log('wheel listener added');
  }, 1600);
}
