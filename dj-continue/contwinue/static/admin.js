function deleteTransform(objName,evt,cap) {
	return postE(
		evt.transform_e(function(dobj) {
			return [cap, genRequest({id:dobj.id})];
	}));
}

function makeDecisionsTable(decisions,targetable,addDecision) {
	return new ModListWidget(
		filter(function(d) {return targetable==d.targetable;},decisions),
		TR(TH('Abbr'),TH('Description'),TD()),
		function(obj) {
			var ret = new ButtonInputWidget([],
				{del: new LinkWidget('delete')},
				function() {return obj},
				function(_,bob) {return TR(TD(obj.abbr),TD(obj.description),TD((obj.abbr == 'R' || obj.abbr == 'U') ? '' : bob.del));});
			ret.events.del = deleteTransform('DecisionValue',ret.events.del);
			return ret;
		},
		function() {
			return new ButtonInputWidget(
				[new TextInputWidget('',1,1),
				 new TextInputWidget('',20)],
				{value: new ButtonWidget('Add')},
				function(a,d,t) {return {cookie:authCookie,abbr:a,description:d,targetable:targetable?'yes':'no'};},
				function(is,bs) {return TR(TD(is[0]),TD(is[1]),TD(is[2]),TD(bs.value));})
			.serverSaving(function(v) {return genRequest({url:'DecisionValue/add',fields:v});},true);
		}).dom;
}

function makeTopicsTable(topics) {
	return new ModListWidget(
		topics,
		TR(TH('Name'),TD()),
		function(obj) {
			var ret = new ButtonInputWidget([],
				{del: new LinkWidget('Delete')},
				function() {return obj;},
				function(_,bob) {return TR(TD(obj.name),TD(bob.del));});
			ret.events.del = deleteTransform('Topic',ret.events.del);
			return ret;
		},
		function() {
			return new ButtonInputWidget(
				[new TextInputWidget('',20)],
				{value: new ButtonWidget('Add')},
				function(n) {return {cookie:authCookie,name:n};},
				function(is,bs) {return TR(TD(is[0]),TD(bs.value));})
			.serverSaving(function(v) {return genRequest({url:'Topic/add',fields:v});},true);
		}).dom;
}

function makeRCompsTable(rcomps) {
	return new ModListWidget(
		rcomps,
		TR(TH('Name'),TH('PC Only?'),TD()),
		function(obj) {
			var ret = new ButtonInputWidget([],
				{del:new LinkWidget('Delete')},
				function() {return obj;},
				function(_,bob) {return TR(TD(obj.description),TD(obj.pconly ? 'Y' : 'N'),TD(bob.del));});
			ret.events.del = deleteTransform('ReviewComponentType',ret.events.del);
			return ret;
		},
		function() {
			return new ButtonInputWidget(
				[new TextInputWidget('',30),
				new CheckboxWidget(false)],
				{value:new ButtonWidget('Add')},
				function(d,p) {return {cookie:authCookie,description:d,pconly:(p ? 'yes' : 'no')};},
				function(is,bs) {return TR(TD(is[0]),TD(is[1]),TD(bs.value));})
			.serverSaving(function(v) {return genRequest({url:'ReviewComponentType/add',fields:v});},true);
		}).dom;
}

