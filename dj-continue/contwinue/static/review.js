function getLogoutEventsE() {
	var lbuts = $$('logout');
	var logoutsE = merge_e.apply(this,
			map(function(b) {return extractEvent_e(b,'click');},
				lbuts)
			);
	return logoutsE;
}
function getSummariesE(onLoadTimeE,currentTabB,summariesCap,paperCaps) {
	var reloadSummariesE = merge_e(iframeLoad_e('dectarget'),iframeLoad_e('astarget'));
	var periodicReloadE = timer_e(20000);
	var pqTimesE = merge_e(onLoadTimeE,reloadSummariesE,periodicReloadE);
		
	return rec_e(function(serverRetE) {
		var lastChangeValB = serverRetE.transform_e(function(_) {return _.lcv;}).startsWith(-1);

		var paperQueryE = pqTimesE.snapshot_e(lift_b(function(lcv) {
			return [summariesCap, genRequest({lastChangeVal:lcv})];
		}, lastChangeValB));
	
		return postE(paperQueryE).transform_e(
			function(sums) {
				if(sums == null || !sums.changed) 
					return null;
				else {
					return {lcv: sums.lastChange,
							pinfo: map(function(paper) {
								paper.reviewStats = getReviewStats(paper.reviewsInfo);
								paper.authorSort = parseAuthorList(paper.author);
                paper.launch = paperCaps[paper.id]['launch'];
							return paper;},sums.summaries)};
				}
			}
		).filter_e(function(_) {return _ != null;});
	}).transform_e(function(_) {return _.pinfo;});
}

function FilterWidget(basicInfo) {
	Widget.apply(this);

	var scoreTable;
	
	if(basicInfo.info.useDS) {
		var siWidg = new CombinedInputWidget(
			map(function(_) {return new CheckboxWidget(false);},[-3,-2,-1,0,1,2]),
			function(ni,b,bc,ok,gc,g) {
				return TABLE(TBODY(
						TR(TD(g),TD('Good')),
						TR(TD(gc),TD('Good (In Conflict)')),
						TR(TD(ok),TD('Unknown')),
						TR(TD(bc),TD('Bad (In Conflict)')),
						TR(TD(b),TD('Bad')),
						TR(TD(ni),TD('Not Enough Reviews'))));
			});
		this.behaviors.filterFn = siWidg.behaviors.value.transform_b(function(ss) {
			return function(paper) {
				if(ss[0] || ss[1] || ss[2] || ss[3] || ss[4] || ss[5]) return ss[paper.paper.oscore+3];
				else return true;
			}
		});
		scoreTable = siWidg.dom;
	}
	else {
		var scoreBehs = [];
		var scoreList = [];

		scoreTable = TABLE(TBODY(map(function(hi) {
			return hi.abbr == 'U' ? '' : 
			TR(map(function(low) {
				if(low.abbr == 'U') return TD(' ');
				else if(hi.abbr > low.abbr) return TD(' ');
				else if(hi.abbr == low.abbr) {
					var cb = INPUT({type:'checkbox',value:hi.abbr});
					scoreBehs.push($B(cb).transform_b(function(o) {return {id:hi.abbr,checked:o};}));
					scoreList.push(hi.abbr);
					return TD(cb,BR(),hi.abbr);
				}
				else {
					var cb = INPUT({type:'checkbox',value:hi.abbr+'-'+low.abbr});
					scoreBehs.push($B(cb).transform_b(function(o) {return {id:(hi.abbr+'-'+low.abbr),checked:o};}));
					scoreList.push(hi.abbr+'-'+low.abbr);
					return TD(cb,BR(),hi.abbr+'-'+low.abbr);
				}
			},basicInfo.ratings));
		},basicInfo.ratings)));
		var scoreFilterB = lift_b.apply(lift_b,[function() {
			var ret = {};
			map(function(b) {ret[b.id] = b.checked;},arguments);
			return ret;
		}].concat(scoreBehs))

		this.behaviors.filterFn = lift_b(function(sF) {
			var useScore = fold(function(v, acc) {return acc || sF[v]},false,scoreList);
			return function(paper) {
				if(useScore)
					if(!sF[paper.paper.reviewStats.reviewRange])
						return false;
				return true;
			}
		},scoreFilterB);
	}

	showhide = new ToggleWidget('Filter by Score +','Filter by Score -');
	insertValueB(showhide.behaviors.toggled.transform_b(function(_) {return _ ? 'block' : 'none';}),scoreTable,'style','display');

	this.dom = FIELDSETB({className:'list-score-filter'},LEGENDB(showhide.dom),scoreTable);
}
FilterWidget.prototype = new Widget();

