window.addEventListener('load', function() {
  function makeBelayFrame() {
    var frame = $('<iframe></iframe>');
    frame.attr({
      'src': 'http://localhost:8000/static/belay-frame.html',
      'name': 'belay'
    });
    frame.css({
      border: 'none',
      width: '40em',
      height: '20em',
      padding: '3em'
    });
    return frame;
  }
  function addFrame(frame) {
    var right = $('.right-part');
    right.append(frame);
  }

  var capServer = new CapServer(newUUIDv4());
  var port = makePostMessagePort(null, "belay");
  var tunnel = new CapTunnel(port);
  tunnel.setLocalResolver(capServer
  var becomeInstance;
  port.setOutpostHandler(function(data) {
    var belayWindow = window.frames["belay"];
    port.setTarget(belayWindow);
    becomeInstance = capServer.restore(data.becomeInstance);
    showAccountChoice();
  });

  var frame = makeBelayFrame();
  addFrame(frame);
});
