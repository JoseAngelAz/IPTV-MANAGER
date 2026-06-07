// cdn-fallback.js — Load local vendor files when CDN fails
(function(){
  'use strict';

  var fallbacks = [
    {
      test: function(){ return typeof window.FontAwesome === 'undefined'; },
      urls: ['/static/vendor/fontawesome/css/all.min.css'],
      type: 'css'
    },
    {
      test: function(){ return typeof window.Chart === 'undefined'; },
      urls: ['/static/vendor/chart.js/dist/chart.umd.min.js'],
      type: 'js'
    },
    {
      test: function(){ return typeof window.html2canvas === 'undefined'; },
      urls: ['/static/vendor/html2canvas/dist/html2canvas.min.js'],
      type: 'js'
    },
    {
      test: function(){ return typeof window.htmx === 'undefined'; },
      urls: ['/static/vendor/htmx.org/dist/htmx.min.js'],
      type: 'js'
    },
    {
      test: function(){ return typeof window.Cropper === 'undefined'; },
      urls: ['/static/vendor/cropperjs/dist/cropper.min.js', '/static/vendor/cropperjs/dist/cropper.min.css'],
      type: 'auto'
    }
  ];

  function loadFallback(fb){
    fb.urls.forEach(function(url){
      if(fb.type === 'css' || fb.type === 'auto' && url.endsWith('.css')){
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        document.head.appendChild(link);
      } else {
        var script = document.createElement('script');
        script.src = url;
        script.defer = true;
        document.body.appendChild(script);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    fallbacks.forEach(function(fb){
      try {
        if(fb.test()) loadFallback(fb);
      } catch(e) {
        loadFallback(fb);
      }
    });
  });
})();
