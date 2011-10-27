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
  var hash = window.location.hash.substr(1);
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

  console.log('Belay callback ready');
  onBelayReady(function() {
    console.log('Belay is ready');
    var createCap = capServer.restore(hash);
    console.log('createCap is: ', createCap);
    createCap.post({},
      function(launchInfo) {
        belayBrowser.becomeInstance.post(launchInfo);
      },
      function(fail) {
        error('You may have reached this page in error.');
      });
  });

});

