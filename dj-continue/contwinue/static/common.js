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

