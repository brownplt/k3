function SSRWidget(underlyings,lastSaved,domFn,saveFn,submitFn,savetime,revert,topToo, saveButton) {
	var me = this;
	Widget.apply(this);
	this.inputElems = [];
	var bottomSaveButton = saveButton ? new ButtonWidget('Save Now','save') : SPAN();
	var bottomSubmitButton = new ButtonWidget('Submit','submit');
	this.events.revert = receiver_e();
  this.events.save = zero_e();
	if(revert)
		var bottomRevertButton = new ButtonWidget('Revert','revert');
	if(topToo) {
		var topSaveButton = saveButton ? new ButtonWidget('Save Now','save') : SPAN();
    if (saveButton)
      this.events.save = merge_e(topSaveButton.events.click,bottomSaveButton.events.click);
		var topSubmitButton = new ButtonWidget('Submit','submit');
		this.events.submit = merge_e(topSubmitButton.events.click,bottomSubmitButton.events.click);
		if(revert) {
			var topRevertButton = new ButtonWidget('Revert','revert');
			this.events.revert = merge_e(topRevertButton.events.click,bottomRevertButton.events.click);
		}
	}
	else {
    if (saveButton)
      this.events.save = bottomSaveButton.events.click;
		this.events.submit = bottomSubmitButton.events.click;
		if(revert)
			this.events.revert = bottomRevertButton.events.click;
	}
	this.behaviors.value = lift_b.apply({},[function() {return slice(arguments,0);}].concat(map(function(w) {return w.behaviors.value;},underlyings)));
	this.events.submitted = submitFn(snapshot_e(this.events.submit,this.behaviors.value));
	this.events.saved = merge_e(saveFn(snapshot_e(merge_e(this.events.save,timer_e(savetime)),this.behaviors.value).filterRepeats_e().filter_e(id)),this.events.submitted);
	this.behaviors.lastSaved = this.events.saved.transform_e(function(_) {return new Date()}).startsWith(new Date(lastSaved*1000));
	this.behaviors.unsaved = merge_e(this.events.saved.constant_e(false),this.behaviors.value.changes().constant_e(true)).startsWith(false);

	var genStDom = function(us,ls) {
			var usd = '';
			if(us) usd = SPAN({'font-style': 'italic', 'color': 'gray'},
                        '(Saving draft...)');
			var lsstr = ls.getTime() > 0 ? 'Last Draft Saved '+ls.toLocaleString() : 'No draft saved yet.'
			return DIV({align:'center', 'font-size': 'small'},lsstr,' ',usd);
	};
	var bottomStatusB = lift_b(genStDom,this.behaviors.unsaved,this.behaviors.lastSaved);
	var bottomDomB = DIVB({className:'form-buttons'},
			bottomStatusB,BR(),
			bottomSaveButton.dom,
			revert ? bottomRevertButton.dom : '',
			bottomSubmitButton.dom);
	if(topToo) {
		var topStatusB = lift_b(genStDom,this.behaviors.unsaved,this.behaviors.lastSaved);
		var topDomB = DIVB({className:'form-buttons'},
				topStatusB,BR(),
				topSaveButton.dom,
				revert ? bottomRevertButton.dom : '',
				topSubmitButton.dom);
	}

	map(function(w) {
		w.greyOutable(
			merge_e(
				me.events.saved.constant_e(false),
				w.behaviors.value.changes().constant_e(true)
			).startsWith(false));
		me.inputElems = me.inputElems.concat(w.inputElems);},underlyings);

	this.dom = domFn.apply({},(topToo ? [topDomB,bottomDomB] : [bottomDomB]).concat(map(function(w) {return w.dom;},underlyings)));
}
inheritFrom(SSRWidget,InputWidget)

