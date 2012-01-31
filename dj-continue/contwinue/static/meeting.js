function PreviewControlWidget() {
	Widget.apply(this);
	var hideA = A({href:'javascript://Hide Previews'},'hide upcoming');
	var showA = A({href:'javascript://Show Previews',style:{display:'none'}},'show upcoming');
	var pControls = DIV({className:'preview-box-controls'},'[',hideA,showA,']');
	var showPrevsB = merge_e(extractEvent_e(hideA,'click').constant_e(false),extractEvent_e(showA,'click').constant_e(true)).startsWith(true);
	insertValueB(showPrevsB.transform_b(function(_) {return _ ? 'none' : 'inline';}),showA,'style','display');
	insertValueB(showPrevsB.transform_b(function(_) {return _ ? 'inline' : 'none';}),hideA,'style','display');
	this.dom = pControls;
	this.behaviors.show = showPrevsB;
}
function JumpBoxWidget() {
    	Widget.apply(this);
	var nextBox = INPUT({type:'text',size:5,style:{display:'inline'}});
	var jumpBtn = INPUT({type:'button',value:'Jump',style:{display:'inline'}});
	this.events.jump = snapshot_e(extractEvent_e(jumpBtn,'click'),$B(nextBox));
	this.dom = SPAN(nextBox,' ',jumpBtn);
}
function ControlBoxWidget(onLoadTimeE,basicInfoE,meetingCapsE) {
	Widget.apply(this);
	var cb = this;
	var proceedBtn = INPUT({type:'button',value:'Proceed'});
	var nextBtn = INPUT({type:'button',value:'Next Paper'});
	var startBtn = INPUT({type:'button',value:($URL('continue') ? 'Resume' : 'Start Meeting')});
	var endBtn = INPUT({type:'button',value:'End Meeting'});

	var jumpBox = new JumpBoxWidget();
	var pControls = new PreviewControlWidget();

	pE = extractEvent_e(proceedBtn,'click');
	nE = extractEvent_e(nextBtn,'click');
	sE = extractEvent_e(startBtn,'click');
	jE = jumpBox.events.jump;
	eE = extractEvent_e(endBtn,'click');

  var snapnull = function(evt, e) {
    return evt.snapshot_e(evt, e.startsWith(null)).filter_e(function(_) {
      return _ !== null;
    });
  };
  var endCapE = getFieldE(meetingCapsE, 'endMeeting').transform_e(function(_) {
    return [_, {}];
  });
	var endE = postE(snapnull(eE, endCapE));
  snapnull(endE, getFieldE(meetingCapsE, 'backToList')).transform_e(function(_) {
		window.location = _;
  });

	this.events.meetingInfo = rec_e(function(miE) {
		var loadMInfoE = getE(getFieldE(meetingCapsE, 'getOrder'));
 		cb.events.ordNext = miE.transform_e(
			function(mo) {
				var n = fold(function(v, acc) {
						if (acc == 'cur') return v;
						if (v.current) return 'cur';
						return acc;
					},null,mo);
				if(n == 'cur') return null; else return n;
			}
		);
		var jumpNextE = combine_eb(function(nn,mo) {
			if(!mo) return null;
			if(nn == '') return null;
			var pnum = parseInt(nn);
			return fold(function(v, acc) {
				return acc ? acc : (v.paperID == pnum ? v : acc);},null,mo);
		},jE,miE.startsWith(null));
		cb.events.next = merge_e(jumpNextE.filter_e(function(_) {
			    if(_ == null) window.alert('Not a valid paper!');
			    return _ != null;
		}),snapshot_e(nE,cb.events.ordNext.startsWith(null)));
    var jumpCapE = getFieldE(meetingCapsE, 'jumpTo');
		var jumpPaperE = snapshot_e(pE,cb.events.next.startsWith(null));
    var jumpE = postE(lift_b(function(cap, when) {
        if (!cap || !when) { return null; }
        return [cap, {'paper': when.paperID}];
      }, jumpCapE.startsWith(null), jumpPaperE.startsWith(null)).
      changes().filter_e(id));
		return merge_e(loadMInfoE,jumpE);
	});
	this.behaviors.ordNext = this.events.ordNext.startsWith(null);
	
	this.behaviors.current = this.events.meetingInfo.transform_e(function(mo) {
			return fold(function(v, acc) {return acc ? acc : (v.current ? v : acc);},null,mo);
	}).startsWith(null);

  var pinfoE = this.behaviors.current.changes().filter_e(function(_) {
    return _ != null;
  });

  var paperInfoE = lift_b(function(pinfo, getPaper) {
      if (!pinfo || !getPaper) { return null; }
      return [getPaper, {paper: pinfo.paperID}];
    }, pinfoE.startsWith(null),
    getFieldE(meetingCapsE, 'getPaper').startsWith(null)).changes().
    filter_e(id);

	this.events.pInfo = postE(paperInfoE).transform_e(function(p) {
    p.reviewStats = getReviewStats(p.reviewsInfo);
    return p;
  });

	this.behaviors.view = merge_e(
		sE.constant_e('current'),
		this.events.pInfo.skipFirst_e().constant_e('current'),
		this.events.next.constant_e('switching')
	).startsWith('starting');
	this.behaviors.showPrev = lift_b(function(cv,sp) {return (cv != 'switching') && sp; },this.behaviors.view,pControls.behaviors.show);

	var decselB = lift_b(function(bi,paper,updateDecision) {
		if(!bi || !paper || !updateDecision) return SELECT();
		var ds = new SelectWidget(paper.decision.id,map(function(de) {
				return OPTION({value:de.id},de.description);},
				filter(function(de) {return paper.othercats || !de.targetable || paper.target.id == de.id;},bi.decisions)));

    var updE = postE(ds.behaviors.value.changes().
      transform_e(function(decisionID) {
        return [updateDecision, {paper: paper.id, decision: decisionID}];
      }));

		var greyB = merge_e(ds.behaviors.value.changes().constant_e(true),updE.constant_e(false)).startsWith(false);
		return ds.greyOutable(greyB).dom;
	},basicInfoE.startsWith(null),this.events.pInfo.startsWith(null),
    getFieldE(meetingCapsE, 'updateDecision').startsWith(null));

	this.dom = lift_b(function(ds,cv,next) {
		if(cv == 'starting') return DIV(startBtn,BR(),jumpBox.dom,pControls.dom);
		if(cv == 'switching') return DIV(proceedBtn,BR(),jumpBox.dom);
		if(cv == 'current') return (next ? DIV(ds,nextBtn,BR(),jumpBox.dom,pControls.dom) : DIV(ds,endBtn,BR(),jumpBox.dom,pControls.dom));
	},decselB,this.behaviors.view,this.behaviors.ordNext);
}

