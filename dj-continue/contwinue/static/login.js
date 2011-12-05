function getAuthInfoE(onLoadTimeE, login) {
	var loginclickedE = merge_e(
			extractEvent_e('loginbutton','click'),
			merge_e(
				extractEvent_e('usernamebox','keypress'),
				extractEvent_e('passwordbox','keypress')
			).filter_e(function(e) {return e.keyCode == 13;}));

	var loginQueryE = loginclickedE.transform_e(function(lc) {
			$('loginbutton').focus();
			return [login,
				{email:getObj('usernamebox').value,password:getObj('passwordbox').value}];
	});
	var loginE = postE(loginQueryE);

	var failedLoginE = loginE.filter_e(function(v) {return !v;});
	failedLoginE.transform_e(function(_) {
		/*TODO: do something else here? */
		window.alert("Login Failed!");
	});

	var authInfoE = loginE.filter_e(function(v) { return v != false; });
	return authInfoE;
}
function getLogoutEventsE(onLoadTimeE) {
    if ($URL('logout'))
	return getFilteredWSO_e(onLoadTimeE.constant_e(
		    genRequest({url:'Auth/logOut',fields: {cookie:$URL('logout')}})));
    else
	return receiver_e();
}
function doResetPassword(fpClicksE) {
    var rpWidget = new CombinedInputWidget(
	    [new TextInputWidget('',40),
	    new TextInputWidget('',40)],
	    function(un,em) {
	    	return TABLE({className:'key-value'},
		    TR(TH('Username:'),TD(un)),
		    TR(TH('Email: '),TD(em)));
		}).withButton(
		    new ButtonWidget('Reset Password'),
		    function(tbl,btn) {
			    return DIV(
				P('To reset your password, please enter your username and email address above. You will be emailed with a link that will enable you to enter a new password.'),
				tbl,
				P({style:{textAlign:'center'}},btn));
		    }).serverSaving(
			function(rpi) {
				return genRequest(
				    {url:'User/resetPassword',
				    fields:{username:rpi[0],email:rpi[1]}})});
    return merge_e(fpClicksE.constant_e(rpWidget.dom),rpWidget.events.serverResponse.transform_e(
    	function(sr) {
		if(sr.error) return P({className:'error'},sr.error);
		else return P('Thanks! You will be emailed shortly.');
		})).startsWith(DIV());
}
function loader() {
	var flapjax = flapjaxInit();
	demoEventsE = consumer_e();
	document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);});};
	var onLoadTimeE = receiver_e();
	var exceptsE = captureServerExcepts();
	handleExcepts(exceptsE);
  var capServer = new CapServer();

  var expecting_existing;
  extractEvent_e('glogin', 'click').transform_e(function(_) {
    expecting_existing = false;
    clientkey = newUUIDv4();
    window.open(COMMON.urlPrefix + "/glogin?clientkey=" + clientkey);
  });

  extractEvent_e('glogin-return', 'click').transform_e(function(_) {
    clientkey = newUUIDv4();
    expecting_existing = true;
    window.open(COMMON.urlPrefix + "/glogin?clientkey=" + clientkey);
  });

  var deptURL = function(bi, tail) {
    return COMMON.urlPrefix + '/' + bi.info.shortname + tail;
  };
  var launch = function(launchable) {
    var newLoc = launchable.launchbase + '#' + launchable.launchcap;
    window.location.href = newLoc;
  };
	var basicInfoE = getBasicInfoE(onLoadTimeE).transform_e(function(bi) {
    window.login = function(jsonData) {
      var data = JSON.parse(jsonData);
      console.log('Made it: ', data);
      if(data.newaccount) {
        capServer.restore(deptURL(bi.value, '/create_user')).post({
            key: data.key,
            email: data.email
          },
          function(success) {
            if(success.error) { return; /* TODO(joe): handle */ }
            console.log('Success! ', success);
            launch(success[0]);
          },
          function(fail) {
            console.log('Failed, ', fail);
          });
      }
      else {
        capServer.restore(deptURL(bi.value, '/get_launch')).post({
            key: data.key
          },
          function(success) {
            console.log('Success (login)!', success); 
            launch(success[0]);
          },
          function(fail) {
            console.log('Failed (login)!', fail); 
          });
      }
    }

    return bi.value;
  });
	doConfHead(basicInfoE);
	basicInfoE.transform_e(function(bi) {
		document.title = bi.info.name;
	});
	var authInfoE = getAuthInfoE(onLoadTimeE, capServer.restore(COMMON.urlPrefix + '/continue_login'));
	getLogoutEventsE(onLoadTimeE);
	authInfoE.transform_e(function(ai) {
    if(ai && ai.launch && ai.launch.length === 1) {
      launch(ai.launch[0]);
    }
	});

  var requestedB = lift_b(function(bi, email) {
    if(!bi || !email) return null;
    return [capServer.restore(deptURL(bi, '/request_account')),
            {email: email}];
  }, basicInfoE.startsWith(null),
     extractValue_b('email'));

  var requestedE =
    postE(extractEvent_e('reqacctok', 'click').snapshot_e(requestedB));

  insertValueB(
  	extractEvent_e('reqacct','click').constant_e('block').startsWith('none'),
    'reqacct_content','style','display');
  insertValueB(requestedE.constant_e('block').startsWith('none'),
               'requested','style','display');

  insertValueB(extractEvent_e('reqacct','click').constant_e('none').startsWith('inline'),'reqacct','style','display');

  insertDomB(doResetPassword(extractEvent_e('rp-open','click')),'rp-info');

	onLoadTimeE.sendEvent('loaded!');
	
	if($URL('session') == 'expired' || $URL('session') == 'denied') 
	    insertDomB(merge_e(authInfoE,requestedE).constant_e('').startsWith('Your session has expired due to inactivity. Please login again.'),'expired','beginning');
    
}
