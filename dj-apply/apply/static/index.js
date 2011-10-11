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

  capServer.setResolver(function(instanceID) {
    if(instanceID !== capServer.instanceID) {
      return tunnel.sendInterface;
    }
  });

  tunnel.setLocalResolver(function() { capServer.publicInterface; });

  var becomeInstance;
  var frame = makeBelayFrame();
  tunnel.setOutpostHandler(function(outpost) {
    port.setTarget(frame[0].contentWindow);  
    becomeNewInstance = capServer.dataPostProcess(outpost).becomeInstance;
    // TODO(joe): fix this up
    launchInfo = {
      domain: 'http://localhost:8001/',
      url: 'applicant/',
      private_data: 'hello from apply!'
    };
    becomeNewInstance.post(launchInfo, function(response) {
        // NOTE(joe): this shouldn't happen, because the belay-frame
        // will navigate the window to start the instance
        console.log('Got a response: ', response);
      },
      function(err) {
        console.log('Error: ', err);
      });
  });


  addFrame(frame);
});