function TopicFilterWidget(basicInfo,cookie,getAbstracts) {
	Widget.apply(this);

	var topicKvs = map(function(t) {return {k:t.id,v:t.name};},basicInfo.topics).concat({k:-1,v:SPAN({style:{fontStyle:'italic'}},'No Topics Selected')});
	var topicSel = new CheckboxListWidget(topicKvs,[]);
	topicSel.dom.className = 'topicList';
	topicSel.dom.id = 'topicSelectionWidget'

	var anyall = new RadioListWidget([{k:'any',v:'Match Any Category'},{k:'all',v:'Match All Categories'}],'any');
	anyall.dom.className = 'topicList';

	var searchbox = INPUT({type:'text',value:'',size:15});

	var searchB = $B(searchbox);

	var titleCb = INPUT({type:'checkbox',checked:true});
	var authorCb = INPUT({type:'checkbox'});
	var abstractCb = INPUT({type:'checkbox'});
	var abstA = A({href:'javascript://Get Abstrcts'},'Click to load abstracts for searching');
	var getAbstractsB = getE(
			extractEvent_e(abstA,'click').once_e().constant_e(getAbstracts)
		).transform_e(function(al) {return toObj(al,function(o) {return o.id;});}).startsWith(null);

	var searchBoxB = getAbstractsB.transform_b(function(ga) {
		return DIV({className:'searchbox',id:'searchbox'},
			'Search for ',searchbox,' in ',titleCb, 'Title ',authorCb,'Author',(ga ? [abstractCb,' Abstracts'] : [BR(),abstA]));
	});

	var topicListB = DIVB(
		topicSel.dom,BR(),anyall.dom,HR(),
		searchBoxB);

	var searchMatchesB = lift_b(function(abstracts,searchF,sTitle,sAuthor,sAbstract) {
			return function(paper) {
				if(searchF == '' || !(sTitle || sAuthor || sAbstract))
					return true;
				return (
					(sTitle && paper.paper.title.toLowerCase().indexOf(searchF.toLowerCase()) != -1) ||
					(sAuthor && paper.paper.author.toLowerCase().indexOf(searchF.toLowerCase()) != -1) ||
					(sAbstract && abstracts[paper.paper.id].value.indexOf(searchF.toLowerCase()) != -1));
			}
	},getAbstractsB,searchB,$B(titleCb),$B(authorCb),$B(abstractCb));

	this.behaviors.filterFn = lift_b(function(anyall,topicF,searchF) {
		return function(paper) {
			if(!searchF(paper)) return false;
			if(topicF.length) {
				var pTopics = toObj(paper.paper.topics,function(t) {return t.id;});
				if(paper.paper.topics.length == 0) pTopics[-1] = true;
				var foldFn = (anyall == 'any') ? function(v, acc) {return acc || pTopics[v];} : function(v, acc) {return acc && pTopics[v];};
				return fold(foldFn,(anyall == 'any') ? false : true,topicF);
			}
			return true;
		};
	},anyall.behaviors.value,topicSel.behaviors.value,searchMatchesB);

	var allTops = toObj(topicKvs,function(t) {return t.k;});
	allTops[-1] = {k:-1,v:'No Topics Specified'};
	descriptionB = lift_b(function(anyall,topicF,searchF,sTitle,sAuthor,sAbstract) {
		var desc = 'Papers';
		if(searchF != '' && (sTitle || sAuthor || sAbstract)) {
			desc += ' with ';
			var searchIn = ''
			if(sTitle) searchIn = 'title';
			if(sAuthor) searchIn = (searchIn == '' ? 'author' : searchIn+' or author');
			if(sAbstract) searchIn = (searchIn == '' ? 'abstract' : searchIn+' or abstract');
			desc += searchIn + ' matching "'+searchF+'"';
		}
		if(topicF.length) {
			desc += ' whose topics include ';
			var quant = '';
			if (anyall == 'any') quant = 'one of: '; else quant = 'all of: ';
			if(topicF.length > 1)
			 	desc += quant;
			desc += fold(function(v, acc) {return (acc == '') ? allTops[v].v : acc + ', '+allTops[v].v;},'',topicF);
		}
		if(desc == 'Papers') desc = 'No Filter In Use';
		return DIV(desc);
	},anyall.behaviors.value,topicSel.behaviors.value,searchB,$B(titleCb),$B(authorCb),$B(abstractCb));
			
	var allbidSel = SELECT(map(function(bo) {
				return OPTION({value:bo.id, selected:(bo.id == basicInfo.info.defaultBidID)},bo.abbr,'. ',bo.description); }, basicInfo.bids));
	var allbidBtn = INPUT({type:'button',value:'Do it!'});
	var allbidPar = DIV({id:'allbidPar',className:'set-all-bids'},'Bid ',allbidSel,' on every unbid paper maching this filter (not just on this page!) ',' ',allbidBtn);
	this.events.setbid = snapshot_e(extractEvent_e(allbidBtn,'click'),$B(allbidSel));

	showhide = new ToggleWidget('Filter and Search Papers [+]','Filter and Search Papers [-]');
	var dspB = switch_b(showhide.behaviors.toggled.transform_b(function(t) {if (t) return topicListB; else return descriptionB;}));
	this.dom = DIVB(FIELDSETB({className:'list-topic-filter'},LEGENDB(showhide.dom),dspB),allbidPar);

	demoEventsE.add_e(showhide.behaviors.toggled.changes().transform_e(function(tog) {return {action:'togglefilter',open:tog};}));
	demoEventsE.add_e(topicSel.behaviors.value.changes().transform_e(function(tog) {return {action:'topicclicked'};}));
	demoEventsE.add_e(searchB.changes().transform_e(function(sv) {return {action:'filtersearched',value:sv};}));
}
TopicFilterWidget.prototype = new Widget();

function MirrorFilterWidget(fw) {
	Widget.apply(this);
	this.dom = '';
	this.behaviors.filterFn = fw.behaviors.filterFn;
}
MirrorFilterWidget.prototype = new Widget();

