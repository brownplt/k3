$(function() {
  var stashURL = COMMON.urlPrefix + '/make-stash/';
  var stationInfo;
  var clientLocation;
  var capServer = new CapServer(newUUIDv4());
  var stash = capServer.restore(stashURL);

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

  function notLoggedIn() {
    $('#login-frame').show();
  }


  var sessionID, checkLogin;
  var matchInfo = COMMON.sessionRegExp.exec(document.cookie);
  if (matchInfo === null) {
    notLoggedIn();
  }
  else {
    sessionID = matchInfo[1];
    checkLogin = capServer.restore(COMMON.urlPrefix + '/check_login/');
    console.log('Request to: ' + checkLogin.serialize());
    checkLogin.post(
      { sessionID : sessionID },
      function(response) {
        console.log('Got login response');
        if(response.loggedIn) {
          console.log('Logged in');
          get_station(function(station) {
            capServer.restore(station).get(function(station_info) {
              stationInfo = station_info;
              if(clientLocation) go();
            },
            function(err) {
              console.log('Couldn\'t get station info: ', err);
            });
          });
        }
        else { notLoggedIn(); }
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

  function launch(launchInfo) {
    console.log('Launching: ', launchInfo);
    stash.post({
      sessionID: sessionID,
      private_data: launchInfo.private_data
    },
    function(restoreCap) {
      var nav = launchInfo.domain +
                launchInfo.url +
                "#" +
                encodeURI(restoreCap.serialize());
      console.log('Nav: ', nav);
      window.parent.location.href = nav;
    },
    function(err) { 
      console.log('Make-stash failed: ', err);
    });
  }


  function instanceChoice(instanceInfos) {
    var accountsDiv = $('#account-frame');
    console.log('choicing: ', instanceInfos);
    accountsDiv.show();
    instanceInfos.forEach(function(instance) {
      instance.get(function(instanceInfo) {
        var elt = $('<button></button>');
        if(typeof instanceInfo.public_data === 'string') {
          elt.html(instanceInfo.public_data);
        }
        else { return; } // Don't show the relationship
        console.log('Appending: ', elt);
        accountsDiv.append(elt);
        elt.click(function() {
          launch(instanceInfo);
        });
      });
    });
  }

  function go() {
    var port = makePostMessagePort(window.parent, "belay");
    var tunnel = new CapTunnel(port);
    capServer.setResolver(function(instanceID) {
      if(instanceID !== this.instanceID) {
        return tunnel.sendInterface;
      }
    });
    tunnel.setLocalResolver(function() { return capServer.publicInterface; });
    console.log('StationInfo: ', stationInfo);

    stationInfo.instances.get(function(instanceInfos) {
      console.log(instanceInfos);
      if(instanceInfos.length > 0) {
        instanceChoice(instanceInfos);
      }
    });

    tunnel.sendOutpost(capServer.dataPreProcess({
      services: {
        becomeInstance: capServer.grant(function(launchInfo, sk, fk) {
          stationInfo.newInstance.post(launchInfo, function(launched) {
            launch(launchInfo);
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