function loader() {
	var flapjax = flapjaxInit();

	authCookie = $URL('cookie');
	var onLoadTimeE = receiver_e();
	var exceptsE = captureServerExcepts();
	handleExcepts(exceptsE);
  var capServer = new CapServer();
  var launchCap = launchCapFromKey(COMMON.urlPrefix, capServer);
  var launchE = getE(onLoadTimeE.constant_e(launchCap));
	var basicInfoE = getFieldE(launchE, 'basicInfo');
	basicInfoE.transform_e(function(_) {
		document.title = _.info.shortname + ' - PC Meeting';
	});

	var controlBox = new ControlBoxWidget(onLoadTimeE,basicInfoE,
    getFieldE(launchE, 'meetingCaps'));
	insertDomB(controlBox.dom,'control-box','beginning');

	insertValueE(basicInfoE.transform_e(function(bi) {
		var targetables = fold(function(v, acc) {return v.targetable ? acc+1 : acc;},0,bi.decisions);
		if(targetables > 1) return 'block'; else return 'none';
	}),'ptall','style','display');


	confchangesE = combine_eb(function(next,current) {
		var ret = {nolonger:[],still:[],willbe:[]}
		if(current == null || next == null) return ret;
		var cconf = current.paperConflicts.sort();
		var nconf = next.paperConflicts.sort();
		var i=0, j=0;
		while(i<cconf.length || j<nconf.length) {
			if(i==cconf.length) {
				ret.willbe.push(nconf[j]);			
				j++;
			}
			else if(j==nconf.length) {
				ret.nolonger.push(cconf[i]);
				i++;
			}
			else if(cconf[i]==nconf[j]) {
				ret.still.push(cconf[i]);
				i++; j++;
			}
			else if(cconf[i] < nconf[j]) {
				ret.nolonger.push(cconf[i]);
				i++;
			}
			else {
			    	ret.willbe.push(nconf[j]);
				j++;
			}
		}
		return ret;
	},controlBox.events.next,controlBox.behaviors.current);

	function getclist(l,nobody) {
	    var cl = fold(function(v, acc) {return (acc == 'Nobody') ? v : acc+', '+v;},'Nobody',l);
	    if (!nobody && cl=='Nobody')
		cl = '';
	    return cl;
	}

	insertDomE(confchangesE.transform_e(function(ccb) {return getclist(ccb.nolonger,true);}),'nlconf','beginning');
	insertDomE(confchangesE.transform_e(function(ccb) {return getclist(ccb.still,true);}),'stillconf','beginning');
	insertDomE(confchangesE.transform_e(function(ccb) {return getclist(ccb.willbe,true);}),'newconf','beginning');


	insertDomE(controlBox.events.pInfo.transform_e(
		    function(paper) {
          return DIV({className:'summary-box '+paper.reviewStats.reviewRange},paper.reviewStats.reviewRange);}),'summary');
	insertDomE(controlBox.events.pInfo.transform_e(function(paper) {return H2('#'+paper.id+': '+paper.title);}),'ptitle');
	insertDomE(controlBox.events.pInfo.transform_e(function(paper) {return H4(paper.author);}),'pauthor');
	insertDomE(controlBox.events.pInfo.transform_e(function(paper) {return SPAN(
					fold(function(v, acc) {
						if (acc == '') 
							return v.fullname;
						else
							return acc + ', ' + v.fullname;
					},'',paper.conflicts));}),'pconf');
	insertDomE(controlBox.events.pInfo.transform_e(function(paper) {return paper.target.description + ' ('+(paper.othercats ? 'Loose' : 'Tight')+')';}),'ptgt');
	insertDomE(controlBox.events.pInfo.transform_e(function(paper) {return TABLE({className:'key-value'},
	    map(function(r) {return TR(TH(r.name),TD(r.submitted ? r.overall+'/'+r.expertise : ''));}, paper.reviewsInfo));}),'prevs');


	var previewB = switch_b(controlBox.behaviors.view.transform_b(function(cv) {
		return cv == 'starting' ? controlBox.behaviors.current : controlBox.behaviors.ordNext;
	}));
	var laterB = lift_b(function(prev,mi) {
	    if(prev == null || mi == null) return DIV();
	    var laters = [];
	    var evenlaters = [];
	    for(var i=0;i<mi.length;i++) {
	    	if(mi[i].paperID == prev.paperID) {
		    for(var j = i+1; j < mi.length && j < i+3; j++) {
			laters.push(H4('#'+mi[j].paperID+': '+mi[j].paperTitle));
		    }
		    for(var j = i+3; j < mi.length && j < i+7; j++) {
		    	evenlaters.push(H4('#'+mi[j].paperID));
		    }
		    if(mi.length >= i+7)
		        evenlaters.push(H4('...'));
		    return SPAN(DIV({className:'later'},laters),evenlaters);
		}
	    }
	    return DIV();
	},previewB,controlBox.events.meetingInfo.startsWith(null));

	insertDomB(previewB.transform_b(function(_) {return _ ? H4('#'+_.paperID+': '+_.paperTitle) : ''}),'ntitle');
	insertDomB(previewB.transform_b(function(_) {return _ ? P({className:'authors'},_.paperAuthors) : ''}),'nauthor');
	insertValueB(previewB.transform_b(function(_) {return _ ? (_.paperConflicts.length ? 'block' : 'none')  : 'none'}),'nconfhead','style','display');
	insertDomB(previewB.transform_b(function(_) {return _ ? getclist(_.paperConflicts) : '';}),'nconf');
	insertDomB(laterB,'later');

	insertDomE(controlBox.events.next.transform_e(function(_) {return H2('#'+_.paperID+': '+_.paperTitle);}),'stitle');
	insertDomE(controlBox.events.next.transform_e(function(_) {return H4(_.paperAuthors);}),'sauthor');

	insertValueB(controlBox.behaviors.view.transform_b(function(_) {return (_ == 'starting' ? 'block' : 'none');}),'starting','style','display');
	insertValueB(controlBox.behaviors.view.transform_b(function(_) {return (_ == 'switching' ? 'block' : 'none');}),'switching','style','display');
	insertValueB(controlBox.behaviors.view.transform_b(function(_) {return (_ == 'current' ? 'block' : 'none');}),'current','style','display');
	insertValueB(controlBox.behaviors.showPrev.transform_b(function(show) {return show ? 'block' : 'none';}),'preview-box','style','display');
	onLoadTimeE.sendEvent('loaded!');
}
