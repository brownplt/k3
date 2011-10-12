$(function() {
  var capServer = new CapServer(newUUIDv4());
  var re = /.*session=([\-0-9a-zA-Z]+).*/;
  var urlPrefix = window.location.protocol + '//' + window.location.host;

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

  var sessionID, checkLogin;
  var matchInfo = re.exec(document.cookie);
  if (matchInfo !== null) {
    sessionID = matchInfo[1];
    checkLogin = capServer.restore(urlPrefix + '/check_login/');
    checkLogin.post(
      { sessionID : sessionID },
      function(response) {
        if(response.loggedIn) {
          console.log('Logged in');
          get_station(function(station) {
            capServer.restore(station).get(function(station_info) {
              go(station_info);
            },
            function(err) {
              console.log('Couldn\'t get station info: ', err);
            });
          });
        } 
      },
      function(response) {
        console.log("Getting logged in status failed: ", {r : response});
      }
    );
  }

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
          capServer.restore('http://' + window.location.host + '/make-stash/').post(launchInfo.private_data,
            function(restoreCap, status, xhr) {
              var nav = launchInfo.domain +
                        launchInfo.url +
                        "#" +
                        encodeURI(restoreCap.serialize());
              console.log('Nav: ', nav);
//              window.parent.location.href = nav;
            });
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