function genAbstractRow(numCols,getAbstract) {
	return function(paper,cookie) {
		var shabs = new ToggleWidget('Show Abstract','Hide Abstract');
		var shabs2 = new ToggleWidget('Show Abstract','Hide Abstract');
		shabs2.events.toggleOn.transform_e(function(to) {shabs.events.toggleOn.sendEvent(true);});
		shabs2.events.toggleOff.transform_e(function(to) {shabs.events.toggleOff.sendEvent(false);});
		var abstrE = getE(shabs.events.toggleOn.constant_e(getAbstract));
		var abstrB = merge_e(
			shabs.events.toggleOff.constant_e(SPAN()),
			abstrE.transform_e(function(_) {
				return DIV({className:'abstract-row'},paraString(_,''),
					P({className:'topics-list'},'Topics: ',fold(function(v, acc) {return (acc == 'None') ? v.name : acc + ', '+v.name;},'None',paper.topics))
				);})
			).startsWith(SPAN());
		return TRB(TD({className:'blank'}),
				TDB({className:'blank-line'},DIVB({className:'reviewer-list'},shabs2.dom)),
				TDB({className:'blank-line',colSpan:numCols-2},DIVB({className:'reviewer-list',style:{textAlign:'right'}},shabs.dom),abstrB));
	}
}
function genPaperLink(id,cookie,mode,tab,review,launch) {
  return 'paperview?id='+id+'&mode='+mode+'&tab='+tab+(review?'&review='+review:'')+"#"+launch;
}

numberCol = new Column('number','#',function(a,b) {return a.id - b.id;},
	function (paper,cookie,tab) {return TD({style:{color:paper.completed?'#000':'#900'}},paper.id,BR(),B(paper.decision.abbr));});
summaryCol = new Column('summary','Sum',
	function(a,b) {
		if (!a.reviewStats.max && !b.reviewStats.max)
			return 0;
		else if (!a.reviewStats.max)
			return 1;
		else if (!b.reviewStats.max)
			return -1;
		else if (a.reviewStats.max < b.reviewStats.max)
			return -1;
		else if (a.reviewStats.max > b.reviewStats.max)
			return 1;
		else if (a.reviewStats.min < b.reviewStats.min)
			return -1;
		else if (a.reviewStats.min > b.reviewStats.min)
			return 1;
		else
			return 0;
		},
		function (paper,cookie,tab) {return TD(DIV({className:paper.reviewStats.reviewRange},
				paper.reviewStats.reviewRange == 'E' ? '-' : paper.reviewStats.reviewRange));});
authorCol = new Column('authors','Authors',function(a,b) {return a.authorSort < b.authorSort ? -1 : (a.authorSort > b.authorSort ? 1 : 0);},
		function(paper,cookie,tab) {return TD({className:'authors'},paper.author);});
titleCol = new Column('title','Title',function(a,b) {return a.title < b.title ? -1 : (a.title > b.title ? 1 : 0);},
		function (paper,cookie,tab) {
			var pl = paper.hasconflict ? paper.title : A({target:'_blank',href:genPaperLink(paper.id,cookie,'paper_info_tab',tab,false,paper.launch)},paper.title);
			if(!paper.hasconflict) demoEventsE.add_e(extractEvent_e(pl,'click').constant_e({action:'paperclick'}));
			return TD({className:'title'},pl);
		});
shortNumberCol = new Column('short-number','#',function(a,b) {return a.id - b.id;},
		function (paper,cookie,tab) {return TD({className:'shortnumber'},paper.id);});
var defaultCols = [numberCol,summaryCol,authorCol,titleCol];

function PaperEntry(basicInfo,paper,cookie,tab,columns,getSecondRow) {
	var me = this;
	this.paper = paper;
	if(!columns) columns = defaultCols;
	if(!getSecondRow) getSecondRow = function(paper,cookie,tab) {
		return TR(TD({className:'blank'},' '),TD({className:'blank-line',colSpan:columns.length-1},DIV({className:'reviewer-list'},
			paper.reviewsInfo ? (paper.reviewStats.sub+'/'+paper.reviewStats.rev+': ', (paper.reviewStats.rev ?
			fold(function(v, acc) {	if (!acc) return [v]; else return acc.concat([', ',v]); },
				null,map(function(review) {
					if(review.submitted) {
						return A({target:'_blank',href:genPaperLink(paper.id,cookie,'paper_info_tab',tab,review.id)},
                    review.name+' ('+review.overall+'/'+review.expertise+')', paper.launch);
					}
					else {
						return SPAN({className:'missing'},review.name)
					}
				},paper.reviewsInfo)) : SPAN({className:'error'},'No reviewers assigned')) 
			) : 'Assigned for your review.')));
	}
	this.paper.dcobj = toObj(this.paper.dcomps, function(dc) {return dc.typeID;});
	this.paper.completed = fold(function(v,acc) {return acc && (!(v.mandatory && v.format != 'Text') || me.paper.dcobj[v.id]);},true,basicInfo.components);

	this.doms = null;
	this.getDoms = function() {
		if (this.doms == null) this.doms = [
				TR(map(function(col) {var c = col.makeTD(paper,cookie,tab); c.className=col.className; return c;},columns)),
				getSecondRow(paper,cookie,tab)
			];
		return this.doms;
	}
	this.getObj = function() {return this.paper;}
}

