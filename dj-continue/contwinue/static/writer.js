function makeAccountInfoTab(launchInfo, basicInfo, launchKey) {
  var makeEmptyGoogleDiv = function() {
    var btn = INPUT({
      style: {'margin-left': '35%','text-align': 'center'},
      id:'google-attach',
      type:'button',
      value:'Attach to a Google Account'
    });
    return DIV(btn);
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

    insertDomB(attemptsE.filter_e(function(r) {
        return r.error;
      }).
      transform_e(function(err) {
        return SPAN({style:{color:'red'}}, err.message);
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

  if(googles.length === 0) { googleDiv = makeEmptyGoogleDiv(); }
  else {
    googleDiv = DIV(
      P('This account is associated with the Gmail account for ',
STRONG(googles[0].email), '.  This means you can sign in with Google to get back to' +
' your submissions.'));

  }
  if(continues.length === 0) { continueDiv = makeEmptyContinueDiv(); }
  else {
    continueDiv = 
      DIV(
        P(STRONG("This account has a password, but you can add another if you like.")),
        makeEmptyContinueDiv()
      );
  }

  var pad = {style:{margin:'1em'}};
  var launch = COMMON.urlPrefix + '/paper' + launchKey;
  var link = DIV(pad,H3('Bookmark this link, and visit it directly: '),
                DIV({style:{'margin':'1em'}},A({href:launch},launch)));

  var search = DIV(pad,H3('Save the invitation message.  You can search your inbox for:'),
                  DIV({style:{'text-align':'center', 'margin': '1em'}},
                      STRONG('paper submit request ' + basicInfo.info.name)))
  var accountGoogle = DIV(pad,H3('Associate with a Google account:'),
                            googleDiv);
  var accountContinue = DIV(pad,H3('Create a password:'),
                              continueDiv);

  // "login options for returning to your submissions"
  // "bookmark this link" --> "visit this link directly (don't share it)"
  // "save the INVITATION message"
  return DIV({style:{width:'70%','padding-left':'15%','padding-bottom':'2em'}},
             P('Welcome, ', STRONG(launchInfo.email), '.  ' +
               'You have several options for returning to your submissions:',
               P(),
               UL(
                link,
                search,
                accountGoogle,
                accountContinue)))
}

function paperFrame(paperInfo) {
  return 'subtarget_' + paperInfo.id;
}

function paperContentId(paperInfo) {
  return 'paper_details_' + paperInfo.id;
}

function makeDetailsTab(userInfo,paperInfo,basicInfo,authorText,extensions,errorsB,launchInfo,paperCaps) {
	var deadlineExts = toObj(extensions,function(e) {return e.typeID;});
	var getDeadline = function(compType) {
		if (deadlineExts[compType.id]) return deadlineExts[compType.id].until; else return compType.deadline;
	};
	var getDeadlineStr = function(compType) {
		if (deadlineExts[compType.id]) return deadlineExts[compType.id].untilStr; else return compType.deadlineStr;
	};

  var newUserWidget = function() {
    var dismiss = P(A({href:'javascript://Close', id:'dismiss'}, 'Dismiss'));
    var d = DIV({id: 'new-user-message',
                 style: {
                   border: '1px solid black',
                   'background-color': '#eee',
                   'margin-left': '10%',
                   'margin-right': '10%'
                 }},
                P('Welcome, ' + launchInfo.email + '!'),
                P('Enter information for your submission below.  ' +
                  'For details about managing your account, visit the My ' +
                  'Account tab above'),
                dismiss);
    var msgVisB = extractEvent_e(dismiss, 'click').
                    constant_e('none').startsWith('block');
    insertValueB(msgVisB, d, 'style', 'display');
    return d;
  };

	var makeComponentBox = function(compType,compVal) {
		var deadpara = P({className:'small'},'Deadline: ',
				(((new Date()).getTime()/1000) < getDeadline(compType)) ? 
					getDeadlineStr(compType) : 
					SPAN({className:'error'},'Elapsed: '+getDeadlineStr(compType))
				);
		var submittedpara = (compVal && compVal.value != '') ? 
			P({style:{fontSize:'120%',color:'#00aa00',margin:'0.1em',fontWeight:'bold'}},'Submitted') : P({style:{fontSize:'120%',color:'#aa0000',margin:'0.1em',fontWeight:'bold'}},'Not Yet Submitted');
		if (compType.format == 'Text') {
			return TD(
					submittedpara,
					compVal ? SPAN({className:'small'},'Last modified: ',compVal.lsStr,BR(),BR()) : '',
					TEXTAREA({cols:80,rows:20,name:compType.abbr},(compVal ? compVal.value : '')),
					deadpara
			);
		}
		else {
		    	var cvext = '';
			if(compVal && compVal.value.indexOf('.') != -1)
			    cvext = compVal.value.substr(compVal.value.indexOf('.')+1);
			var slstr = '';
			var sizelimit = compType.sizelimit;
			return TD(
				submittedpara,
				compVal ? P('Current: ',A({'href':'Author/'+compType.id+'.'+cvext+'?cookie='+authCookie},'download'),BR(),
					SPAN({className:'small'},'Last modified: ',compVal.lsStr)) : '',
				[INPUT({type:'file',name:compType.abbr,size:50}),
				(compType.format == 'PDF' ? P({className:'small'},'Use PDF format only.') : ''),
				(compType.sizelimit ? P({className:'small'},'Maximum upload size ',''+compType.sizelimit+' MB') : ''),
				 deadpara]
			);
		}
	}

	var componentValues = toObj(paperInfo.components,function(c) {return c.typeID;});
	var missinginfo = foldR(function(v, acc) {	
			return ((!componentValues[v.id] || componentValues[v.id].value == '') && v.mandatory) ? 
				(getDeadline(v) < ((new Date()).getTime()/1000) ? 
					[P('You must still submit your '+v.description+'. The deadline was:'),P({className:'error'},getDeadlineStr(v))] :
					[P('You must still submit your '+v.description+'. The deadline is:'),P(getDeadlineStr(v))]) : acc;},
			'Submission Complete',basicInfo.components);
	var targetables = fold(function(v, acc) {return v.targetable ? acc+1 : acc;},0,basicInfo.decisions);

	var titleWidget = new TextInputWidget(paperInfo.title,40)
			.belayServerSaving(function(title) {
        return genRequest({fields:{title:title}});
      }, true, paperCaps.setTitle)
			.toTableRow('Paper Title:');
	var authorWidget = new TextInputWidget(paperInfo.author,70)
			.belayServerSaving(function(author) {
        return {fields:{author:author}};
      }, true, paperCaps.setAuthor)
			.toTableRow('Author List:');
	var pcpWidget = new CheckboxWidget(paperInfo.pcpaper)
			.belayServerSaving(function(pcpaper) {
					return {fields:{pcpaper:(pcpaper ? 'yes' : 'no')}};
      }, true, paperCaps.setPcPaper)
			.toTableRow('PC Paper?');
	var twDom = '';
	if(targetables > 1) {
		var targetsel = new SelectWidget(paperInfo.target.id,map(function(dec) {return OPTION({value:dec.id},dec.description);},filter(function (d) {return d.targetable;},basicInfo.decisions)));
		var othercats = new CheckboxWidget(paperInfo.othercats);
		var targetWidget = new CombinedInputWidget([targetsel,othercats],function(tsdom,ocdom) {
							return DIV(tsdom,BR(),ocdom,'Yes, I/we would like the paper considered in other categories also.');
							}).serverSaving(function(to) {
								return {fields:{target:to[0],othercats:(to[1] ? 'yes' : 'no')}};
							}, true, paperCaps.setTarget).toTableRow('Target Category:');
		twDom = targetWidget.dom;
	}
	var topicsWidget = new CheckboxListWidget(map(function(t) {return {k:t.id,v:t.name};},basicInfo.topics),
												map(function(t) {return t.id;},paperInfo.topics))
    .belayServerSaving(function(tids) {	return {fields:{topics:tids}}; },
                true, paperCaps.setTopics)
    .toTableRow('Topic(s):');
	var errorsDomB = errorsB.transform_b(function(e) {if(e.error) return P({className:'error'},e.error); else return SPAN();});
	return DIVB(launchInfo.newUser ? newUserWidget() : '',
		((missinginfo == 'Submission Complete') ? '' : P('Please finish providing information about your submission.')),
		H3('General Information'),
		TABLE({className:'key-value'},TBODY(
			TR(TH('Contact:'),TD(userInfo.fullname,' <',launchInfo.email,'>')),
			basicInfo.info.showNum ? TR(TH('Paper #:'),TD(paperInfo.id)) : '',
			TR(TH('Remaining Components:'),TD({className:(missinginfo == 'Submission Complete' ? 'yes-submitted' : 'normal')},missinginfo)),
				titleWidget.dom,
				authorWidget.dom,
				twDom,
				pcpWidget.dom,
				topicsWidget.dom
		)),
		DIV(paraString(authorText[0],'',80000)),
		H3('Components'),
		(missinginfo == 'Submission Complete' ? P(
			'You have finished your submission. You may update any component until its deadline. If you wish to submit another paper, please ',
			A({href:'login.html'},'create a new author account'),' for the new paper.') : 
			P('You have not yet completed your submission. You may submit or update any component until its deadline.')),
		errorsDomB,
		FORM({target:paperFrame(paperInfo),action:paperCaps.updateComponents.serialize(),method:'post',encoding:'multipart/form-data'},
		INPUT({type:'hidden',name:'cookie',value:authCookie}),
		TABLE({className:'key-value'},TBODY(
			map(function(component) {
				return TR(TH(component.description),TD(makeComponentBox(component,componentValues[component.id])))
			},basicInfo.components))),
		DIV(paraString(authorText[1],'',80000)),
		P({className:'centered'},INPUT({type:'submit',value:'Submit'})))
	);
}
function loader() {
	var flapjax = flapjaxInit();
	demoEventsE = consumer_e();
	document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);});};
  var capServer = new CapServer();
  
	var onLoadTimeE = receiver_e();

  var launchCap = launchCapFromKey(COMMON.urlPrefix, capServer);
  var launchE = getE(onLoadTimeE.constant_e(launchCap));

	var exceptsE = captureServerExcepts();
	handleExcepts(exceptsE);
	var basicInfoE = getE(launchE.transform_e(function(li) {
    return li.getBasic;
  }));
	basicInfoE.transform_e(function(bi) {
		document.title = bi.info.shortname + ' - Paper Submission';
  });
	doConfHead(basicInfoE);
	authCookie = $URL('cookie');
	getObj('logout_tab').href = 'login.html?logout='+authCookie;
	var curUserE = getCurUserE(onLoadTimeE,authCookie);
//	doLoginDivB(curUserE);
	var authorTextE = getE(launchE.transform_e(function(li) {
    return li.getAuthorText;
  }));
  var tabTitle = function(s) {
     return truncate(s === '' ? 'Untitled paper' : s, 15);
  }
 
/*  insertValueB(detailsInfoE.transform_e(function(di) {
    return tabTitle(di.title);
  }).startsWith(''), getObj('main_tab'), 'innerText');
*/
/*  launchE.transform_e(function(di) {
    map(function(op) {
      insertDomB(LI({className:'left-tab'},
        A({href:op.launch.launchbase + '#' + op.launch.launchcap,
           className: di.title === op.title ? 'selected' : ''},
           tabTitle(op.title, 15))), 'tab_list', 'end');
    }, di.otherPapers);
  });
*/

  papersE = launchE.transform_e(function(di) {
    return di.papers;
  });
  launchE.transform_e(function(di) {
    var newE = postE(extractEvent_e('new_submission', 'click').transform_e(function() {
      return [di.addPaper, {}];
    }));
    newE.transform_e(function(newPaper) {
      window.location.href = newPaper.launch.launchbase + '#' + 
        newPaper.launch.launchcap;
      window.location.reload();
    });
  });

  var accountTabB = lift_b(function(li, bi) {
    if(li && bi) return makeAccountInfoTab(li, bi, window.name);
    return SPAN();
  }, launchE.startsWith(null), basicInfoE.startsWith(null));

  function one_e(val) {
    var r = receiver_e();
    setTimeout(function() { r.sendEvent(val); }, 0);
    return r;
  }

  lift_e(function(cu, bi, papers, le) {
    if(!(le && bi && papers)) return;
    var paperDomId = function(paper) { return 'paper_tab_' + paper.id; };
    var paperDom = function(paper) {
      var detailsQueryE = one_e(paper.getPaper);
      var loadFrame = IFRAME({
        id:paperFrame(paper),
        name:paperFrame(paper),
        style: {display:'none'},
      });
      insertDomB(loadFrame, getObj(document.body), 'end');
      var deadextE = getE(one_e(paper.getDeadlineExtensions));
      var perE = iframeLoad_e(paperFrame(paper));
      var perB = perE.startsWith(true);
      var allDetailsQuerysE = merge_e(snapshot_e(perE,detailsQueryE.startsWith(null)),detailsQueryE);
      var detailsInfoE = getE(allDetailsQuerysE);
      var detailsTabB = lift_b(function(di,at,de) {
          if (di && at && de) {
            var visibility = di.title === le.mainTitle ? 'block' : 'none';
            return makeDetailsTab(cu,di,bi,at,de,perB,le,paper); 
          }
          else {
            return constant_b(getLoadingDiv(paperContentId(paper)));
          }
        },
        detailsInfoE.startsWith(null),authorTextE.startsWith(null),deadextE.startsWith(null)); 


      var tab = LI({className:'left-tab'},
        A({
            href:'javascript://Switch',
            className: 'writer-tab',
            id: paperDomId(paper)
          },
          tabTitle(paper.title, 15)));

      var detailsContentB = DIVB({
          id: paperContentId(paper)
        },
        switch_b(detailsTabB));
      return {
        tab: tab,
        details: detailsContentB
      };
    };
    var startPaper = filter(function(paper) {
      return paper.title === le.mainTitle;
    }, papers)[0];
    var otherPapers = filter(function(paper) {
      return paper !== startPaper;
    }, papers);

    map(function(paper) {
      var pDom = paperDom(paper)
      insertDomB(pDom.tab, 'tab_list', 'end');
      insertDomB(pDom.details, 'content', 'end');
    }, papers);

    var WriterTabs = new TabSet(
      constant_b(['user']),
      {admin:[],reviewer:[],user:$$('writer-tab'),logged_out:[]},
      function(that) {
        var tabClicksE = map(function(tab) {
          return extractEvent_e(tab, 'click').constant_e(tab.id);
        }, that.allTabs);
        return merge_e.apply(this, tabClicksE).
          startsWith(paperDomId(startPaper));
      }
    );
    WriterTabs.displayOn('account_tab', 'account_content');
    map(function(paper) {
      WriterTabs.displayOn(paperDomId(paper), paperContentId(paper));
    }, papers);
  }, curUserE, basicInfoE, papersE, launchE);

	insertDomB(accountTabB,'account_placeholder');
	onLoadTimeE.sendEvent('loaded!');
}

