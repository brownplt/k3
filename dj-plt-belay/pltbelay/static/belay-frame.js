$(function() {
  var stashURL = COMMON.urlPrefix + '/make-stash/';
  var stationInfo;
  var clientLocation;
  var capServer = new CapServer(newUUIDv4());
  var stash = capServer.restore(stashURL);

  function get_station(k) {
    $.ajax('/get_station/', {
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

  $('#createplt').click(function() {
    $('#login-frame').hide();
    $('#account-frame').hide();
    $('#create-account').show();
  });

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
              go();
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

  $.pm.bind('init', function(data) {
    console.log(data);
    clientLocation = data.clientLocation;
    console.log('Client location is: ', clientLocation);
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

  $('#submit').click(function(e) {
    var uname = $('#username').val();
    var password1 = $('#password1').val();
    var password2 = $('#password2').val();

    if(password1 !== password2) {
      alert("Passwords did not agree.");
      return;
    }

    if (!COMMON.validateLoginInfo(uname, password1)) {
      if(uname.length > 20) {
        alert("We require usernames to be less than 20 characters.");
        return;
      }
      if(password1.length < 8) {
        alert("Please use at least 8 characters for your password.");
        return;
      }
      alert("Invalid username or password");
      return;
    }
    
    function failure() {
      alert("Something went wrong with your request." +
            "Please contact the site administrator " + 
            "(link at the bottom of the page).")
    }

    function create() {
      console.log("Creating account");
      var createAccount = capServer.restore(COMMON.urlPrefix + '/create_plt_account/');
      createAccount.post(
        { username : uname, password : password1 }, 
        function(response) {
          window.location = COMMON.urlPrefix + response.redirectTo;
        },
        failure
      );
    }

    var checkUname = capServer.restore(COMMON.urlPrefix + '/check_uname/');
    checkUname.post(
      { username : uname },
      function(response) {
        if (response.available) { create(); }
        else { alert("That username is taken, please try another."); }
      },
      failure
    );

  });

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
    // TODO(joe): need to make sure we have a reasonable clientLocation
    // if we're going to launch here.
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

    var stashser, stashcap;
    // NOTE(joe): We're only using stashes that point to the Belay server,
    // which this check is ensuring.
    if (typeof clientLocation === 'object' &&
        typeof clientLocation.hash === 'string' &&
        clientLocation.hash.indexOf(COMMON.urlPrefix) !== -1) {
      stashser = clientLocation.hash.substr(1);
      stashcap = capServer.restore(stashser);
      launchInstance(stashcap);
    }
    else {
      launchNonInstance();
    }

    function launchInstance(stashcap) {
      stashcap.post({ sessionID: sessionID },
        function(stashed) {
          tunnel.sendOutpost(capServer.dataPreProcess({
            services: {},
            launchInfo: stashed
          }));
        },
        function(fail) {
          console.log('Getting stashed value failed: ', fail);
        });
    }

    function launchNonInstance() {
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
  }
});