function makeBidTable(papersB,bidvals,basicInfo,updateBids,getAbstracts,paperCaps) {
	var bidClicksE = consumer_e();
	var setOneE = postE(bidClicksE.transform_e(function(bc) {
		return [updateBids, {bid:bc.value,papers:[bc.id]}];
	}));
	demoEventsE.add_e(setOneE.transform_e(function(so) {return {action:'setbid',paper:so.paperID};}));

	var allChangesE = consumer_e();
	demoEventsE.add_e(allChangesE.transform_e(function(aa) {return {action:'allbid'};}));
	var bidChangesE = merge_e(allChangesE,setOneE);
	
	var bidValsB = collect_b(bidvals,bidChangesE,function(newclick,bvs) {
			map(function(nb) {
				bvs[nb.paperID] = nb;
			},newclick);
			return bvs;
	});

	var bidsByValB = lift_b(function(ps,bvs) {
			var ret = {};
			map(function(bt) {ret[bt.id] = 0;},basicInfo.bids);
			map(function(p) {ret[(bvs[p.id] ? bvs[p.id].valueID : basicInfo.info.defaultBidID)] += 1;},ps);
			return P('Bid Summary: ',map(function(bt) {return bt.abbr+': '+ret[bt.id]+' ';},basicInfo.bids));
	},papersB,bidValsB);

	var bcolumns = [shortNumberCol,authorCol,titleCol,
		new Column('bid','Bid',function(a,b) {
				var bnow = bidValsB.valueNow();
				var bida = bnow[a.id] ? bnow[a.id].valueID : basicInfo.info.defaultBidID
				var bidb = bnow[b.id] ? bnow[b.id].valueID : basicInfo.info.defaultBidID
				return bida-bidb; },
			function(paper,cookie,tab) {
				var bidid = bidvals[paper.id] ? bidvals[paper.id].valueID : basicInfo.info.defaultBidID;
				var bidselect = new SelectWidget(bidid,
					map(function(bo) {
						return OPTION({value:bo.id},bo.abbr,'. ',bo.description);
					}, basicInfo.bids));
				insertValueE(
					setAllE
						.transform_e(function(abs) {
							return fold(function(v, acc) {
                return acc ? acc : (v.paperID == paper.id ? v.valueID : null)},null,abs);
						})
						.filter_e(function(_) {return _;}),
					bidselect.behaviors.inputElems.valueNow()[0],
					'value'
				);
				var bvalE = extractEvent_e(bidselect.behaviors.inputElems.valueNow()[0],'change')
					.transform_e(function(_) {return bidselect.behaviors.inputElems.valueNow()[0].value;});
				var greyB = merge_e(bvalE.constant_e(true),bidChangesE.constant_e(false)).startsWith(false);
				bidselect = bidselect.greyOutable(greyB);
				bidClicksE.add_e(bvalE.transform_e(function(bv) {
          return {id:paper.id,value:bv};
        }));
				return TD({name:'bidcolumn'},bidselect.dom);
			})
	];
	
	var paperEntriesB = papersB.transform_b(function(papers) {
			return map(function(p) {
        return new PaperEntry(
          basicInfo,
          p,
          authCookie,
          'bidding_tab',
          bcolumns,
          genAbstractRow(bcolumns.length, paperCaps[p.id].getAbstract)
        );
      },papers)
    });
	
	var paperListsB = lift_b(function(bvs,paperEntries) {
		var l = [[],[]];
		map(function(pe) {
			if (bvs[pe.paper.id] && !(bvs[pe.paper.id].valueID == basicInfo.info.defaultBidID))
				l[0].push(pe);
			else
				l[1].push(pe);
		},paperEntries);
		return l;
	},bidValsB,paperEntriesB);

	var topfilt = new TopicFilterWidget(basicInfo,authCookie,getAbstracts);
	var setAllE = postE(combine_eb(function(nbid,pl,filt) {
			return [updateBids, genRequest({
			  papers: map(
          function(p) {return p.paper.id;},
          filter(filt,pl[1])
        ),
        bid:nbid
      })];
		},topfilt.events.setbid,paperListsB,topfilt.behaviors.filterFn));
	allChangesE.plug_e(setAllE);

	var noBidTable = new TableWidget(paperListsB.transform_b(function(l) {return l[1];}),'paper',bcolumns,topfilt).dom;
	var bidTable = new TableWidget(paperListsB.transform_b(function(l) {return l[0];}),'paper',bcolumns,new MirrorFilterWidget(topfilt)).dom;

	return DIVB(bidsByValB,H3('To Bid'),noBidTable,H3('Already Bid'),bidTable);
}

function makeAllTable(papersB,basicInfo) {
	var acolumns = defaultCols.concat([
			new Column('p-reviewed','%',
				function(a,b) {
					if (a.reviewStats.rev == 0 && b.reviewStats.rev == 0)
						return 0;
					else if (a.reviewStats.rev == 0)
						return -1;
					else if (b.reviewStats.rev == 0)
						return 1;
					else
						return (a.reviewStats.sub/a.reviewStats.rev) - (b.reviewStats.sub/b.reviewStats.rev);
				},
				function(paper,cookie,tab) {return TD(paper.reviewStats.rev ? (Math.floor(paper.reviewStats.sub/paper.reviewStats.rev*100)+'%') : 'N/A');}),
			new Column('max-expertise','Exp',
				function(a,b) {
					if (a.reviewStats.maxExp == ' ' && b.reviewStats.maxExp == ' ')
						return 0;
					else if (a.reviewStats.maxExp == ' ')
						return 1;
					else if (b.reviewStats.maxExp == ' ')
						return -1;
					else if (a.reviewStats.maxExp < b.reviewStats.maxExp)
						return -1;
					else if (a.reviewStats.maxExp > b.reviewStats.maxExp)
						return 1;
					else
						return 0;
				},
				function(paper,cookie,tab) {return TD(paper.reviewStats.maxExp);})]);
	
	var paperEntriesB = papersB.transform_b(function(papers) {return map(function(p) {return new PaperEntry(basicInfo,p,authCookie,'all_tab',acolumns);},papers)});
	var tbl = new TableWidget(paperEntriesB,'paper',acolumns,new FilterWidget(basicInfo));
	demoEventsE.add_e(tbl.behaviors.cols.changes().transform_e(function(bsc) {return {action:'all-sort',sortby:acolumns[bsc[0].col].className};}));
	return tbl.dom;
}

