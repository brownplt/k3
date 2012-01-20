/*
 * Dealing with Strings
 */

function abbrName(name) {
	var names = name.split(' ');
	var n;
	for(n = names.length-1;names[n] == '';n--);
	return names[n].substr(0,Math.min(3,names[n].length));
}
function parseAuthorList(alist) {
	var csplit;
	if(alist.indexOf(',') != -1) 
		csplit = alist.split(',');
	else
		csplit = [alist];
	var names = [];
	map(function(c) {
		if(c.indexOf('and') != -1)
			names = names.concat(c.split('and'));
		else
			names = names.concat(c);
	},csplit);
	var ret = [];
	map(function(n) {
		var allnames = strip(n).split(' ');
		ret = ret.concat([allnames[allnames.length - 1]]).concat(slice(allnames,0,allnames.length-1));
	},names);
	return fold(function(v, acc) {return acc + v;},'',ret);
}
/*
 * Application-Specific Things for Multiple Pages
 */

function TabSet(currentRolesB,roleTabs,getCurrentTabB) {
	this.roleTabs = roleTabs;
	this.allTabs = [];
	this.defaultTabs = {};

	var that = this;
	for (var role in this.roleTabs) {
		if (this.roleTabs.hasOwnProperty(role)) {
			map(function(tab) {
				if (!inList(tab, that.allTabs)) that.allTabs.push(tab);
			}, this.roleTabs[role]);
		}
	}
	this.tabsToShowB = currentRolesB.transform_b(function(roles) {
			return fold(function(v, acc) {
				map(function(tab) {
					if (!inList(tab,acc)) acc.push(tab);
				},that.roleTabs[v]);
				return acc;
			}, [], roles);
	});

	map(function(tab) {
		insertValueB(that.tabsToShowB.transform_b(function(tts) {return inList(tab,tts) ? 'inline' : 'none';}),getObj(tab).parentNode,'style','display');
	},this.allTabs);
	this.currentTabB = getCurrentTabB(this);
	map(function(tab) {
		insertValueB(that.currentTabB.transform_b(function(ctab) {
				return ctab == tab.id ? addClass(tab.className,'selected') : remClass(tab.className,'selected');}),tab,'className');
	},this.allTabs);
	this.displayOn = function(tab,tag) {
		insertValueB(this.currentTabB.transform_b(function(ct){
      return (ct == tab) ? 'block' : 'none';}),tag,'style','display');
	};
}
function getBasicInfoE(onLoadTimeE) {
	return getFilteredWSO_e(onLoadTimeE.constant_e(
		genRequest(
			{url: 'getBasic',
			fields: {},
			asynchronous: false})
		));
}
function doLoginDivB(userInfoE) {
	insertDomB(userInfoE.startsWith({rolenames:['loggedout']}).transform_b(function(userval) {
		return ((userval.rolenames.length == 1 && userval.rolenames[0] == 'loggedout') || (userval == null)) ? 
			SPAN() :
			SPAN('Login: ',B(userval.username),' (',
				fold(function(v, acc) {if(acc == null) return v; else return acc + ', '+v;},null,userval.rolenames),
			')');
		}),'login','beginning');
}
function doConfHead(basicInfoE) {
	insertDomB(basicInfoE.transform_e(function(bi) {
    return bi.info.name;
  }).startsWith(''),'confhead','beginning');
}
function setTitle(bi,currentTabB) {
	currentTabB.transform_b(function(ct) {
		if(ct && getObj(ct).title)
			document.title = bi.info.shortname + ' - '+getObj(ct).title;
		else
			document.title = bi.info.name;
	});
}
function getReviewStats(reviews) {
	if(!reviews)
		return {reviewRange:'E',rev:-1,sub:-1,maxExp:' ',max:false,min:false};

	var rs = fold(function(review,rs) {
		rs.rev += 1;
		if (review.submitted) {

			if(review.expertise.abbr) ex = review.expertise.abbr; else ex = review.expertise;
			if(review.overall.abbr) oa = review.overall.abbr; else oa = review.overall;

			rs.sub += 1;
			if (review.expertise != 'F' && ((rs.maxExp == ' ') || rs.maxExp > ex))
				rs.maxExp = ex;
			if(oa != 'U') {
				if (!(rs.max) || rs.max > oa)
					rs.max = oa;
				if (!(rs.min) || rs.min < oa)
					rs.min = oa;
			}
		}
		return rs;
	},{rev:0,sub:0,max:false,min:false,maxExp:' '},reviews);
	rs.reviewRange = (rs.max ? (rs.max == rs.min ? rs.max : rs.max+'-'+rs.min) : 'E');
	return rs;
}
function getCurUserE(onLoadTimeE,authCookie) {
	return getFilteredWSO_e(onLoadTimeE.constant_e(
		genRequest(
			{url: 'Auth/currentUser',
			fields: {cookie:authCookie},
			asynchronous:false})
	));
}
function getLoadingDiv() {
	return DIV({className:'loading'},'Please wait. Continue is loading information from the server.');
}
function compLink(cookie,pid,pname,comptype,compvalue) {
	var lastdot = compvalue.lastIndexOf('.');
	extension = lastdot == -1 ? '.pdf' : compvalue.substr(lastdot);
	compvalue = ''+pid+'-'+comptype+'-';
	pname = pname.toLowerCase();
	for(var i=0;compvalue.length<15&&i<pname.length;i++)
		if((pname[i] >= 'a' && pname[i] <= 'z') || (pname[i] >= '0' && pname[i] <= '9'))
			compvalue += pname[i];
	compvalue += extension;
	return 'Paper/'+pid+'/'+comptype+'/'+compvalue+'?cookie='+cookie;
}
function handleExcepts(exceptsE) {
	exceptsE.transform_e(function(e) {
		if(e.value == 'expired')
			window.location = 'login.html?session=expired';
		else if(e.value == 'denied')
			window.location = 'login.html?session=denied';
		return false;
	});
}

