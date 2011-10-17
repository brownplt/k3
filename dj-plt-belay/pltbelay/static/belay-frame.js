$(function() {
  var stationInfo;
  var clientLocation;
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

  var sessionID, checkLogin;
  var matchInfo = COMMON.sessionRegExp.exec(document.cookie);
  if (matchInfo !== null) {
    sessionID = matchInfo[1];
    checkLogin = capServer.restore(COMMON.urlPrefix + '/check_login/');
    checkLogin.post(
      { sessionID : sessionID },
      function(response) {
        if(response.loggedIn) {
          console.log('Logged in');
          get_station(function(station) {
            capServer.restore(station).get(function(station_info) {
              stationInfo = station;
              if(clientLocation) go();
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

  $(window).bind('message', function(e) {
    $(window).unbind('message');
    clientLocation = e.originalEvent.data.clientLocation;
    if(!clientLocation) {
      console.log("Unexpected message from client: ", e);
      return;
    }
    if(stationInfo) go();
  });

  function go() {
    var port = makePostMessagePort(window.parent, "belay");
    var tunnel = new CapTunnel(port);
    capServer.setResolver(function(instanceID) {
      if(instanceID !== this.instanceID) {
        return tunnel.sendInterface;
      }
    });
    tunnel.setLocalResolver(function() { return capServer.publicInterface; });
    tunnel.sendOutpost(capServer.dataPreProcess({
      services: {
        becomeInstance: capServer.grant(function(launchInfo, sk, fk) {
          stationInfo.newInstance.post(launchInfo, function(launched) {
            capServer.restore('http://' + window.location.host + '/make-stash/').post(launchInfo.private_data,
              function(restoreCap, status, xhr) {
                var nav = launchInfo.domain +
                          launchInfo.url +
                          "#" +
                          encodeURI(restoreCap.serialize());
                console.log('Nav: ', nav);
                window.parent.location.href = nav;
              });
            sk('success');
          },
          function(err) {
            console.log('belay_frame: Failed to create new instance: ', err);
            fk('failed');
          });
        })
      }
    }));
  }
});