function makeReviewTable(papersB,basicInfo,cuser,getReviewPercentages,paperCaps) {
	var downloadCols = map(function(dc) {
			return new Column('download',dc.description,function(a,b) {return 0;},
		function (paper,cookie,tab) {
      var ccap = paperCaps[paper.id].compsCaps[dc.id];
      if (ccap) {
        return TD(paper.dcobj[dc.id] ? A({target:'_blank',
          href:ccap.serialize()},'Download') : '');
      }
      else {
        return TD(SPAN());
      }
    })},
		filter(function(c) {return c.format != 'Text';},basicInfo.components));
	var trListsB = papersB.transform_b(function(papers) {
		var toreview = [];
		var reviewed = [];
		map(function(pe) {
			if(pe.reviewsInfo) {
				map(function(r) {
					if(r.reviewerID == cuser.id) {
						if(r.submitted)
							reviewed.push(new PaperEntry(basicInfo,pe,authCookie,'review_tab',defaultCols.concat(downloadCols)));
						else
							toreview.push(new PaperEntry(basicInfo,pe,authCookie,'review_tab',[shortNumberCol,authorCol,titleCol].concat(downloadCols),genAbstractRow(3+downloadCols.length,paperCaps[pe.id].getAbstract)));
					}
				},pe.reviewsInfo)
			}
			else
				toreview.push(new PaperEntry(basicInfo,pe,authCookie,'review_tab',[shortNumberCol,authorCol,titleCol].concat(downloadCols),genAbstractRow(3+downloadCols.length,paperCaps[pe.id].getAbstract)));
		},papers);
		return [toreview,reviewed];
	});

	var progressBarB = trListsB.transform_b(function(l) {
		var progress = (l[1].length + l[0].length) ? parseInt(l[1].length / (l[1].length+l[0].length) * 100)+'%' : 'N/A';

		return TABLE({className:'progress-bar', width:'90%'},TBODY(TR(
			TH({width:'20%'},'Progress:'),
			TD({width:'8%',align:'right'},progress),
			TD(DIV({className:'progress-dv'},
				DIV({className:'progress-inner-dv',style:{width:(progress=='N/A'?'100%':progress)}},' ')))
			)));
	});

	var othersLink = A({href:'javascript://Others',name:'othersdoing'},'(How are the others doing?)');
	var othersLinkClicked = extractEvent_e(othersLink,'click');
	demoEventsE.add_e(othersLinkClicked.constant_e({action:'progressclicked'}));
	var closeLink = A({href:'javascript://Close Others'},'Close');
	var closeLinkClicked = extractEvent_e(closeLink,'click');
	var displayTableB = collect_b('none',merge_e(othersLinkClicked.constant_e(true),closeLinkClicked.constant_e(false)),function(action,oval) {
			return action ? (oval == 'none' ? 'block' : 'none') : 'none';
		});
	var allReviewsE = getE(othersLinkClicked
    .constant_e(getReviewPercentages));
	var reviewTableB = lift_b(function(doDisplay,pcts) {
			return DIV({style:{display:doDisplay}},
				TABLE({className:'progress-bar',width:'90%'},TBODY(
					map(function(pct) {
						if(pct.id == cuser.id) return '';
						return TR(
							TH({style:{fontWeight:'normal',width:'20%'}},pct.name),
							TD({width:'8%',align:'right'},pct.percentage),
							TD(DIV({className:'progress-dv'},
								DIV({className:'progress-inner-dv',style:{width:pct.percentage=='N/A'?'100%':pct.percentage}},' ')))
						);
          },pcts))),
				P({className:'action-link'},closeLink));
	},displayTableB,allReviewsE.startsWith([]));
	return DIVB(
		progressBarB,
		P({className:'action-link',style:{fontSize:'x-small'}},othersLink),
		reviewTableB,
		H3('To Review'),
		new TableWidget(trListsB.transform_b(function(l) {return l[0];}),'paper',[shortNumberCol,authorCol,titleCol].concat(downloadCols)).dom,
		H3('Reviewed'),
		new TableWidget(trListsB.transform_b(function(l) {return l[1];}),'paper',defaultCols.concat(downloadCols)).dom
	);
}

function makeAssignTable(papersB,basicInfo) {
	var acolumns = [numberCol,summaryCol,authorCol,
		new Column('title','Title',function(a,b) {return a.title < b.title ? -1 : (a.title > b.title ? 1 : 0);},
				function(paper,cookie,tab) {return TD(paper.hasconflict ? 
					paper.title : A({target:'_blank',href:genPaperLink(paper.id,cookie,'paper_assign_tab',tab,false,paper.launch)},paper.title));}),
		new Column('reviewers','Rvwrs',function(a,b) {return a.reviewStats.rev - b.reviewStats.rev;},
				function(paper,cookie,tab) {return TD(paper.reviewStats.rev+'');})];
	var paperEntriesB = papersB.transform_b(function(papers) {
		return map(function(p) {return new PaperEntry(basicInfo,p,authCookie,'assign_tab',acolumns);},papers);
	});
	var unassignedB = papersB.transform_b(function(papers) {
		var u = fold(function(v, acc) {return v.reviewStats.rev == 0 ? acc+1 : acc;},0,papers);
		return u ? P({className:'action-link'},SPAN({className:'error'},u+' unassigned')) : SPAN(' ');
	});
	return DIVB(unassignedB,
				//P({className:'action-link'},A({href:'spreadsheet.html?cookie='+authCookie,target:'_blank',rel:'presentation'},'Spreadsheet View')),
				new TableWidget(paperEntriesB,'paper',acolumns).dom);
}

