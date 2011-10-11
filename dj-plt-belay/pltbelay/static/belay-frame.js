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
        console.log('Logged in');
        get_station(function(station) {
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
    var port = makePostMessagePort(window.parent, "belay");
    var tunnel = new CapTunnel(port);
    capServer.setResolver(function(instanceID) {
      if(instanceID !== this.instanceID) {
        return tunnel.sendInterface;
      }
    });
    tunnel.setLocalResolver(function() { return capServer.publicInterface; });
    tunnel.sendOutpost(capServer.dataPreProcess({
      becomeInstance: capServer.grant(function(launchInfo, sk, fk) {
        station_info.newInstance.post(launchInfo, function(launched) {
          // TODO(joe): navigate to launchInfo.domain + url
          sk('success');
        },
        function(err) {
          console.log('belay_frame: Failed to create new instance: ', err);
          fk('failed');
        });
      }),
      notifyLocation: capServer.grant(function(url) {
        // TODO: get fragment, load private_data
      })
    }));
  }
});
