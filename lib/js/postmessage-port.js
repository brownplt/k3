var makePostMessagePort = (function() {
  // target: Window object to send to
  // portName: Shared name that windows use to connect
  // url (optional): Base URL to append fragments to for ie7
  function create(target, portName, url) {
    var handler = {
      postMessage: function(data) {
        var to_send = {
          target: target,
          type: portName,
          data: data
        };
        if (typeof url === 'string') to_send.url = url;
        $.pm(to_send);
      },
      // onmessage is set by the client
      onmessage: null
    };
    $.pm.bind({
      type: portName,
      fn: function(data) {
        handler.onmessage({
          data: data,
          ports: []
        });
      }
    });
    return handler;
  };
  return Object.freeze(create);
})();