function makeComponentsTable(basicInfo) {
	return new ModListWidget(
		basicInfo.components,
		TR(TH('Abbr'),TH('Description'),TH('Format'),TH('Deadline (DD-MM-YYYY)'),TH('Grace'),TH('Man'),TH('Max'),TD(),TD()),
		function(obj) {
			var ret = new ButtonInputWidget(
				[new TextInputWidget(obj.abbr,1,1),
				new TextInputWidget(obj.description,20),
				new DateWidget(obj.deadline),
				new TextInputWidget(obj.gracehours,3,3),
				new TextInputWidget(obj.sizelimit,4,4)],
				{value:new ButtonWidget('Save Changes'),
				del:new LinkWidget('Delete')},
				function(a,d,de,g,s) {
					return {id:obj.id,cookie:authCookie,abbr:a,description:d,
						format:obj.format,
						deadline:de,gracehours:g,mandatory:(obj.mandatory?'yes':'no'),
						sizelimit:s};},
				function(is,bs) {
					return TR(TD(is[0]),TD(is[1]),TD(obj.format),
						TD(is[2]),TD(is[3],' Hours'),TD(obj.mandatory ? 'Y' : 'N'),TD(is[4]),
						TD(bs.value),TD(obj.id == basicInfo.info.displayComponent.id ? '' : bs.del));})
			.serverSaving(function(v) {
				return genRequest({url:'ComponentType/change',fields:v});
			},true);
			ret.events.del = deleteTransform('ComponentType',ret.events.del);
			return ret;
		},
		function() {
			return new ButtonInputWidget(
				[new TextInputWidget('',1,1),
				new TextInputWidget('',20),
				new SelectWidget('Text',[OPTION({value:'Text'},'Text'),OPTION({value:'PDF'},'PDF'),OPTION({value:'Any'},'Any')]),
				new DateWidget(0),
				new TextInputWidget(0,3,3),
				new CheckboxWidget(false),
				new TextInputWidget(0,4,4)],
				{value:new ButtonWidget('Add')},
				function(a,d,f,de,g,man,max) {
					return {cookie:authCookie,
							abbr:a,description:d,deadline:de,format:f,
							gracehours:g,sizelimit:max,
							mandatory:(man?'yes':'no')};},
				function(is,bs) {
					return TR(TD(is[0]),TD(is[1]),TD(is[2]),TD(is[3]),TD(is[4],' Hours'),
							TD(is[5]),TD(is[6]),TD(bs.value));})
				.serverSaving(function(v) {return genRequest({url:'ComponentType/add',fields:v});},true);
		}).dom;
}

function UserTableWidget(usersB,isPC,curUser,adminInfo) {
	Widget.apply(this);

	var roleChangeE = consumer_e();
	var deletionClicksE = consumer_e();
	var deletionsE = deletionClicksE.transform_e(function(_) {
		if (window.confirm('Are you sure you want to delete '+_.fullname+'\'s account?'))
			return _;
		else
			return null;
	}).filter_e(function(_) {return _ != null;});
	getFilteredWSO_e(deletionsE.transform_e(function(u) {
		return genRequest(
			{url: 'User/'+u.id+'/delete',
			fields:{cookie:authCookie}});
		}));

	var cUsersB = switch_b(usersB.transform_b(function(users) {
		return collect_b(users,deletionsE,function(delUser,existing) {
			return filter(function(_) {return _.id != delUser.id;},existing);
		});
	}));
	
	function UserEntry(u) {
		this.user = u;
		this.getObj = function() {return this.user;};
		this.getDoms = function() {
			var user = this.user;
			var deleteLnk = A({href:'javascript://Delete'},'[delete]');
			deletionClicksE.add_e(extractEvent_e(deleteLnk,'click').constant_e(user));
			var emailLnk = A({href:'javascript://Change'},'[change]');
			var changeBtn = INPUT({'type':'button','value':'OK'});
			var changeField = INPUT({'type':'text','value':user.email});
			var changedE = getFilteredWSO_e(
					extractEvent_e(changeBtn,'click').transform_e(
						function(newEmail) {
							user.email = changeField.value;
							return genRequest(
								{url:'User/'+user.id+'/changeEmail',
								fields:{cookie:authCookie,email:user.email}});
					}
				)
			);
			var whichToDisplayB = merge_e(changedE.constant_e(1),extractEvent_e(emailLnk,'click').constant_e(2)).startsWith(1);
			var emailDomB = lift_b(function(whch) {
				var noChangeField = SPAN(user.email);
				if(whch == 1) return TD(noChangeField,' ',emailLnk); else return TD(changeField,changeBtn);
			},whichToDisplayB);
			var userTd = TD(user.username);

			if(!isPC) {
				return [TRB(userTd,TD(user.fullname),emailDomB,TD(deleteLnk))];
			}
			else {
				return [TRB(userTd,TD(user.fullname),emailDomB,map(function(rl) {
					if(rl == 'admin' && (user.id == curUser.id || user.id == adminInfo.adminContact.id))
						return TD('Y');
					var rolecb = INPUT({type:'checkbox',checked:inList(rl,user.rolenames)});
					roleChangeE.add_e(extractEvent_e(rolecb,'change').transform_e(function(_) {
						if(rolecb.checked)
							user.rolenames = user.rolenames.concat([rl]);
						else
							user.rolenames = filter(function(r) {return r != rl;}, user.rolenames);
						return {id:user.id,role:rl,value:rolecb.checked};
					}));
					return TD(rolecb);
				},['admin','reviewer']),(user.id == curUser.id || user.id == adminInfo.adminContact.id) ? TD() : TD(deleteLnk))];
			}
		}
	}

	var columns = [
		new Column('login','Login',function(a,b) {return a.username < b.username ? -1 : (a.username > b.username ? 1 : 0);}),
		new Column('name','Name',function(a,b) {return a.fullname < b.fullname ? -1 : (a.fullname > b.fullname ? 1 : 0);}),
		new Column('email','Email',function(a,b) {return a.email < b.email ? -1 : (a.email > b.email ? 1 : 0);})];

	if (isPC) {
		columns = columns.concat([
			new Column('admin','Admin?',function(a,b) {return 0;}),
			new Column('rev','Reviewer?',function(a,b) {return 0;})]);
			}
		
	this.dom = new TableWidget(cUsersB.transform_b(function(users) {return map(function(u) {return new UserEntry(u);},users);}),'member',columns).dom;

	this.events.roleChanged = roleChangeE;
}