function PaperView(paperInfo,curUser,basicInfo,caps) {
	this.paper = paperInfo;
	this.user = curUser;
	this.basicInfo = basicInfo;
	this.header = DIV(
			basicInfo.info.useDS ? 
				DIV({className:'summary-box o'+this.paper.oscore},'/') :
				DIV({className:'summary-box '+this.paper.reviewStats.reviewRange},this.paper.reviewStats.reviewRange),
			H2('#'+this.paper.id+': '+this.paper.title+(this.paper.pcpaper?' (PC Paper)':'')),
			H4(this.paper.author));

	var that = this;

	this.getInfoTable = function(isReview) {
		var textTRs = [];
		map(function(component) {
			var ctype = fold(function(v, acc) {
        return acc ? acc : (v.id == component.typeID ? v : false);
      }, false, basicInfo.components);
			if(ctype.format == 'Text')  {
				var ohdom = TH();
				var oddom = TD();
				var showhide = new ToggleWidget('Hide '+ctype.description,'Show '+ctype.description);
				var textdv = paraString(component.value,'pre');
				insertDomB(
					showhide.behaviors.toggled.transform_b(function(_) {return _ ? DIV({className:'pre'},' ') : textdv;}),
					oddom,'beginning');
				insertDomB(showhide.dom,ohdom,'beginning');
				textTRs.push(TR(ohdom,oddom));
			}
			else
				return '';
			},this.paper.components);
    var componentsDict = {};
    map(function(c) { componentsDict[c.typeID] = c; }, this.paper.components);

    var hiddenTRs = [];
    var self = this;
    map(function(ctype) {
        var ohdom = TH();
        var oddom = TD();
        var showhide = new ToggleWidget('Hide '+ctype.description,'Show '+ctype.description);
        var textdv = paraString('You do not have permission to see ' +
          'this paper\'s ' + ctype.description + '  You may request ' +
          'access by clicking below, and a PC member will grant your ' +
          'request if appropriate.', 'pre');
        var grantbutton = BUTTON();
        var postedE = postE(extractEvent_e(grantbutton, 'click').
          transform_e(function(_) {
            return [caps.requestComponents[ctype.id], {}];
          }));
        var requestedB = postedE.
          startsWith(ctype.id in self.paper.grants);
        var textB = requestedB.lift_b(function(r) {
          return r ? 'Access Requested' : 'Request Access';
        });
        insertValueB(requestedB, grantbutton, 'disabled');
        insertDomB(textB, grantbutton, 'end');

        var requestDiv = DIVB(textdv, grantbutton);
        insertDomB(
          switch_b(showhide.behaviors.toggled.transform_b(function(_) {return _ ?
DIVB({className:'pre'},' ') : requestDiv;})),
          oddom,
          'beginning');
        insertDomB(showhide.dom,ohdom,'beginning');
        if (caps.requestComponents[ctype.id] && !componentsDict[ctype.id]) {
          textTRs.push(TR(ohdom,oddom));
        }
    }, filter(function(_) { return _.protected; }, basicInfo.components));


		var decsel;
		if(inList('admin',this.user.rolenames)) {
			var dsw = new SelectWidget(that.paper.decision.id, 
					map(function(de) {return OPTION({value:de.id},de.description); }, that.basicInfo.decisions));
			var chdec = postE(dsw.behaviors.value.changes().transform_e(function(dec) {
				return [caps.updateDecision, {decision:dec}];
      }));
			decsel = dsw.greyOutable(merge_e(dsw.behaviors.value.changes().constant_e(true),chdec.constant_e(false)).startsWith(false)).dom;
		}
		else
			decsel = this.paper.decision.description;

		var biddom = (this.basicInfo.info.showBid && inList('reviewer',this.user.rolenames) && this.paper.bids) ? 
			TR(TH('Your Bid:'),TD(
						new SelectWidget(
							fold(function(v, acc) {return v.bidderID == that.user.id ? v.valueID : acc;},that.basicInfo.info.defaultBidID,that.paper.bids),
							map(function(bv) {return OPTION({value:bv.id},bv.abbr + ' - '+bv.description);},that.basicInfo.bids)).
              belayServerSaving(function(bidid) {
								return genRequest({fields:{bid:bidid,papers:that.paper.id}});
              }, false, caps.updateBids).dom)) : '';

		var targetables = fold(function(v, acc) {return v.targetable ? acc+1 : acc;},0,basicInfo.decisions);

		return TABLE({className:'key-value'},TBODY(
			targetables >1 ? TR(TH('Target Category: '),TD(P(this.paper.target.description,'; ',
				(this.paper.othercats ?
					['but the author ',STRONG('DOES')] :
					['and the author ',STRONG('DOES NOT')]),
				' want this submission considered for other categories.'))) : '',
			TR(TH('Decision: '),TD(decsel)),
			TR(TH('Topics: '),TD(fold(function(v, acc) {return acc ? acc+ '; '+v.name : v.name;},null,this.paper.topics))),
			inList('admin',this.user.rolenames) ? TR(TH('Email: '),TD(this.paper.contact.email)) : '',
			map(function(component) {
				var ctype = fold(function(v, acc) {return acc ? acc : (v.id == component.typeID ? v : false);},false,basicInfo.components);
				if (ctype.format != 'Text') {
					return TR(TH(ctype.description,':'),TD(A({target:'_blank',
            href:caps.getComponents[component.id].serialize()},'Download')));
				}
				else
					return '';
				},this.paper.components),
			textTRs,
			biddom,
			TR(TH('Reviews: ',BR(),
					(this.paper.reviews?
						A({href:'mailto:'+
							map(function(review) {return review.reviewer.email;},this.paper.reviews).join(',')},'(Email Reviewers)') :
						'')),
				TD(this.paper.reviews ? map(function(review) {
					return SPAN(review.submitted ? 
						(isReview ? 
							A({href:'#'+review.id},review.reviewer.fullname + ' (' + review.overall.abbr + '/' + review.expertise.abbr + ')') :
							(review.reviewer.fullname + ' (' + review.overall.abbr + '/' + review.expertise.abbr + ')')) : 
						SPAN({className:'unfinished-review'},review.reviewer.fullname),
						BR());
				},this.paper.reviews) : 'Assigned for your review.'))
		));
	};
	this.getAssignDom = function(usersInfo,nextIdB) {
		var allusers = {};
    console.log('assign-domming');
		var usersByBid = {};
		var that = this;
		map(function(b) {
			usersByBid[b.id] = [];
		},this.basicInfo.bids);
		map(function(u) {
			allusers[u.id] = u;
			allusers[u.id].bid = that.basicInfo.info.defaultBidID;
			allusers[u.id].reviewing = false;
			allusers[u.id].submitted = false;
		}, usersInfo);
		map(function(b) {
			if (allusers[b.bidderID])
				allusers[b.bidderID].bid = b.valueID;
		}, this.paper.bids);
		map(function(r) {
			allusers[r.reviewer.id].reviewing = true;
			if(r.submitted) allusers[r.reviewer.id].submitted = true;
		}, this.paper.reviews ? this.paper.reviews : []);
		map(function(u) {
			usersByBid[u.bid].push(u);
		}, usersInfo);
			

		var saveBtn = INPUT({type:'submit',value:'Save'});
		var saveAdvB = nextIdB.transform_b(function(nID) {return INPUT({disabled:(nID==0),type:'submit',value:'Save and Advance'});});
		var saveAdvClicksE = switch_b(saveAdvB.transform_b(function(_) {return extractEvent_e(_,'click').constant_e(true).startsWith(false);})).changes();
		var AdvanceB = merge_e(extractEvent_e(saveBtn,'click').constant_e(false),saveAdvClicksE).startsWith(false);

		var advanceToE = snapshot_e(
				iframeLoad_e('astarget'),
				lift_b(function(adv,next) {return (adv ? next : 0);},AdvanceB,nextIdB)
			).filter_e(function(_) {return _ !== 0;});
		advanceToE.transform_e(function(next) {
			var redirect = 'paperview?id='+next.id+'&mode=paper_assign_tab&tab='+$URL('tab')+
            "#" + next.cap;
      window.location = redirect;
    });

		return DIVB(
			this.getInfoTable(false),
			FORMB({target:'astarget',action:caps.assignReviewers.serialize(),method:'post'},
				INPUT({type:'hidden',name:'cookie',value:authCookie}),
				map(function(bt) {
					if (bt.abbr == 'V' || usersByBid[bt.id].length == 0)
						return '';
					else return DIV(H3('"'+bt.abbr+'. '+bt.description+'"'),DIV({className:'checkbox-grid'},
						map(function(u) {
							return DIV({className:'checkbox-pair'},
								INPUT({type:'checkbox',checked:u.reviewing,name:'assign',value:u.id}),
								LABEL(u.submitted?'*':'',u.fullname,(u.reviewCount ? ' ['+u.reviewCount+']' : '')));
							},usersByBid[bt.id]),BR()));
				},this.basicInfo.bids),
				P({className:'form-note'},
					 '* = submitted review already',BR(),
					'Numbers in brackets tally the assignments of each reviewer. Reviewers with a conflict of interest are not listed.'),
				DIVB({className:'form-buttons'},saveBtn,saveAdvB)
  		)
		);
	}
	this.getReviewFormDom = function(userReviewInfo,revertE) {
		var userReview = userReviewInfo.review;

		var ctypes = toObj(userReview.components,function(rc) {return rc.typeID;});
	
		var ctas = map(function(rc) {
				var cta = new InputWidget(TEXTAREA({name:'comp-'+rc.id,cols:80,rows:15},(ctypes[rc.id] ? ctypes[rc.id].value : '')));
				cta.behaviors.value = cta.behaviors.value.transform_b(function(v) {return {id:rc.id,value:v};});
				return cta;
			},this.basicInfo.rcomponents);
		var overallBox = new SelectWidget(userReview.overall.id,
			map(function(r) {
				return OPTION({value:r.id},r.abbr+'. '+r.description);
			}, this.basicInfo.ratings));
		var expertiseBox = new SelectWidget(userReview.expertise.id,
			map(function(r) {
				return OPTION({value:r.id},r.abbr+'. '+r.description);
			}, this.basicInfo.expertises));
		var srBox = new InputWidget(TEXTAREA({name:'subreviewer',rows:3,cols:36,value:userReview.subreviewers}));

		var genSaveReq = function(ctaVals,ov,ex,subrev,submit) {
			var flds = {};
			map(function(ctav) {flds['comp-'+ctav.id] = ctav.value;},ctaVals);
			flds.overallrating = ov;
			flds.expertiserating = ex;
			flds.subreviewer = subrev;
			flds.submit = (submit ? 'yes' : 'no');
			flds.cookie = authCookie;
			return [caps.saveReview, flds];
		};

		var revForm = new SSRWidget([overallBox,expertiseBox,srBox].concat(ctas),
			userReview.lastSaved,
			function(topStDom,btmStDom,ov,ex,sr) {
				var ctadoms = slice(arguments,5);
				var i=-1;
				return DIVB(
					that.getInfoTable(false),
					HR(),BR(),
					topStDom,
					H3('Scores'),
					DIV({className:'form-inputs'},
						LABEL({className:'key'},'Overall Review'),ov,BR(),
						LABEL({className:'key'}, 'Expertise'),ex),
					BR({clear:'both'}),
					map(function(cta) {i++; return DIV({className:'recvomp'},H3(LABEL(basicInfo.rcomponents[i].description)),cta);},ctadoms),
					DIV({className:'revcomp'},
						H3('Sub-Reviewer Information'),
						SPAN('Please list sub-reviewers one to a line, with last name first.  E.g.:'),
						BLOCKQUOTE({align:'center'},'Pollack, Jackson',BR(),'van der Goes, Hugo'),
						DIV({className:'form-inputs'},LABEL({className:'key'},'Subreviewer(s)'),sr)),
					BR({clear:'both'}),
					btmStDom);
			},
			function(saveE) {
				return postE(saveE.transform_e(function(vals) {
					return genSaveReq(slice(vals,3),vals[0],vals[1],vals[2],false);
				}));
			},
			function(submitE) {
				return postE(submitE.transform_e(function(vals) {
					return genSaveReq(slice(vals,3),vals[0],vals[1],vals[2],true);
				}).filter_e(function(rq) {
					var problems = '';
					if(rq[1].overallrating == that.basicInfo.info.defaultOverallID)
						problems += 'You have not set a valid rating for the paper.\n' 
					if(rq[1].expertiserating == that.basicInfo.info.defaultExpertiseID)
						problems += 'You have not rated your expertise for this paper.\n'
					var vs = false;
					map(function(bc) {
						if(!bc.pconly && rq[1]['comp-'+bc.id].length < 100 && !vs) {
							vs = true;
							problems += 'You have entered a very short review.\n'
						}
					},basicInfo.rcomponents);
					if(problems != '')
						return window.confirm('There are a few possible issues with your review:\n\n'+problems+'\nAre you sure you want to submit it?');
					else
						return true;
				}));
			},30000,(userReviewInfo.hasPublished),true);
		revForm.events.submitted.transform_e(function(_) {
      window.location.reload();
//			window.location = 'continue.html?cookie='+authCookie+'&tab='+$URL('tab');
		});
		revertE.add_e(revForm.events.revert);
		demoEventsE.add_e(revForm.behaviors.value.changes().transform_e(function(_) {return {action:'reviewchanged'};}));
		return revForm.dom;
	};
	this.getCommentFormDom = function(userCommentInfo,revertE,csubmitE) {
    var comment = !!userCommentInfo.comment;
		var valueWidget = new InputWidget(TEXTAREA({cols:80,rows:15,value:(comment ? userCommentInfo.comment.value : '')}));
		var comForm = new SSRWidget([valueWidget],
				(comment ? userCommentInfo.comment.lastSaved : 0),
				function(statusDom,valueDom) {
					return DIVB(
						H4('Enter Comment'),
						DIV({className:'form-inputs'},valueDom),
						statusDom);
				},
				function(saveE) {return postE(saveE.transform_e(function(vals) {
						return [caps.draftComment, {draft:vals[0]}];
				}));},
				function(submitE) {return postE(
					submitE.filter_e(function(vals) {
						if(vals[0] == '') {
							window.alert('You cannot submit an empty comment. Please enter a comment and then submit again.');
							return false;
						}
						return true;})
					.transform_e(function(vals) {
						return [caps.postComment, {value:vals[0]}];
				}));},
				3000,false,false);
		revertE.add_e(comForm.events.revert);
		csubmitE.add_e(comForm.events.submitted);
		return DIVB(PB(comForm.dom));
	};
	this.getReviewsDom = function() {
		return DIV(
			this.getInfoTable(true),
			this.paper.reviews ? map(function(review) {
				var pctypes = toObj(review.components,function(rc) {return rc.typeID;});
				return review.submitted ? DIV(
					A({name:review.id}),
					H3(review.reviewer.fullname),
					TABLE({className:'key-value'},
						TBODY(
							TR(TH('Overall:'),TD(review.overall.abbr+'. '+review.overall.description)),
							TR(TH('Expertise:'),TD(review.expertise.abbr+'. '+review.expertise.description)),
							map(function(ctype) {
								return pctypes[ctype.id] ?
									TR(TH(ctype.description),TD(paraString(pctypes[ctype.id].value,'pre'))) : '';
								},basicInfo.rcomponents),
							review.subreviewers != '' ? TR(TH('Subreviewers:'),TD(paraString(review.subreviewers,'pre'))) : ''))) : '';
			},this.paper.reviews) : '',
      DIV({style:{'padding-bottom': '2em'}},HR(),H3('Comments'),
        this.paper.comments.length ? 
          TABLE({className:'key-value'},
            TBODY(
              map(function(comment) {
                return DIV({className:'comment'},
                            SPAN(STRONG(comment.submitterName), ' says...'),
                            SPAN({className:'commentdate'},
                                 ' (' + comment.postedString + ')'),
                       P(paraString(comment.value,'pre')));
              },this.paper.comments)
            )) : P('(No comments for this paper yet)'))
		);
	};
	this.getOptDom = function(extensions) {
		hidecb = INPUT({type:'checkbox',checked:(that.paper.hidden)});
		postE($B(hidecb).changes().transform_e(function(_) {
				return [caps.setHidden, {hidden: _ ? 'yes':'no'}];
		}));

		var extns = toObj(extensions,function(e) {return e.typeID;});

		return DIV(
			H3('Hide/Show Paper'),
			P('Hide Paper? ',hidecb),
			P('When a paper is hidden, it will disappear from all lists of papers, but will still be accessible from the "Goto.." tab.'),
			H3('Deadline Extensions'),
			P('Components whose names are shown in red have already had their deadlines extended.'),
			TABLE({className:'key-value'},TBODY(
				TR(TH('Component'),TH('Deadline'),TH()),
				map(function(ct) {
					var deadw = new DateWidget(extns[ct.id]?extns[ct.id].until:ct.deadline);
					var okb = INPUT({type:'button',value:'Grant Extension'});
					var setE = postE(snapshot_e(extractEvent_e(okb,'click'),deadw.behaviors.value).transform_e(function(nd) {
						return [caps.setDeadline, {typeid:ct.id,until:nd}];
					}));
					var greyB = merge_e(extractEvent_e(okb,'click').constant_e(true),setE.constant_e(false)).startsWith(false);
					deadw = deadw.greyOutable(greyB);
					return TR(TD({style:{color:extns[ct.id]?'#f00':'#000'}},ct.description),
							  TD(deadw.dom),
							  TD(okb));
				},basicInfo.components)
			))
		);
	}
}