function getLaunchCap() {
  var hash = window.location.hash;
  if(hash === "" || hash ==="#") {
    hash = window.name;
  }
  else {
    window.name = hash;
  }
  return hash.substr(1);
}


/*
  Often, we don't want to put the entire capability into the url.
  Instead, we put the private part, and restore a capability based
  on a prefix determined by the client-side code.

  String * CapServer → Capability
*/
function launchCapFromKey(prefix, capServer) {
  var hash = window.location.hash;
  if(hash === '' || hash === '#') { hash = window.name; }
  else { window.name = hash; }
  window.location.hash = '#';

  if(hash === '' || hash === '#') { return false; }

  return capServer.restore(prefix + hash.substr(1));
}

function truncate(str, len) {
  if (str.length <= len) { return str; }
  return str.substr(0, len-3) + "...";
}

function worldB(init, handlers) 
/*: ∀ α . α * Array<∃ β . {0: EventStream<β>, 1: α * β -> α}> -> Behavior<α> */
{
  return merge_e.apply(null,
    handlers.map(function(handler)
    /*: ∃ β . {0: EventStream<β>, 1: α * β -> α} -> EventStream<α -> α> */
    {
      return handler[0].transform_e(function(eventValue) /*: β -> (α -> α) */ {
        return function(world) /*: α -> α */ {
          return handler[1](world, eventValue);
        };
      });
    }))
   .collect_e(init, function(handler, world) /*: (α -> α) * α -> α */ {
      return handler(world);
    })
   .startsWith(init);
}

