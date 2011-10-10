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
          capServer.restore(station).get(function(station_info) {
            go(station_info);
          },
          function(err) {
            console.log('Couldn\'t get station info: ', err);
          });
        });
      } else {
      }
    },
    error: function(data, status, xhr) {
      console.log("Getting logged in status failed: ", {d: data, s: status});
    }
  });

  function go(station_info) {
    console.log('station_info: ', station_info);
    var port = makePostMessagePort(window.parent, "belay");
    var tunnel = new CapTunnel(port);
    capServer.setResolver(function(instanceID) {
      if(instanceID !== this.instanceID) {
        return tunnel.sendInterface;
      }
    });
    tunnel.setLocalResolver(function() { return capServer.publicInterface; });
    tunnel.sendOutpost(capServer.dataPreProcess({
      becomeNewInstance: capServer.grant(function(launchInfo) {
        console.log('launchInfo: ', launchInfo);
        return 'why hello to you to!';
        // TODO: becomeAnInstance
      }),
      notifyLocation: capServer.grant(function(url) {
        // TODO: get fragment, load private_data
      })
    }));
  }
});
