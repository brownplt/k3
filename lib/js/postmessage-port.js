var makePostMessagePort = (function() {
  // target: Window object to send to (can be undefined and set later)
  // portName: Shared name that windows use to connect
  // url (optional): Base URL to append fragments to for ie7
  function create(target, portName, url) {
    var handler = {
      postMessage: function(data) {
        var to_send = {
          target: target,
          type: portName,
          data: data,
          success: function() { console.log("sending success: ", data); },
          error: function(err) { console.log("sending failure: ", [data, err]); }
        };
        if (typeof url === 'string') to_send.url = url;
        $.pm(to_send);
      },
      // onmessage is set by the client
      onmessage: null,
      setTarget: function(newTarget) { target = newTarget; }
    };
    $.pm.bind(portName, function(data) {
        handler.onmessage({
          data: data,
          ports: []
        });
    });
    return handler;
  };
  return Object.freeze(create);
})();
