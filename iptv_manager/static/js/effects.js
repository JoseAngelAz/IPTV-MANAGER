// effects.js — pixel sparkle trail
(function(){
  'use strict';

  var POOL_SIZE = 40;
  var THROTTLE_MS = 60;
  var pool = [];
  var idx = 0;
  var last = 0;

  function getSparkle(){
    var el = pool[idx];
    if(!el){
      el = document.createElement('div');
      el.className = 'sparkle-particle';
      el.style.cssText = 'position:fixed;width:4px;height:4px;border-radius:50%;pointer-events:none;z-index:9999;opacity:0;will-change:transform,opacity;';
      document.body.appendChild(el);
      pool[idx] = el;
    }
    idx = (idx + 1) % POOL_SIZE;
    return el;
  }

  function emit(x, y){
    var now = Date.now();
    if(now - last < THROTTLE_MS) return;
    last = now;

    var el = getSparkle();
    var colors = ['#fbbf24','#60a5fa','#a78bfa','#f472b6','#34d399'];
    var color = colors[Math.floor(Math.random() * colors.length)];
    var size = 3 + Math.random() * 3;
    var dx = (Math.random() - 0.5) * 20;
    var dy = -Math.random() * 20 - 5;

    el.style.cssText = 'position:fixed;left:' + (x - size/2) + 'px;top:' + (y - size/2) + 'px;width:' + size + 'px;height:' + size + 'px;border-radius:50%;pointer-events:none;z-index:9999;background:' + color + ';box-shadow:0 0 4px ' + color + ';animation:sparkle-fly 0.6s ease-out forwards;will-change:transform,opacity;';

    el.style.setProperty('--dx', dx);
    el.style.setProperty('--dy', dy);
  }

  function onMove(e){
    var x, y;
    if(e.touches){
      x = e.touches[0].clientX;
      y = e.touches[0].clientY;
    } else {
      x = e.clientX;
      y = e.clientY;
    }
    emit(x, y);
  }

  document.addEventListener('mousemove', onMove, {passive: true});
  document.addEventListener('touchmove', onMove, {passive: true});

  var style = document.createElement('style');
  style.textContent = '@keyframes sparkle-fly{0%{opacity:1;transform:translate(0,0) scale(1)}100%{opacity:0;transform:translate(var(--dx,0),var(--dy,0)) scale(0)}}';
  document.head.appendChild(style);
})();