function loadComm(basicInfoE,adminInfoE,usersByRoleB,dvCapsE) {
	var emailDecisionDomB = basicInfoE.transform_e(function(basicInfo) {
		return SELECT({name:'email-decision'},
			map(function(dec) {
				return OPTION({value:dec.id},dec.description)
			},basicInfo.decisions)
			);
		}).startsWith(SELECT({name:'email-decision'}));
	var emailDecisionE = $E(emailDecisionDomB);
	var emailRadioB = $B('emailto');
	var emailQueryB = 
    getE(lift_b(function(emailDecision, dvCaps) {
      return dvCaps[emailDecision]; 
    }, emailDecisionE.startsWith(null), dvCapsE.startsWith({})).
    changes().filter_e(function(v) { return v; })).startsWith([]);
	var decusersB = lift_b(function(emailQuery,usersByRole) {
		var ubid = {};
		map(function(u) {ubid[u.id] = u;},usersByRole.user);
		return map(function(qi) {return ubid[qi];},emailQuery);
	},emailQueryB,usersByRoleB);

	var emaileesB = lift_b(function(decusers,rad,usersByRole) {
			if(rad == 'allsub')
				return usersByRole.user;
			else if(rad == 'somesub')
				return decusers;
			else
				return usersByRole.pc;
		},decusersB,emailRadioB,usersByRoleB);

	var emailStrB = emaileesB.transform_b(function(ems) {return P(fold(function(v, acc) {if (acc == null) return v.email; else return acc + ', '+v.email},null,ems));});

	var sendReviewsB = lift_b(function(cbox,radio) {
		if(radio != 'pc' && cbox) return 'yes'; else return 'no';
	},$B('email-reviews'),emailRadioB);

	var psE = merge_e(extractEvent_e('email-preview','click').constant_e('preview'),extractEvent_e('email-send','click').constant_e('send'))

	var emailsE = getFilteredWSO_e(snapshot_e(psE,lift_b(function(stage,emailees,subject,body,reviews) {
		var uids = map(function(u) {return u.id;},emailees);
		return genRequest(
			{url: 'User/sendEmails',
			fields: {cookie:authCookie,stage:stage,sendReviews:reviews,users:uids,subject:subject,body:body}});
	},psE.startsWith('preview'),emaileesB,$B('email-subject'),$B('email-message'),sendReviewsB)));
	
	var emailContentE = emailsE.transform_e(function(pvs) {
		if(pvs.sent) return P(STRONG('Emails sent.')); else return DIV({className:'email-preview'},H3('Full text of emails to send:'),map(function(u) {
			return DIV({className:'single-email-preview'},'To: '+u.To.email,BR(),'Subject: '+u.Subject,BR(),BR(),PRE(u.Body));
		},pvs));
	});

	insertDomB(emailContentE.startsWith(''),'previews');
	insertDomB(emaileesB.transform_b(function(el) {return ''+el.length + ' Users';}),'email-to','beginning');
	insertDomB(emailDecisionDomB,'email-decision');
	insertDomB(emailStrB,'recipients','beginning');
	insertValueB(emailRadioB.transform_b(function(_) {if(_ == 'pc') return 'trhide'; else return 'trshow';}),'email-reviews-row','className');

	insertDomB(adminInfoE.transform_e(function(adminfo) {return P(adminfo.adminContact.fullname + ' <'+adminfo.adminContact.email+'>');}).startsWith(P()),
				'email-from','beginning');
}