function setPaperContent(currentTabB,paperInfoB,curUserB,basicInfoB,usersInfoB,extensionsB,userReviewB,userCommentB,nextIdB,revertE,commentRevertE,commentSubmitE,
capsB) {
	var currentObjB = lift_b(function(paperInfo,curUser,basicInfo,caps) {
		if (paperInfo == null || curUser == null || basicInfo == null ||
        caps == null)
			return null;
		else {
			return new PaperView(paperInfo, curUser, basicInfo, caps);
		}
	},paperInfoB, curUserB, basicInfoB, capsB);

	var currentDomB = switch_b(currentTabB.transform_b(function(tab) {
		switch(tab) {
			case 'paper_assign_tab':
				return switch_b(lift_b(function(o, u) {
          console.log('assign-tabbing: ', o, u);
          return (o && u) ? o.getAssignDom(u,nextIdB) : DIVB();}, currentObjB, usersInfoB));
			case 'paper_info_tab':
				return switch_b(lift_b(function(o, c) {return o ?
            DIVB(o.getReviewsDom(),
                o.getCommentFormDom(c,commentRevertE,commentSubmitE))
          : DIVB();
        }, currentObjB, userCommentB));
			case 'paper_review_form_tab':
				return switch_b(lift_b(function(o,r) {return (o && r) ? o.getReviewFormDom(r,revertE) : DIV()},currentObjB,userReviewB));
			case 'paper_options_tab':
				return lift_b(function(o,e) {return (o && e) ? o.getOptDom(e) : DIV()},currentObjB,extensionsB);
			default:
				return lift_b(function(_) {return DIV()}, constant_b(true)); 
		}
	}));
	insertDomB(currentObjB.transform_b(function(o) {return o ? o.header : DIV()}),'paperhead');
	insertDomB(currentDomB,'paper_content','beginning');
}