function makeDecideTable(papersB,basicInfo,updateCaps) {
	var decEventsE = receiver_e();
	var dcolumns = defaultCols.concat([
			new Column('decision','Decision',function(a,b) {return a.decision.id - b.decision.id;},
				function(paper,cookie,tab) {
					var dsWidg = new SelectWidget(paper.decision.id,
							map(function(de) {
								return OPTION({value:de.id, selected:(de.id == paper.decision.id)},de.description);
							},filter(function(de) {return (!de.targetable || paper.othercats || de.id == paper.target.id);}, basicInfo.decisions))
						).belayServerSaving(function(dval) {
							return genRequest({fields:{decision:dval}});
						}, true, updateCaps[paper.id].updateDecision);
					return TD(dsWidg.dom);
				})]);
	var paperEntriesB = papersB.transform_b(function(papers) {return map(function(p) {return new PaperEntry(basicInfo,p,authCookie,'decide_tab',dcolumns);},papers)});
	return new TableWidget(paperEntriesB,'paper',dcolumns,new FilterWidget(basicInfo)).dom;
}

function makeMeetingTable(papersB,basicInfo,cuser,meetingInfo,meetingCaps) {
	var meetingOrderB = constant_b(meetingInfo);
	var contdomB = constant_b('');

	if(inList('admin',cuser.rolenames)) {
		function toOrderStr(mi,pname) {
			return fold(function(v,acc) {return (acc == '') ? ''+v[pname] : acc+' '+v[pname];},'',mi);
		}

		var orderbtn = INPUT({type:'button',value:'Set Order'});
		var startmeeting = A({href:'javascript://Start Meeting'},'Start Meeting');
		var considerall = A({href:'javascript://Consider All'},'Consider All Papers');
		var considerundec = A({href:'javascript://Consider Undecided'},'Consider All Undecided Papers');
		var orderBox = new InputWidget(TEXTAREA({rows:10,cols:40},toOrderStr(meetingInfo,'paperID')));

		var continuemeeting = A({href:'meeting?continue=yes#' + meetingCaps.launchMeeting},'Continue Meeting');
		var restartmeeting = A({href:'javascript://Restart Meeting'},'Restart Meeting');
		
		var caE = snapshot_e(extractEvent_e(considerall,'click'),papersB.transform_b(function(ps) {return toOrderStr(ps,'id');}));
		var cuE = snapshot_e(extractEvent_e(considerundec,'click'),papersB.transform_b(function(ps) {
					return toOrderStr(filter(function(_) {return _.decision.id == basicInfo.info.defaultDecisionID;},ps),'id');}));
		var soE = snapshot_e(extractEvent_e(orderbtn,'click'),orderBox.behaviors.value);
		
		var setOrderE = postE(merge_e(caE,cuE,soE).transform_e(
      function(pstr) { return [meetingCaps.setOrder, {pstr:pstr}];}));
		var startE = postE(snapshot_e(extractEvent_e(startmeeting,'click'),setOrderE.startsWith(meetingInfo)).filter_e(function(ord) {
			return ord.length > 0;}).transform_e(function(ord) {
        return [meetingCaps.jumpTo, {paper:ord[0].paperID}];
		  }));
		startE.transform_e(function(_) {
      window.location = 'meeting#' + meetingCaps.launchMeeting;
    });
		var restartE = postE(extractEvent_e(restartmeeting,'click').
      constant_e([meetingCaps.endMeeting, {}]));
		meetingOrderB = merge_e(setOrderE,startE,restartE).startsWith(meetingInfo);

		insertValueE(setOrderE.transform_e(function(_) {return toOrderStr(_,'paperID');}),orderBox.dom,'value');
		greyB = merge_e(merge_e(caE,cuE,soE).constant_e(true),setOrderE.constant_e(false)).startsWith(false);
		var obdom = orderBox.greyOutable(greyB).dom;

		var nomeetingdom = DIV({className:'control-box'},
			H4('Meeting Controls'),
			UL(LI(startmeeting),LI(considerall),LI(considerundec)),
			obdom,DIV({className:'form-buttons'},orderbtn));
		var continuedom = DIV({className:'control-box'},
			H4('Meeting Controls'),
			UL(LI(continuemeeting),LI(restartmeeting)));
		var meetingStartedB = meetingOrderB.transform_b(function(mo) {return fold(function(v, acc) {return acc || v.current;},false,mo);});
		contdomB = meetingStartedB.transform_b(function(_) {
			return _ ? continuedom : nomeetingdom;});
	}

	var ordByIdB = meetingOrderB.transform_b(function(mo) {return toObj(mo,function(m) {return m.paperID;});});
	var orderedPapersB = lift_b(function(papers,ordById) {
			return map(function(p) {
				var pp = objCopy(p);
				if (ordById[pp.id]) {
					pp.morder = ordById[pp.id].morder;
					pp.current = ordById[pp.id].current;
				}
				return pp;
			},papers);
		},papersB,ordByIdB);

	var mcolumns = defaultCols.concat([new Column('meeting-order','M',
		function(a,b) {
			if (a.morder) {	return (b.morder ? (a.morder - b.morder) : -1);}
			else if (b.morder) return 1;
			else return 0;
		},
		function(paper,cookie,tab) {
			return TD(paper.morder ? (paper.current ? SPAN({style:{color:'#00f'}},paper.morder) : paper.morder) : '-');})]);
	var getMRow = function(paper,cookie) {
		return TR(TD({className:'blank'},' '),TD({className:'blank-line',colSpan:4},DIV({className:'reviewer-list'},'Conflicts: ',
			paper.conflicts.length ?
						fold(function(conf,l) {
							cspn = SPAN({className:'conflict'},conf.fullname);
							if(l.length == 0) return [cspn]; else return l.concat([', ',cspn]);},[],paper.conflicts)
					: 'None')));
	};
	var paperEntriesB = orderedPapersB.transform_b(function(papers) {
			return map(function(p) {return new PaperEntry(basicInfo,p,authCookie,'meeting_tab',mcolumns,getMRow);},papers)});

	return  DIVB(
				contdomB,
				new TableWidget(paperEntriesB,'paper',mcolumns).dom);
}