function loadUserTables(curUserE,adminInfoE,usersByRoleB,setContactE) {
	var pcTableB = lift_b(function(cu,ai) {
		if(cu && ai)
			return new UserTableWidget(usersByRoleB.transform_b(function(_) {return _.pc;}),true,cu,ai);
		else
			return {dom:DIVB(),events:{roleChanged:receiver_e()}};
	},curUserE.startsWith(null),adminInfoE.startsWith(null));

	var roleChangeE = switch_e(pcTableB.changes().transform_e(function(_) {return _.events.roleChanged;}))
	var pcDomB = switch_b(pcTableB.transform_b(function(_) {return _.dom;}));

	getFilteredWSO_e(roleChangeE.transform_e(function(rcreq) {
		return genRequest(
			{url:'User/'+rcreq.id+'/setRole',
			fields:{cookie:authCookie,role:rcreq.role,value:rcreq.value?'on':'off'}});
		}));
	var adminUsersB = lift_b(function(ui,_) {return filter(function(u) {return inList('admin',u.rolenames);},ui.pc);},usersByRoleB,roleChangeE.startsWith(null));

	var dcAdmB = lift_b(function(adminfo,admins) {
		if(adminfo)
			return SELECT(
				map(function(u) {
					var sel = (u.id == adminfo.adminContact.id);
					return OPTION({value:u.id,selected:sel},u.fullname);
				},
			admins));
		else
			return SELECT();
	},adminInfoE.startsWith(null),adminUsersB);

	dcAdmChangesE = $B(dcAdmB).changes().collect_e(
		{changed:false,val:null},function(nv,ov) {
			if(nv && nv != ov.val)
				return {changed:true,val:nv};
			else
				return {changed:false,val:nv};
		}
	).filter_e(function(_) {return _.changed;}).transform_e(function(_) {return _.val;});

  var contactWorldB = worldB([null, null],
    [[ dcAdmChangesE, function(post, ci) { return [post[0],{contactID:ci}]; }],
     [ setContactE, function(post, sc) { return [sc, post[1]]; }]]);

  var changeContactE = 
    contactWorldB.changes().filter_e(function(post) { return post[0] && post[1]; });

  postE(changeContactE).transform_e(function(_) {loadAdminfoE.sendEvent('Load!')});

	insertDomB(dcAdmB,'dcadm');
	
	insertDomB(pcDomB,'pc_members');
	var userTable = new UserTableWidget(usersByRoleB.transform_b(function(_) {return _.user;}),false);
	insertDomB(userTable.dom,'users');
}

function loadDS(basicInfoE,adminInfoE) {
	var dsDomB = lift_b(function(basicInfo,adminInfo) {
		if(basicInfo.info.useDS) {
			return new CombinedInputWidget(
				[new TextInputWidget(adminInfo.dsCutoffHi,5,5),
				 new TextInputWidget(adminInfo.dsCutoffLo,5,5),
				 new TextInputWidget(adminInfo.dsConflictCut,5,5)],
				 function(a,b,c) {return [a,b,c];})
				.withButton(new ButtonWidget('Re-categorize Papers'),
					function(ds,bs) {
						return DIV(
							H3('Decision Support'),
							P('The decision support system recategorizes papers every night based on all reviews that have been received by that time. It uses three parameters to categorize papers: the "high-score cutoff", which is a score from 0-9 that defines roughly what the average score of a "good" paper should be; the "low-score cutoff", which defines roughly what the average score of a "bad" paper should be; and the "conflict cutoff", a number from 0-1 which defines how much conflict is needed for a paper to be marked as "conflicted". Note that not all "good" papers will necessarily have a score above the high-score cutoff, nor will all papers with a score above the high-score cutoff be necessarily marked "good".'),
							P('To modify these cutoffs, change the values below and then click "Re-categorize Papers". You may also just click "Re-categorize Papers" without changing the values to force the system to re-categorize papers immediately. Please allow up to 30 seconds for the re-categorization.'),
							TABLE({className:'key-value'},
								TBODY(TR(TH('High-Score Cutoff'),TD(ds[0])),
									TR(TH('Low-Score Cutoff'),TD(ds[1])),
									TR(TH('Conflict Cutoff'),TD(ds[2])),
									TR(TD({colSpan:2},bs)))));
						})
				.serverSaving(function(v) {
					return genRequest({url:'updateScores',
							fields:{hi:v[0],lo:v[1],cc:v[2],cookie:authCookie}});
				})
				.dom;
		}
		else {
			return SPAN();
		}
	},basicInfoE.startsWith({info:{useDS:false}}),adminInfoE.startsWith(null));
	insertDomB(dsDomB,'ds');
}

