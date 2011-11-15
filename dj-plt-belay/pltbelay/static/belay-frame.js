if(false)
window.console = {
  log: function(str) {
    var rest = "";
    for(var i = 1; i < arguments.length; i++) {
      rest += arguments[i] + ", ";
    }
    $(document.body).append('<p>' + str + ' '  + rest + '</p>');
  }
};

$(function() {
  console.log("Cookie: " + document.cookie);
  var stationInfo;
  var clientLocation, clientEmail;
  var clientkey = null;
  var loginEmail;
  var sessionToken;
  var capServer = new CapServer(newUUIDv4());

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

  function hideAll() {
    $('#login-frame').hide();
    $('#plt-login-frame').hide();
    $('#account-frame').hide();
    $('#create-account').hide();
    $('#nobody').hide();
  }

  $('#backtomain').click(function(e) {
    hideAll();
    $('#plt-login-frame').fadeIn();
    $('#login-frame').fadeIn();
  });

  $('#loginplt').click(function(e) {
    hideAll();
    $('#plt-login-frame').show();
  });

  $("#plt-submit").click(function(e) {
    var username = $("#username-login").val();
    var password = $("#password-login").val();

    function login() {
      if (!COMMON.validateLoginInfo(username, password)) {
        alert('Invalid username/password');
        return;
      }

      var pltLogin = capServer.restore(COMMON.urlPrefix + '/plt_login/');
      pltLogin.post(
        { username : username, password : password },
        function(loginInfo) {
          loginInfo.email = username;
          handleLoginInfo(loginInfo);
        },
        function(err) {
          console.log('PLT login failed: ', err);
        }
      );
    }

    login();
  });

  $('#createplt').click(function() {
    hideAll();
    $('#create-account').fadeIn();
    console.log('The client\'s email is: ', clientEmail);
    if (clientEmail) {
      $('#username-create').hide();
      $('#username-preset').text(clientEmail);
      $('#username-preset').show(clientEmail);
    }
  });

  $('#glogin').click(function() {
    clientkey = newUUIDv4();
    window.open(COMMON.urlPrefix + "/glogin?clientkey=" + clientkey);
  });

  notLoggedIn();

  $.pm.bind('init', function(data) {
    console.log(data);
    clientLocation = data.clientLocation;
    clientEmail = data.email;
    if(data.showCreate) {
      $('#createplt').show();
    }
    console.log('Client location is: ', clientLocation);
    if(!clientLocation) {
      console.log("Unexpected message from client: ", e);
      return;
    }
    console.log("CL: ", clientLocation);
    console.log("CLH: ", clientLocation.hash);
    if(clientLocation.hash !== "" && clientLocation.hash !== "#") go();
  });

  window.login = function(data) {
    data = JSON.parse(data);
    console.log('maybe setting token: ', data);
    console.log('client key: ', clientkey);
    if(clientkey === data.clientkey) {
      data.loginInfo.station = capServer.restore(data.loginInfo.station);
      data.loginInfo.makeStash = capServer.restore(data.loginInfo.makeStash);
      handleLoginInfo(data.loginInfo);
    }
  };

  function launchWithLauncher(launchInfo, stasher, launcher) {
    console.log('Launching: ', launchInfo);
    console.log('With stasher: ', stasher.serialize());
    stasher.post({
      private_data: launchInfo.private_data
    },
    function(restoreCap) {
      var nav = launchInfo.domain +
                launchInfo.url +
                "#" +
                encodeURI(restoreCap.serialize());
      console.log('Nav: ', nav);
      launcher(nav);
    },
    function(err) { 
      console.log('Make-stash failed: ', err);
    });
  }

  function launch(launchInfo) {
    launchWithLauncher(launchInfo, makeStash, function(nav) {
        console.log("About to launch: ", nav);
        window.parent.location.href = nav;
      });
  }


  function handleLoginInfo(loginInfo) {
    console.log("Login-infoing", loginInfo);
    makeStash = loginInfo.makeStash;
    loginEmail = loginInfo.email;
    loginInfo.station.get(function(station_info) {
      stationInfo = station_info;
      console.log('station_info: ', station_info);
      console.log('stationInfo: ', stationInfo);
      go();
    });
  }

  $('#submit').click(function(e) {
    var uname = $('#username-create').val();
    if($('#username-preset').text() !== '') {
      uname = $('#username-preset').text();
    }
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
      createAccount.post({
          username : uname,
          password : password1
        }, 
        function(loginInfo) {
          loginInfo.email = uname;
          handleLoginInfo(loginInfo);
        },
        failure);
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
    console.log('Making an instance choice');
    var accountsDiv = $('#account-frame');
    hideAll();
    console.log('choicing: ', instanceInfos);
    accountsDiv.fadeIn();
    instanceInfos.forEach(function(instance) {
      instance.get(function(instanceInfo) {
        var div = $('<div></div>');
        var elt = $('<button class="launchButton"></button>');
        if(typeof instanceInfo.public_data === 'string') {
          elt.text('Launch ' + instanceInfo.public_data);
        }
        else { return; } // Don't show the relationship
        div.append(elt);
        accountsDiv.append(div);
        elt.click(function() {
          launch(instanceInfo);
        });
      });
    });
  }

  var launched = false;
  function go() {
    if(launched) { console.log('Refusing to launch twice'); return; }
    launched = true;
    console.log('Launching...');
    // TODO(joe): need to make sure we have a reasonable clientLocation
    // if we're going to launch here.
    var port = makePostMessagePort(window.parent, "belay");
    console.log('Made a belay port...');
    var tunnel = new CapTunnel(port);
    console.log('Made a belay tunnel...');
    capServer.setResolver(function(instanceID) {
      if(instanceID !== this.instanceID) {
        return tunnel.sendInterface;
      }
    });
    tunnel.setLocalResolver(function() { return capServer.publicInterface; });
    console.log('StationInfo: ', stationInfo);

    if(stationInfo) {
      console.log('StationInfo.instances[@]: ', stationInfo.instances['@']);
      stationInfo.instances.get(function(instanceInfos) {
        console.log('Instance infos: ', instanceInfos, instanceInfos.length);
        if(instanceInfos.length > 0) {
          instanceChoice(instanceInfos);
        }
        else {
          hideAll();
          $('#nobody').fadeIn();
        }
        console.log('Done callback');
      });
    }

    console.log('Checking things');
    var stashser, stashcap;
    // NOTE(joe): We're only using stashes that point to the Belay server,
    // which this check is ensuring.
    // TODO(joe): Is this necessary?  How badly can a client screw us up here?
    if (typeof clientLocation === 'object' &&
        typeof clientLocation.hash === 'string' &&
        clientLocation.hash.length > 2// &&
/*        clientLocation.hash.indexOf(COMMON.urlPrefix) !== -1 */) {
      console.log('Launching instance');
      stashser = clientLocation.hash.substr(1);
      stashcap = capServer.restore(stashser);
      launchInstance(stashcap);
    }
    else {
      console.log('Launching non-instance');
      launchNonInstance();
    }

    function launchWithoutSaving(launchCap, sk, fk) {
      console.log('Getting: ', launchCap);
      launchCap.get(function(launchInfo) {
        console.log('Got launchCap: ', launchInfo);
        launchWithLauncher(launchInfo, stashcap, function(nav) {
            sk(nav);
          });
        },
        function(err) {
          console.log('LaunchWOSaving: ', err);
        });  
    }

    function launchInstance(stashcap) {
      stashcap.get(function(stashed) {
          tunnel.sendOutpost(capServer.dataPreProcess({
            services: {
              launchWithoutSaving: capServer.grant(launchWithoutSaving)
            },
            launchInfo: stashed
          }));
        },
        function(fail) {
          console.log('Getting stashed value failed: ', fail);
        });
    }

    function launchNonInstance() {
      var services = {
          becomeInstance: capServer.grant(function(launchInfo, sk, fk) {
            stationInfo.newInstance.post(launchInfo, function(launched) {
              launch(launchInfo);
            },
            function(err) {
              console.log('belay_frame: Failed to create new instance: ', err);
              fk('failed');
            });
          }),
          loginEmail: loginEmail
        };
      console.log('services: ', services);
      tunnel.sendOutpost(capServer.dataPreProcess({
        services: services
      }));
    }
  }
});

