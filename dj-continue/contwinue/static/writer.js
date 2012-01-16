
function paperFrame(paperInfo) {
  return 'subtarget_' + paperInfo.id;
}

function paperContentId(paperInfo) {
  return 'paper_details_' + paperInfo.id;
}
function paperDomId(paper) {
  return 'paper_tab_' + paper.id;
}
function tabTitle(s) {
   return truncate(s === '' ? 'Untitled paper' : s, 15);
}

function makeDetailsTab(paperInfo,basicInfo,authorText,extensions,errorsB,launchInfo,paperCaps) {
	var deadlineExts = toObj(extensions,function(e) {return e.typeID;});
	var getDeadline = function(compType) {
		if (deadlineExts[compType.id]) return deadlineExts[compType.id].until; else return compType.deadline;
	};
	var getDeadlineStr = function(compType) {
		if (deadlineExts[compType.id]) return deadlineExts[compType.id].untilStr; else return compType.deadlineStr;
	};

  var userNameB = new TextInputWidget(paperInfo.thisAuthor.name, 40).
    belayServerSaving(function(input) {
      return genRequest({fields:{name:input}})
    }, false, launchInfo.updateName).
    toTableRow('Your Name:');

  var updatedNameE = userNameB.events.serverResponse.transform_e(function(r) {
    return r.name;
  });
  var updatedNameB = updatedNameE.startsWith(paperInfo.thisAuthor.name);
  var contactName = paperCaps.paperContactName;
  var contactEmail = paperCaps.paperContactEmail;
  var contactNameB = updatedNameE.transform_e(function(name) {
    if(launchInfo.email === contactEmail) {
      return name;
    }
    else {
      return contactEmail;
    }
  }).startsWith(contactName);

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
			var slstr = '';
			var sizelimit = compType.sizelimit;
			return TD(
				submittedpara,
				compVal ? P('Current: ',A({'href':compVal.getComponent.serialize(), target: '_blank'},'download'),BR(),
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

  var titleB = titleWidget.events.serverResponse.transform_e(function(r) {
    return r.title;
  }).startsWith(paperInfo.title);

  insertValueB(lift_b(function(value) {
    var ret;
    if(typeof value === 'string') ret = value;
    else if(typeof value === 'object') ret = value.title;
    return tabTitle(ret);
  }, titleWidget.behaviors.value), paperDomId(paperInfo), 'innerText');

  paperInfo.authors.push({
    name: updatedNameB,
    email: launchInfo.email,
    added: true,
    remove: null
  });
  var authorsErrors = P({style: {color: 'red'}}, BR());
  var authorsWidget = new ModListWidget(
    paperInfo.unverifiedAuthors.concat(paperInfo.authors),
    TR(TH('Name'), TH('Email')),
    function(unverified) {
      var ret = new ButtonInputWidget([],
        {del: unverified.remove === null ? new ClickWidget(SPAN(),null) : new LinkWidget('Remove')},
        function() { return unverified; },
        function(_,delobj) {
          return TRB(TDB(unverified.name), TD(unverified.email), delobj.del);
        });
      ret.events.del = postE(ret.events.del.transform_e(function() {
        return [unverified.remove, {}]
      }));
      return ret
    },
    function() {
      var adder = new ButtonInputWidget(
        [new TextInputWidget('',30),
         new TextInputWidget('',30)],
        {value: new ButtonWidget('Add')},
        function(name, email) {
          return {name: name, email: email};
        },
        function(inputs, attrs) {
          return TR(TD(inputs[0]), TD(inputs[1]), TD(attrs.value));
        }).
        belayServerSaving(function(author) {
          return {fields:{name:author.name, email:author.email}}; 
        }, true, paperCaps.addAuthor);
      var authorResponses = adder.events.serverResponse;
      var errors = authorResponses.filter_e(function(r) {
        return r.error;
      });
      insertValueE(errors.constant_e('block'), authorsErrors,
          'style', 'display');
      insertValueE(errors.transform_e(function(r) {
        setTimeout(function() { $(authorsErrors).fadeOut(3000); }, 1000);
        return r.message;
      }), authorsErrors, 'innerText');
      return adder;
    });


  var hasTitleAndNameB = lift_b(function(name, title) {
    return name !== '' && title !== '';
  }, updatedNameB, titleB);

  var authorsRow = TRB(
    TH('Authors'),
    TDB(PB({
      style:{
       'font-style':'italic'
      }},
      'Adding an author will send them a message with a link to edit this paper.', 
      SPANB({
        style: {
          display: hasTitleAndNameB.lift_b(function(tn) {
            return !tn ? 'block' : 'none'
          })
        }}, '  To add authors, make sure you\'ve entered your name and a title for the paper.')),
    DIVB({
        style: {
          display: hasTitleAndNameB.lift_b(function(tn) { 
            return tn ? 'table-row' : 'none';
          })
        }
      },
      authorsWidget.dom),
      authorsErrors));
    
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
		TABLEB({className:'key-value'},TBODYB(
      userNameB.dom,
			TRB(TH('Paper Contact:'),TDB(contactNameB,' <',paperCaps.paperContactEmail,'>')),
			basicInfo.info.showNum ? TR(TH('Paper #:'),TD(paperInfo.id)) : '',
			TR(TH('Remaining Components:'),TD({className:(missinginfo == 'Submission Complete' ? 'yes-submitted' : 'normal')},missinginfo)),
				titleWidget.dom,
        authorsRow,
				twDom,
				pcpWidget.dom,
				topicsWidget.dom
		)),
		DIV(paraString(authorText[0],'',80000)),
		H3('Components'),
		(missinginfo == 'Submission Complete' ?
       P('You have finished your submission. You may update any component until its deadline.')
     : P('You have not yet completed your submission. You may submit or update any component until its deadline.  Note that to submit, you must click the Submit button at the bottom of the page.')),
		errorsDomB,
		FORM({target:paperFrame(paperInfo),action:paperCaps.updateComponents.serialize(),method:'post',encoding:'multipart/form-data'},
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
	extractEvent_e('logout_tab', 'click').transform_e(function(_) {
    window.name = "";
  });
  insertValueE(basicInfoE.transform_e(function(bi) {
    return bi.info.shortname + '/home';
  }),'logout_tab', 'href');
	var authorTextE = getE(launchE.transform_e(function(li) {
    return li.getAuthorText;
  }));
 
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
    var newPaperDiv = DIV({
        style: {
          'max-width': '30em',
          'float': 'right',
          'position': 'absolute',
          'right': '5em',
          'border': '2px solid black',
          'background-color': 'white',
          'padding': '1em'
        }
      },
      A({id:'closenew',style:{float:'right',width:'1em','text-align':'center'},href:'javascript://Close'}, 'X'),
      P(STRONG({'padding-right': '1em'}, 'Enter the new paper\'s title (you can change it later):')),
      INPUT({id:'newtitle', 'height': '3em', size: '50', type:'text'}),
      BR(),
      INPUT({id: 'submitnew', 'height': '3em', size: '50', type:'button', value:'Submit'})
    );
    insertDomB(newPaperDiv, 'tab_list', 'after');
    var subClicksE = extractEvent_e('new_submission', 'click').transform_e(function() {
      // TODO(joe): how to do this with flapjax?  focusing before it shows
      // up doesn't work, so i use this dirty hack to do it on the next turn
      setTimeout(function() { getObj('newtitle').focus(); }, 0);
      return 'block';
    });
    var closeClicksE = extractEvent_e('closenew', 'click').transform_e(function() {
      return 'none';
    });
    insertValueB(merge_e(subClicksE, closeClicksE).startsWith('none'),
                  newPaperDiv, 'style', 'display')

    var submitPaperE = extractEvent_e('submitnew', 'click').merge_e(
      extractEvent_e('newtitle', 'keypress').filter_e(function(v) {
        return v.keyCode === 13;
      }));
    insertValueB(submitPaperE.constant_e(true).startsWith(false),
      'newtitle', 'disabled');
    insertValueB(submitPaperE.constant_e(true).startsWith(false),
      'submitnew', 'disabled');
    var postDataE = submitPaperE.transform_e(function(_) {
      return [di.addPaper, {title: getObj('newtitle').value}];
    });
    var newE = postE(postDataE);
    newE.transform_e(function(newPaper) {
      window.location.href = newPaper.launch.launchbase + '#' + 
        newPaper.launch.launchcap;
      window.location.reload();
    });
  });

  var accountTabB = lift_b(function(li, bi) {
    if(li && bi) {
      var searchString = 'paper submit request ' + bi.info.name;
      return makeAccountInfoTab(
        li,
        searchString,
        COMMON.urlPrefix + '/paper' + window.name
      );
    }
    return SPANB();
  }, launchE.startsWith(null), basicInfoE.startsWith(null));

  function one_e(val) {
    var r = receiver_e();
    setTimeout(function() { r.sendEvent(val); }, 0);
    return r;
  }

  lift_e(function(bi, papers, le) {
    if(!(le && bi && papers)) return;
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
            return makeDetailsTab(di,bi,at,de,perB,le,paper); 
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
  }, basicInfoE, papersE, launchE);

	insertDomB(switch_b(accountTabB),'account_placeholder');
	onLoadTimeE.sendEvent('loaded!');

}

