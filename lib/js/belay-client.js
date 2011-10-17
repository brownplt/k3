var capServer;
var storage;
var launchInfo;
var belayBrowser;

var onBelayReady = (function() {
  var tunnel;
  var callbacks = [];
  var outpostReceived = false;

  window.belay.portReady = function() {
    console.log('Setting up port');
    tunnel = new CapTunnel(window.belay.port);
    tunnel.setOutpostHandler(function(data) {
      console.log('Setting up outpost: ', data);
      var setupData = (function() {
        var processedData = (new CapServer('radish')).dataPostProcess(data);
        return {
          instanceID: processedData.instanceID,
          snapshot: processedData.info ? processedData.info.snapshot : undefined
        };
      })();
      var instanceID = setupData.instanceID;
      var snapshot = setupData.snapshot;
      capServer = new CapServer(instanceID, snapshot);

      var resolver = function(instID) {
        return tunnel.sendInterface;
      };
      capServer.setResolver(resolver);

      tunnel.setLocalResolver(function(instID) {
        if (instID === instanceID) return capServer.publicInterface;
        else return null;
      });

      var outpostData = capServer.dataPostProcess(data);
      belay.outpost = outpostData;
      belayBrowser = outpostData.services;

      belay.dirty = function() {
        // Do nothing: should be replaced by instance if needed
      };

      capServer.setSyncNotifier(function() {
        belay.dirty();
      });

      storage = outpostData.storage;
      launchInfo = outpostData.info;

      outpostReceived = true;
      callbacks.forEach(function(f) { f(); });
      callbacks = null;
    });
  };

  return function(callback) {
    if (outpostReceived) { callback(); }
    else { callbacks.push(callback); }
  };
   
})();