function makeAccountInfoTab(launchInfo, searchString, launchURL) {
  var makeEmptyGoogleDiv = function() {
    var btn = INPUT({
      style: {'margin-left': '35%','text-align': 'center'},
      id:'google-attach',
      type:'button',
      value:'Attach to a Google Account'
    });
    extractEvent_e(btn, 'click').transform_e(function(_) {
      clientkey = newUUIDv4();
      window.open(COMMON.urlPrefix + "/glogin?clientkey=" + clientkey);
    });
    return DIVB(btn);
  };
  var makeEmptyContinueDiv = function() {
    var password = INPUT({type:'password', size:30});
    var repassword = INPUT({type:'password', size:30});
    var submit = INPUT({style:{float:'right'},type:'button',value:'Submit'});
    var error = DIV();
    var success = DIV();

    var cdiv = DIV(
      {className: 'key-value'},
      TR({style:{float:'right'}},TH('Password'), TD(password)),
      TR({style:{float:'right'}},TH('Password again'), TD(repassword)),
      BR(),
      submit,
      error,
      success
    );

    var attemptsE = extractEvent_e(submit, 'click').transform_e(function() {
      var p1 = getObj(password).value;
      var p2 = getObj(repassword).value;
      if (p1 !== p2) {
        return {error: true, message: 'Passwords didn\'t match'};
      }
      if (p1 === '') {
        return {error: true, message: 'Empty passwords not allowed'};
      }
      return {
        success: true,
        val: [launchInfo.addPassword, {password: p1}]
      };
    });

    insertDomB(attemptsE.transform_e(function(r) {
        if (r.error) {
          return SPAN({style:{color:'red'}}, r.message);
        }
        else {
          return SPAN();
        }
      }).startsWith(SPAN()), error);

    var reqE = postE(attemptsE.filter_e(function(r) { return r.success; }).
                       transform_e(function(r) { return r.val; }));

    insertDomB(reqE.transform_e(function(_) {
      return SPAN({style:{color:'green'}}, 'Password added');
    }).startsWith(SPAN()), success);

    return cdiv;
  };

  var googles = launchInfo.credentials.googleCreds;
  var continues = launchInfo.credentials.continueCreds;
  var googleDiv;
  var continueDiv;

  var googleEventsE = receiver_e();
  window.login = function(data) {
    googleEventsE.sendEvent(data);
  };
  var googlePostE = postE(googleEventsE.transform_e(function(data) {
    var jsonData = JSON.parse(data);
    return [launchInfo.addGoogleAccount, {
      'key': jsonData.key,
      'new': jsonData.newaccount
    }];
  }));

  var googleErrorsE = googlePostE.filter_e(function(r) {
    return r.error;
  });
  var googleErrorsDiv = DIVB({
      style: {
        display: googleErrorsE.constant_e('block').startsWith('none'),
        color: 'red'
      }
    },
    googleErrorsE.transform_e(function(r) {
      return r.message;
    }).startsWith(''));

  var googleSuccessesE = googlePostE.filter_e(function(r) {
    return r && !r.error;
  });

  var loginlink = COMMON.urlPrefix + '/' + launchInfo.basicInfo.info.shortname +'/home';

  var googlesB = googleSuccessesE.startsWith(googles);
  var googleDivB = lift_b(function(googles) {
    if(googles.length === 0) {
      var btnDiv = makeEmptyGoogleDiv();
      return DIVB(googleErrorsDiv, btnDiv);
    }
    else {
      return DIVB(
        P('This account is associated with the Gmail account for ',
  STRONG(googles[0].email), '.  This means you can sign in with Google to get back to' +
  ' your submissions.'));

    }
  }, googlesB);
  
  if(continues.length === 0) { continueDiv = makeEmptyContinueDiv(); }
  else {
    continueDiv = 
      DIV(
        P("This will let you log in as ", STRONG(launchInfo.email), " with the password " +
          "you create at ", A({target:'_blank',href:loginlink}, loginlink), '.'),
        P(STRONG("This account has a password, but you can add another if you like.")),
        makeEmptyContinueDiv()
      );
  }

  var pad = {style:{margin:'1em'}};
  var link = DIV(pad,H3('Bookmark this link, and visit it directly: '),
                DIV({style:{'margin':'1em'}},A({href:launchURL, target:'_blank'},launchURL)));

  var search = DIV(pad,H3('Save the invitation message.  You can search your inbox for:'),
                  DIV({style:{'text-align':'center', 'margin': '1em'}},
                      STRONG(searchString)))
  var accountGoogle = DIVB(pad,H3('Associate with a Google account:'),
                            switch_b(googleDivB));
  var accountContinue = DIV(pad,H3('Create a password:'),
                              continueDiv);

  return DIVB({style:{width:'70%','padding-left':'15%','padding-bottom':'2em'}},
             PB('Welcome, ', STRONG(launchInfo.email), '.  ' +
               'You have several options for returning to your account:',
               P(),
               ULB(
                link,
                search,
                accountGoogle,
                accountContinue)))
}

function getFieldE(liE, fld) {
  return liE.transform_e(function(li) {
    return li[fld];
  });
}

function methodE(objE, methname, args) {
  return objE.transform_e(function(obj) { return obj[methname].apply(obj, args); });
}

function one_e(val) {
  var rec = receiver_e();
  rec.sendEvent(val);
  return rec;
}

function id(_) { return _; }