function loader() {
	var flapjax = flapjaxInit();
	demoEventsE = consumer_e();
	document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);});};

  var capServer = new CapServer();
	authCookie = $URL('cookie');
	var onLoadTimeE = receiver_e();
	var exceptsE = captureServerExcepts();
	handleExcepts(exceptsE);
	paperReloadsE = consumer_e();
	paperReloadsE.add_e(iframeLoad_e('astarget'));
  var launchCap = launchCapFromKey(COMMON.urlPrefix, capServer);
  var launchE = getE(onLoadTimeE.constant_e(launchCap));
	var basicInfoE = getFieldE(launchE, 'basicInfo');
	doConfHead(basicInfoE);
	var curUserE = getFieldE(launchE, 'currentUser');

  var paperCapsE = getFieldE(launchE, 'paperCaps');

	var paperInfoE = getE(merge_e(launchE,paperReloadsE).snapshot_e(
    getFieldE(paperCapsE, 'getPaper').startsWith(null)).filter_e(function(_) { 
      console.log('Paper: ', _);
      return _; })).
	  transform_e(function(paper) {paper.reviewStats = getReviewStats(paper.reviews); return paper;});

	var revertE = consumer_e();
	var userReviewE = merge_e(
		getE(getFieldE(paperCapsE, 'getReview').filter_e(function(_) { return _; })),
		postE(revertE.snapshot_e(getFieldE(paperCapsE,'revertReview').startsWith(null)).
      filter_e(function(_) { return _; }).
      transform_e(function(c) { return [c,{}]; })).
			filter_e(function(_) {
				return window.confirm('Are you sure you want to revert to your last published review? Anything you have entered since will be lost!');}
			),
    getFieldE(paperCapsE, 'getReview').filter_e(function(_) { 
      return typeof _ === 'undefined';
    }).constant_e(false)
	);
	var commentRevertE = consumer_e();
	var commentSubmitE = consumer_e();
	paperReloadsE.add_e(commentSubmitE);
  var userCommentB = merge_e(
    commentSubmitE.constant_e(""),
    getFieldE(launchE, 'commentDraft')
  ).startsWith(false);
