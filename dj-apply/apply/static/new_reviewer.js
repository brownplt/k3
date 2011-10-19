$(function() {
  var theFrame;
  function makeBelayFrame() {
    var frame = $('<iframe></iframe>');
    frame.attr({
      'src': COMMON.belayFrame,
      'name': 'belay'
    });
    frame.css({
      border: 'none',
      width: '40em',
      height: '20em',
      padding: '3em'
    });
    theFrame = frame;
    return frame;
  }
  function addFrame(frame) {
    var right = $('.right-part');
    right.append(frame);
  }

  // Snag the fragment off before initializing Belay
  var hash = window.location.hash;
  window.location.hash = "";

  window.belay.belayInit(makeBelayFrame, addFrame);

  function error(message) {
    var left = $('.left-part');
    var msg = $('<p>' + message + '</p>');
    console.log(message)
    msg.css({
      'font-size': 'larger',
      'color': 'red'
    });
    left.append(msg);
  }

  onBelayReady(function() {
    var createCap = capServer.restore(hash);
    createCap.post({},
      function(launchCap) {
        belayBrowser.becomeInstance.post({
          domain: COMMON.urlPrefix,
          url: '/static/reviewer.html',
          private_data: launchCap,
          public_data: 'Reviewer account'
        });
      },
      function(fail) {
        error('You may have reached this page in error.');
      });
  });

});

