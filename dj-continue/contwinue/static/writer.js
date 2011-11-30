function makeDetailsTab(userInfo,paperInfo,basicInfo,authorText,extensions,errorsB) {
	var deadlineExts = toObj(extensions,function(e) {return e.typeID;});
	var getDeadline = function(compType) {
		if (deadlineExts[compType.id]) return deadlineExts[compType.id].until; else return compType.deadline;
	};
	var getDeadlineStr = function(compType) {
		if (deadlineExts[compType.id]) return deadlineExts[compType.id].untilStr; else return compType.deadlineStr;
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
			.serverSaving(function(title) {return genRequest({url:'Author/setTitle',fields:{cookie:authCookie,title:title}});})
			.toTableRow('Paper Title:');
	var authorWidget = new TextInputWidget(paperInfo.author,70)
			.serverSaving(function(author) {return genRequest({url:'Author/setAuthor',fields:{cookie:authCookie,author:author}});})
			.toTableRow('Author List:');
	var pcpWidget = new CheckboxWidget(paperInfo.pcpaper)
			.serverSaving(function(pcpaper) {
					return genRequest({url:'Author/setPcPaper',fields:{cookie:authCookie,pcpaper:(pcpaper ? 'yes' : 'no')}});})
			.toTableRow('PC Paper?');
	var twDom = '';
	if(targetables > 1) {
		var targetsel = new SelectWidget(paperInfo.target.id,map(function(dec) {return OPTION({value:dec.id},dec.description);},filter(function (d) {return d.targetable;},basicInfo.decisions)));
		var othercats = new CheckboxWidget(paperInfo.othercats);
		var targetWidget = new CombinedInputWidget([targetsel,othercats],function(tsdom,ocdom) {
							return DIV(tsdom,BR(),ocdom,'Yes, I/we would like the paper considered in other categories also.');
							}).serverSaving(function(to) {
								return genRequest({url:'Author/setTarget',fields:{cookie:authCookie,target:to[0],othercats:(to[1] ? 'yes' : 'no')}});
							}).toTableRow('Target Category:');
		twDom = targetWidget.dom;
	}
	var topicsWidget = new CheckboxListWidget(map(function(t) {return {k:t.id,v:t.name};},basicInfo.topics),
												map(function(t) {return t.id;},paperInfo.topics))
							.serverSaving(function(tids) {
								return genRequest({url:'Author/setTopics',fields:{cookie:authCookie,topics:tids}});})
							.toTableRow('Topic(s):');
	var errorsDomB = errorsB.transform_b(function(e) {if(e.error) return P({className:'error'},e.error); else return SPAN();});
	return DIVB(
		((missinginfo == 'Submission Complete') ? '' : P('Please finish providing information about your submission.')),
		H3('General Information'),
		TABLE({className:'key-value'},TBODY(
			TR(TH('Contact:'),TD(userInfo.fullname,' <',userInfo.email,'>')),
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
		FORM({target:'subtarget',action:'Author/updateComponents',method:'post',encoding:'multipart/form-data'},
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
	var onLoadTimeE = receiver_e();
	var exceptsE = captureServerExcepts();
	handleExcepts(exceptsE);
	var basicInfoE = getBasicInfoE(onLoadTimeE);
	basicInfoE.transform_e(function(bi) {
		document.title = bi.info.shortname + ' - Paper Submission';
  });
	doConfHead(basicInfoE);
	authCookie = $URL('cookie');
	$('logout_tab').href = 'login.html?logout='+authCookie;
	var curUserE = getCurUserE(onLoadTimeE,authCookie);
	doLoginDivB(curUserE);
	var detailsQueryE = curUserE.transform_e(function(cu) {
		return genRequest(
			{url: 'Author/get',
			fields: {cookie:authCookie}});
		});
	var perE = iframeLoad_e('subtarget');
	var perB = perE.startsWith(true);
	var allDetailsQuerysE = merge_e(snapshot_e(perE,detailsQueryE.startsWith(null)),detailsQueryE);
	var detailsInfoE = getFilteredWSO_e(allDetailsQuerysE);
	var deadextE = getFilteredWSO_e(detailsInfoE.transform_e(function(di) {
		return genRequest(
			{url: 'Author/getDeadlineExts',
			fields: {cookie:authCookie,key:'paperID',val:di.id}});
		}));
	var authorTextE = getFilteredWSO_e(onLoadTimeE.constant_e(
			genRequest({url: 'getAuthorText',
			 fields: {cookie:authCookie}})));
	var detailsTabB = lift_b(function(cu,di,bi,at,de) {
			if (cu && di && bi && at && de)
				return makeDetailsTab(cu,di,bi,at,de,perB); else return constant_b(getLoadingDiv());},
			curUserE.startsWith(null),detailsInfoE.startsWith(null),basicInfoE.startsWith(null),authorTextE.startsWith(null),deadextE.startsWith(null)); 
	insertDomB(switch_b(detailsTabB),'main_content');
	onLoadTimeE.sendEvent('loaded!');
}
