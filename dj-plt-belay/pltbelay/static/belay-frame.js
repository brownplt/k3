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

  $.ajax('/check_login', {
    type: 'GET',
    success: function(data, status, xhr) {
      if(data === 'true') {
        $(document.body).append($("<div>Logged in</div>"));
        get_station(function(station) {
          $(document.body).append($("<div>" + station + "</div>"));
          go(station_url);
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
    tunnel.sendOutpost({
      becomeInstance: capServer.grant(function(launchInfo) {
        // TODO: becomeAnInstance
      });
    });
  }
});