function makeGotoTab(summariesB,basicInfo,cuser) {
	var tb = INPUT({type:'text'});
	var ok = INPUT({type:'button',value:'Goto'});
	
	var getGRow = function(paper,cookie) {
			return TR(TD({className:'blank'},' '),TD({className:'blank-line',colSpan:3},' '));
	};

	var paperExistsB = lift_b(function(summaries,pn) {
		var paperNum = parseInt(pn);
		return fold(function(v,acc) {return (v.id==paperNum ? v : acc);},{invalid:true,id:paperNum},summaries);
	},summariesB,$B(tb));
	
	var clkE = extractEvent_e(ok,'click');

	var invalidB = snapshot_e(clkE,paperExistsB).startsWith(true).transform_b(function(pn) {
		if(pn.invalid)
			return P({className:'error'},''+pn.id+' is not a valid paper number.');
		else if(pn.hasconflict)
			return P({className:'error'},'You are conflicted with paper '+pn.id);
		else return '';
	});

	snapshot_e(clkE,paperExistsB).transform_e(function(pn) {
		if(!pn.invalid && !pn.hasconflict)
			window.location = genPaperLink(pn.id,authCookie,'paper_info_tab','goto_tab',false, pn.launch);
	});

	var hiddenHead = '';
	var hiddenTbl = '';
	if(inList('admin',cuser.rolenames)) {
		var hiddensB = summariesB.transform_b(function(ps) {
			return map(function(p) {return new PaperEntry(basicInfo,p,authCookie,'goto_tab',defaultCols,getGRow);},
				filter(function(p) {return p.hidden;},ps));
		});
		hiddenHead = H3('Hidden Papers');
		hiddenTbl = new TableWidget(hiddensB,'paper',defaultCols).dom;
	}

	return DIVB(
			invalidB.transform_b(function(inv) {return DIV(inv,P(STRONG('Enter a paper number: '),tb,' ',ok));}),
			hiddenHead,
			hiddenTbl);
}

function setMainContent(currentTabB,curUser,basicInfo,summariesE,bidValsE,meetingInfoE,launchInfo) {
	var summariesB = summariesE.startsWith([]);
	var nhSummariesB = summariesB.transform_b(function(ps) {return filter(function(p) {return !p.hidden;},ps);});
	var ncSummariesB = nhSummariesB.transform_b(function(ps) {return filter(function(p) {return !p.hasconflict;},ps);});
	var bidValsB = bidValsE.startsWith(null);
	var meetingInfoB = meetingInfoE.startsWith(null);
	var btb = null;
	var atb = null;
	var rtb = null;
	var astb = null;
	var detb = null; 
	var gtb = null;
	var mtb = null;
	var currentObjB = switch_b(switch_b(currentTabB.transform_b(function(tab) {
		switch(tab) {
			case 'bidding_tab':
				if(!btb) {
          btb = lift_b(function(b) {
            if (b) {
              return makeBidTable(
                nhSummariesB,
                b,
                basicInfo,
                launchInfo.updateBids,
                launchInfo.getAbstracts,
                launchInfo.paperCaps
              );
            }
            else { return constant_b(getLoadingDiv());}
          },bidValsB);
        }
				return btb;
			case 'all_tab':
				if(!atb) atb = constant_b(makeAllTable(ncSummariesB,basicInfo));
				return atb;
			case 'review_tab':
				if(!rtb) rtb = constant_b(makeReviewTable(ncSummariesB,basicInfo,curUser,launchInfo.getPercentages,launchInfo.paperCaps));
				return rtb;
			case 'assign_tab':
				if(!astb) astb = constant_b(makeAssignTable(ncSummariesB,basicInfo));
				return astb;
			case 'decide_tab':
				if(!detb)
          detb = constant_b(makeDecideTable(ncSummariesB,basicInfo,launchInfo.paperCaps));
				return detb;
		case 'meeting_tab':
				if(!mtb) mtb = lift_b(function(m) {
          if (m) 
            return makeMeetingTable(nhSummariesB,basicInfo,curUser,
              m,launchInfo.meetingCaps);
          else
            return constant_b(getLoadingDiv());},meetingInfoB);
   			return mtb;
			case 'goto_tab':
				if(!gtb) gtb = constant_b(makeGotoTab(summariesB,basicInfo,curUser));
				return gtb;
			default:
				return constant_b(constant_b(DIV()));
		}
	})));
	insertDomB(currentObjB,'main_content','beginning');
	demoEventsE.add_e(currentTabB.changes().transform_e(function(ct) {return {action:'changetab',tab:ct};}));
}