/*	var userCommentB = getFilteredWSO_e(merge_e(
		merge_e(userReviewE.filter_e(function(ur) {return !ur;}),commentSubmitE)
		.constant_e(
			genRequest(
				{url: 'Paper/'+$URL('id')+'/Comment/get',
				fields: {cookie:authCookie},
				asynchronous: false})
		),
		commentRevertE.constant_e(
			genRequest(
				{url: 'Paper/'+$URL('id')+'/Comment/revert',
				fields: {cookie:authCookie},
				asynchronous: false})
		).filter_e(function(_) {
			return window.confirm('Are you sure you want to revert to your last published comment? Anything you have entered since will be lost!');}
		)
	)).startsWith(false); */

	var uRolesE = lift_b(function(u, ur) {
		var isadmin = inList('admin',u.rolenames);
		var isreviewer = inList('reviewer',u.rolenames);
		var rls = [];
		if (isadmin) rls.push('admin');
		if (isreviewer) {
			if(ur)
				rls.push('reviewing');
			if(!ur || ur.hasPublished)
				rls.push('reviewer');
		}
		if(!ur)
			rls.push('commenter');
		return rls;
	}, curUserE.startsWith({rolenames:['loggedout']}),userReviewE.startsWith(false)).changes();

	var PaperTabs = new TabSet(
		uRolesE.startsWith([]),
		{
			reviewing:[getObj('paper_review_form_tab')],
			commenter:[],
			reviewer:$$('paper-tab'),user:[],loggedout:[],
			admin:$$('paper-tab').concat($$('admin-tab'))
		},
		function(that) {
			var tabClicksE = map(function(tab) {
				return extractEvent_e(tab,'click').constant_e(tab.id);
			},that.allTabs);
			return merge_e.apply(this,[
				userReviewE.transform_e(function(ur) {if(ur && !(ur.hasPublished)) return 'paper_review_form_tab'; else return null;}).
					filter_e(function(_) {return _ != null;})].concat(tabClicksE)).startsWith($URL('mode'));
		}
	);
	lift_b(function(bi,pi,ct) {
		if(bi && pi) {
			var ttl = bi.info.shortname + ' - #'+pi.id+': '+pi.title;
			if(ct && getObj(ct)) ttl += ' ('+getObj(ct).title+')';
			document.title = ttl;
		}
	},basicInfoE.startsWith(null),paperInfoE.startsWith(null),PaperTabs.currentTabB);

	var intoAssignE = merge_e(
		PaperTabs.currentTabB.changes().filter_e(function(t) {return t == 'paper_assign_tab';}),
		$URL('mode') == 'paper_assign_tab' ? onLoadTimeE : receiver_e());
	var usersInfoQueryE = merge_e(launchE,intoAssignE,iframeLoad_e('astarget')).
    snapshot_e(getFieldE(paperCapsE, 'getByRole').startsWith(null)).
    filter_e(function(_) { return _; }).
    transform_e(function(cap) { return [cap, {role: 'reviewer'}]; });
	var usersInfoE = postE(usersInfoQueryE);
	var intoOptionsE = merge_e(
		PaperTabs.currentTabB.changes().filter_e(function(t) {return t == 'paper_options_tab';}),
		$URL('mode') == 'paper_options_tab' ? onLoadTimeE : receiver_e());
	var extnsQueryE = intoOptionsE.snapshot_e(
    getFieldE(paperCapsE, 'getDeadlines').startsWith(null)).filter_e(id);
	var extensionsE = getE(extnsQueryE);

	var nextIdB = merge_e(launchE,intoAssignE).snapshot_e(
      getFieldE(paperCapsE, 'nextPaper').startsWith(null)).
      filter_e(function(_) { 
        return _; }).
    startsWith(0);

  insertValueE(getFieldE(paperCapsE, 'backToList'), 'back_to_list_tab',
      'href');

	setPaperContent(
			PaperTabs.currentTabB,paperInfoE.startsWith(null),curUserE.startsWith(null),
			basicInfoE.startsWith(null),usersInfoE.startsWith(null),extensionsE.startsWith(null),
			userReviewE.startsWith(false),userCommentB,nextIdB,revertE,commentRevertE,commentSubmitE,paperCapsE.startsWith(null));

	onLoadTimeE.sendEvent('loaded!');
	
	if($URL('review'))
		window.location =  '#' + $URL('review');
}

