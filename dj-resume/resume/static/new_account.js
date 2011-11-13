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
    var left = $('.left-part');
    left.append(frame);
  }

  // Snag the fragment off before initializing Belay
  var hash = window.location.hash.substr(1);
  window.location.hash = "";

  var tempServer = new CapServer();
  var emailAndCreate = tempServer.restore(hash);
  emailAndCreate.get(function(eAndC) {
    window.belay.belayInit(makeBelayFrame, addFrame, eAndC.email, true);

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
    onBelayReady(function(readyBundle) {
      var belayBrowser = readyBundle.belayBrowser;
      console.log('Belay is ready');
      var createCap = eAndC.create;
      console.log('createCap is: ', createCap);
      createCap.post({},
        function(launchInfo) {
          console.log("LaunchInfo is: ", launchInfo);
          belayBrowser.becomeInstance.post(launchInfo);
        },
        function(fail) {
          error('You may have reached this page in error.');
        });
    });
  });
});

