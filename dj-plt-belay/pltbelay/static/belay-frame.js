$(function() {
  var capServer = new CapServer(newUUIDv4());
  function get_station(k) {
    $.ajax('/get_station', {
      type: 'GET',
      success: function(data, status, xhr) {
        k(data);
      },
      error: function(data, status, xhr) {
        console.log('failed to get station');
      }
    });
  }

  $.ajax('/check_login/', {
    type: 'GET',
    success: function(data, status, xhr) {
      if(data === 'true') {
        $(document.body).append($("<div>Logged in</div>"));
        get_station(function(station) {
          console.log('Logged in: ', station);
          go(station);
        });
      } else {
      }
    },
    error: function(data, status, xhr) {
      console.log("Getting logged in status failed: ", {d: data, s: status});
    }
  });

  function go(station_url) {
    var port = makePostMessagePort(window.parent, "belay");
    var tunnel = new CapTunnel(port);
    capServer.setResolver(function(instanceID) {
      if(instanceID !== this.instanceID) {
        return tunnel.sendInterface;
      }
    });
    tunnel.setLocalResolver(function() { return capServer.publicInterface; });
    tunnel.sendOutpost(capServer.dataPreProcess({
      becomeInstance: capServer.grant(function(launchInfo) {
        console.log('launchInfo: ', launchInfo);
        return 'why hello to you to!';
        // TODO: becomeAnInstance
      })
    }));
  }
});