function loader() {
	var flapjax = flapjaxInit();
	authCookie = $URL('cookie');
  var capServer = new CapServer();
	var onLoadTimeE = receiver_e();
	var exceptsE = captureServerExcepts();
	handleExcepts(exceptsE);
  var launchCap = launchCapFromKey(COMMON.urlPrefix, capServer);
  var launchE = getE(onLoadTimeE.constant_e(launchCap));
	var basicInfoE = getFieldE(launchE, 'basicInfo');
	basicInfoE.transform_e(function(bi) {
		document.title = bi.info.shortname + ' - Manage Conference';
  });
	doConfHead(basicInfoE);
  loadAdminfoE = merge_e(onLoadTimeE);
	var curUserE = getFieldE(launchE, 'currentUser');
	doLoginDivB(curUserE);
	var authorTextE = getE(launchE.transform_e(function(li) {
    return li.getAuthorText;
  }));

  var accountTabB = lift_b(function(li, bi) {
    if(li && bi) {
      var searchString = 'admin ' + bi.info.name;
      return makeAccountInfoTab(
        li,
        searchString,
        COMMON.urlPrefix + '/admin' + window.name
      );
    }
    return SPANB();
  }, launchE.startsWith(null), basicInfoE.startsWith(null));

	lift_e(function(cu,bi,li) {
			var AdminTabs = new TabSet(
				constant_b(cu.rolenames),
				{admin:$$('admin-tab'),reviewer:[],user:[],loggedout:[]},
				function(that) {
					var tabClicksE = map(function(tab) {
						return (tab == getObj('back_to_list_tab') ? receiver_e() :  extractEvent_e(tab,'click').constant_e(tab.id));
					},that.allTabs);
					return merge_e.apply(this,tabClicksE).startsWith('config_tab');
				}
			);
			setTitle(bi,AdminTabs.currentTabB);
			AdminTabs.displayOn('config_tab','config_content');
			AdminTabs.displayOn('users_tab','user_content');
			AdminTabs.displayOn('customize_tab','custom_content');
			AdminTabs.displayOn('comm_tab','comm_content');
			AdminTabs.displayOn('info_tab','info_content');
      AdminTabs.displayOn('account_tab', 'account_content');
			getObj('back_to_list_tab').href =
        COMMON.urlPrefix + "/review#" + li.launchReview;
	},curUserE,basicInfoE,launchE);

	var adminInfoE = getE(getFieldE(launchE, 'getAdmin'));
	var usersInfoB = getE(getFieldE(launchE, 'getAll')).startsWith([]);
	var usersByRoleB = usersInfoB.transform_b(function(users) {
		var out = {pc:[],user:[]};
		map(function(u) {if (inList('writer',u.rolenames)) out.user.push(u); else out.pc.push(u);},users);
		return out;
	});

	var subRevsB = getE(getFieldE(launchE, 'getSubreviewers')).startsWith([]);
	var subDomB = subRevsB.transform_b(function(srs) {
		return BLOCKQUOTE(map(function(sr) {return P({className:'pre'},sr);},srs));
	});
	insertDomB(subDomB,'subrevlist');

 insertValueE(methodE(getFieldE(launchE, 'configure'), 'serialize', []), 'configure', 'action');

  var setContactE = getFieldE(launchE, 'setContact');
  var dvCapsE = getFieldE(launchE, 'getPapersOfDV');
	loadComm(basicInfoE,adminInfoE,usersByRoleB,dvCapsE);
	loadUserTables(curUserE,adminInfoE,usersByRoleB,setContactE);

	insertValueE(basicInfoE.transform_e(function(bi) {return bi.info.name;}),'conference_name','value');
	insertValueE(basicInfoE.transform_e(function(bi) {return bi.info.shortname;}),'conference_short_name','value');
	insertValueE(basicInfoE.transform_e(function(bi) {return bi.info.showBid;}),'showBid','checked');
	insertValueE(basicInfoE.transform_e(function(bi) {return bi.info.showNum;}),'showNum','checked');
	insertValueE(authorTextE.transform_e(function(at) {return at[0];}),'general_text','checked');
	insertValueE(authorTextE.transform_e(function(at) {return at[1];}),'component_text','checked');

	var categoriesTableB = switch_b(basicInfoE.transform_e(function(bi) {return makeDecisionsTable(bi.decisions,true);}).startsWith(DIVB()));
	var decisionsTableB = switch_b(basicInfoE.transform_e(function(bi) {return makeDecisionsTable(bi.decisions,false);}).startsWith(DIVB()));
	var topicsTableB = switch_b(basicInfoE.transform_e(function(bi) {return makeTopicsTable(bi.topics);}).startsWith(DIVB()));
	var componentsTableB = switch_b(basicInfoE.transform_e(function(bi) {return makeComponentsTable(bi);}).startsWith(DIVB()));
	var rcompsTableB = switch_b(basicInfoE.transform_e(function(bi) {return makeRCompsTable(bi.rcomponents);}).startsWith(DIVB()));

	insertDomB(categoriesTableB,'categories');
	insertDomB(decisionsTableB,'decisions');
	insertDomB(topicsTableB,'topics');
	insertDomB(componentsTableB,'components');
	insertDomB(rcompsTableB,'rcomps');

	apcWidget = new TextAreaWidget('',10,80).withButton(
		new ButtonWidget('Add'),
		function(ae,btn) {
		return P('To add new PC members, enter their names and email addresses in the box below. You should use the format ',
			B('"Full Name" <Email Address>'),
			', with addresses separated by commas, semicolons or new lines. When you add a PC member, they will get a welcome email with a link to a username/password input form.',
			ae,BR(),btn);});
	var apcYes = new ButtonWidget('Yes');
	var apcNo = new ButtonWidget('No');
	var apcReturn = new ButtonWidget('Add More PC Members');
	var apcEmailsB = apcWidget.behaviors.value.transform_b(function(emstr) {
		var pcs = [];
		while(emstr.length) {
			var theregex = /"([^"]*)"[ \t]*<([^>]*)>/;
			var results = theregex.exec(emstr);
			if (results) {
				pcs.push({name:results[1],email:results[2]});
				emstr = emstr.substr(emstr.indexOf(results[0])+results[0].length);
				}
			else
				break;
		}
		return pcs;
	});
	var pcDataE = 
		apcYes.events.click.snapshot_e(apcEmailsB).transform_e(function(pcs) {
			var names = [];
			var emails = [];
			map(function(pc) {
				names.push(pc.name);
				emails.push(pc.email);
			},pcs);
      return {names: names, emails: emails};
    });
  var addPCsCapE = getFieldE(launchE, 'addPCs');
  var pcAddedE = postE(lift_b(function(cap, data) {
      if (cap && data) { return [cap, data]; }
      return null
    }, addPCsCapE.startsWith(null), pcDataE.startsWith(null)).
    changes().
    filter_e(id));
	var confirmB = merge_e(
		apcEmailsB.changes().transform_e(function(pcs) {
			return P(
				'You are about to add the following PC members: ',
				UL(
					map(function(pcm) {
						return LI(pcm.name,': ',pcm.email);
					},pcs)),
				'Continue?',BR(),
				apcYes.dom,' ',apcNo.dom);
		}),
		pcAddedE.transform_e(function(pcerrs) {
			if(pcerrs.length == 0) {
				return P('All PC members were successfully invited. ', apcReturn.dom);
			}
			else {
				return P({className:'error'},'There were errors adding the following PC members:',
					UL(
						map(function(err) {
							return LI(err.name,': ',err.error);
						},pcerrs)),BR(),apcReturn.dom);
			}}),
		merge_e(apcReturn.events.click,apcNo.events.click).constant_e(SPAN())).startsWith(SPAN());
	var showApcDomB = merge_e(
			apcReturn.events.click.constant_e(true),
			apcNo.events.click.constant_e(true),
			apcWidget.behaviors.value.changes().constant_e(false)).startsWith(true);
	var apcDomB = showApcDomB.transform_b(function(shw) {
		return shw ? apcWidget.dom : SPAN();
	});
	insertDomB(apcDomB,'addpc-content');
	insertDomB(confirmB,'addpc-result');
	getObj('conf_cookie').value = authCookie;

	insertDomB(switch_b(accountTabB),'account_placeholder');
	
	iframeLoad_e('conftarget').transform_e(function(_) {
	  onLoadTimeE.sendEvent('load!');
	});
	
	loadDS(basicInfoE,adminInfoE);

	onLoadTimeE.sendEvent('loaded!');
}
