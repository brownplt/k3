function getAuthInfoE(onLoadTimeE) {
	var loginclickedE = merge_e(
			extractEvent_e('loginbutton','click'),
			merge_e(
				extractEvent_e('usernamebox','keypress'),
				extractEvent_e('passwordbox','keypress')
			).filter_e(function(e) {return e.keyCode == 13;}));

	var loginQueryE = loginclickedE.transform_e(function(lc) {
			$('loginbutton').focus();
			return genRequest(
				{url:'Auth/getCookie',
				fields:{username:$('usernamebox').value,password:$('passwordbox').value}}
			);
	});
	var loginE = getFilteredWSO_e(loginQueryE);

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

  window.login = function(jsonData) {
    var data = JSON.parse(jsonData);
    console.log('Made it: ', data);
    if(data.newaccount) {
      // create an account using data.key
    }
    else {
      // show accounts using data.key or launchables
      // or maybe just launch using data.key
    }
  }

  extractEvent_e('glogin', 'click').transform_e(function(_) {
    clientkey = newUUIDv4();
    window.open(COMMON.urlPrefix + "/glogin?clientkey=" + clientkey);
  });

	var basicInfoE = getBasicInfoE(onLoadTimeE).transform_e(function(bi) {
    return bi.value;
  });
	doConfHead(basicInfoE);
	basicInfoE.transform_e(function(bi) {
		document.title = bi.info.name;
	});
	var authInfoE = getAuthInfoE(onLoadTimeE);
	getLogoutEventsE(onLoadTimeE);
	authInfoE.transform_e(function(ai) {
		if (inList('user',ai[1].rolenames))
			window.location = 'writer.html?cookie='+ai[0];
		else
			window.location = 'continue.html?cookie='+ai[0];
	});

	var requestedE = getFilteredWSO_e(extractEvent_e('reqacctok','click').transform_e(function(_) {
		return genRequest({
			url: 'UnverifiedUser/add',
			fields: {name:getObj('full_name').value,email:getObj('email').value}});
		}));
	
	insertValueB(
  	merge_e(extractEvent_e('reqacct','click').constant_e('block'),
            requestedE.constant_e('none')).startsWith('none'),
    'reqacct_content','style','display');
  insertValueB(requestedE.constant_e('block').startsWith('none'),
               'requested','style','display');

  insertValueB(extractEvent_e('reqacct','click').constant_e('none').startsWith('inline'),'reqacct','style','display');

	insertDomB(doResetPassword(extractEvent_e('rp-open','click')),'rp-info');

	onLoadTimeE.sendEvent('loaded!');
	
	if($URL('session') == 'expired' || $URL('session') == 'denied') 
	    insertDomB(merge_e(authInfoE,requestedE).constant_e('').startsWith('Your session has expired due to inactivity. Please login again.'),'expired','beginning');
    
}