function loadPaperLists(MainTabs,onLoadTimeE,curUser,basicInfo,launchInfo) {
  var summariesCapE = launchInfo.getPaperSummaries;
	var summariesE = getSummariesE(onLoadTimeE,MainTabs.currentTabB,summariesCapE,
      launchInfo.paperCaps);
	showLoadBoxE.add_e(summariesE.constant_e(false));

	var bidValsE = getE(onLoadTimeE.constant_e(launchInfo.getUserBids))
	.transform_e(function(bidsin) {
		var bidarr = {};
		map(function(bid) {
			bidarr[bid.paperID] = bid;
		}, bidsin);
		return bidarr;
	});
	var meetingQueryE = MainTabs.currentTabB.changes().filter_e(
    function(ct) { return ct == 'meeting_tab';}).
   constant_e(launchInfo.meetingCaps.getOrder);

	var meetingInfoE = getE(meetingQueryE);

	if(basicInfo.info.useDS) {
		summaryCol = new Column('summary','Sum',
			function(a,b) {	return b.oscore - a.oscore; },
			function(paper,cookie,tab) {return TD(DIV({className:'o'+paper.oscore},
			'/'));});
		defaultCols[1] = summaryCol;
	}

	var contentInfo = setMainContent(MainTabs.currentTabB,curUser,basicInfo,summariesE,bidValsE,meetingInfoE,launchInfo);
}

function loader() {
	var flapjax = flapjaxInit();
	demoEventsE = consumer_e();
	document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);});};

  var capServer = new CapServer();
	var onLoadTimeE = receiver_e();
	authCookie = $URL('cookie');
	var exceptsE = captureServerExcepts();
	showLoadBoxE = consumer_e();
	showLoadBoxE.add_e(exceptsE.constant_e(false));
	showLoadBoxE.add_e(onLoadTimeE.constant_e(true));
	handleExcepts(exceptsE);
  var launchCap = launchCapFromKey(COMMON.urlPrefix, capServer);
  var launchE = getE(onLoadTimeE.constant_e(launchCap));
  
  if(!launchCap || launchCap==="" || launchCap ==="#") {
    window.location = "logout";
  }
	var basicInfoE = getFieldE(launchE, 'basicInfo');

	doConfHead(basicInfoE);
//	var userInfoE = getCurUserE(onLoadTimeE,authCookie);
	var userInfoE = getFieldE(launchE, 'currentUser');
	var doLogoutE = getLogoutEventsE();
  doLogoutE.snapshot_e(basicInfoE.startsWith(null)).
    filter_e(id).transform_e(function(bi) {
      window.name = "";
      window.location = COMMON.urlPrefix + '/' + bi.info.shortname + '/' + 'home';
    });
  doLoginDivB(userInfoE);

  var accountTabB = lift_b(function(li, bi) {
    if(li && bi) {
      var searchString = 'reviewer ' + bi.info.name;
      return makeAccountInfoTab(
        li,
        searchString,
        COMMON.urlPrefix + '/review' + window.name
      );
    }
    return SPANB();
  }, launchE.startsWith(null), basicInfoE.startsWith(null));

  var summariesE = postE(getFieldE(launchE,'getPaperSummaries')
    .transform_e(function(c) { return [c,{lastChangeVal: 0}];}));

	var loadInitTab = $URL('tab') ? $URL('tab') : false;
	
	lift_e(function(basicInfo,userInfo,launchInfo) {
			var revTabs = $$('reviewer-tab');
			if(basicInfo.info.showBid) revTabs = revTabs.concat($$('bid-tab'));
			
			var MainTabs = new TabSet(
				constant_b(userInfo.rolenames),
				{reviewer:revTabs,
					admin:$$('admin-tab').concat(revTabs),
					other:$$('bid-tab')},
				function(that) {
					var tabClicksE = map(function(tab) {
						if(tab != getObj('admin_tab')) return extractEvent_e(tab,'click').constant_e(tab.id); else return receiver_e();
					},that.allTabs);
					var defaultTab = null;
					if(loadInitTab) {
						defaultTab = loadInitTab;
						loadInitTab = false;
					}
					else if (inList('reviewer',userInfo.rolenames))
						defaultTab =  (userInfo.reviewCount > 0 ?	'review_tab' :
									(basicInfo.info.showBid ? 'bidding_tab' : 'all_tab'));
					else if (inList('admin',userInfo.rolenames)) defaultTab = 'all_tab';
					return merge_e.apply(this,tabClicksE).startsWith(defaultTab);
				});
			setTitle(basicInfo,MainTabs.currentTabB);
			insertValueB(MainTabs.currentTabB.transform_b(function(ct){return (ct == null || ct == 'logout_tab') ? 'none' : 'block';}),'maintabs','style','display');
			insertValueB(showLoadBoxE.transform_e(function(_) {return _ ? 'block' : 'none'}).startsWith('none'),'loadbox','style','display');
			var olt2E = receiver_e();
      getObj('admin_tab').href = launchInfo.launchAdmin;
      getObj('admin_tab').target = '_blank';
	    insertDomB(switch_b(accountTabB),'account_placeholder');
      MainTabs.displayOn('account_tab', 'account_content');
			loadPaperLists(MainTabs,olt2E,userInfo,basicInfo,launchInfo);
			olt2E.sendEvent('loaded!');
	},basicInfoE,userInfoE,launchE);
	onLoadTimeE.sendEvent('loaded!');
}

