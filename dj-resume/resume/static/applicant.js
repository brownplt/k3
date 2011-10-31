function makeIntListRange(i,max) {
  if(i > max) 
    return [];
  
  var ret = makeIntListRange(i+1,max);
  ret.push(i);
  return ret;
}


function asOptions(arr) {
  return map(function(a) {
    return OPTION(a);
  },arr);
}

function YearMonthWidget() {
  return new CombinedInputWidget([new SelectWidget('Year',asOptions(__YEARS)),
				  new SelectWidget('Month',asOptions(map(function(mo) {
				    return mo < 10 ? '0' + mo : mo;},  __MONTHS)))]);
}

__YEARS = makeIntListRange(1970,2010);
__MONTHS = makeIntListRange(1,12);
__DAYS = makeIntListRange(1,31);

function ContactInfoRowWidget(ct,comp) {
  if(ct.type == 'contactlong')
    TextAreaWidget.apply(this,[(comp ? comp.value : ''),5,20]);
  else if(ct.type == 'contactshort')
    TextInputWidget.apply(this,[(comp ? comp.value : ''),20]);
  else
    TextInputWidget.apply(this,[(comp ? comp.value : ''),40]);
  this.dom = TR(TH(ct.name),TD(this.dom));
  this.behaviors.value = this.behaviors.value.transform_b(function(v) {return {id:ct.id,value:v};});
}

/**
   Scores is a list of components that have component_type test_score
   The type_id tells what kind of score we're dealing with (i.e. which
   test, GRE Verbal, TOEFL?
*/
function makeScoreList(scores, type_id) {
  return new ModListWidget(scores,
			   TR(TH('Score'),TH('Date'),TH('Verified?')),
			   function(obj) {
    ret = new ButtonInputWidget([],
	{del:new LinkWidget('Remove')},
				function() {return obj;},
				function(_,bob) {
				  return TR(TD(obj.value), 
					    TD(obj.date),
					    TD(obj.verified ? 'Yes' : 'No'),
					    TD(obj.verified ? '' :
					       bob.del));
				});
    ret.events.del = 
      getFilteredWSO_e(
		       ret.events.del.transform_e(function(score) {
			 return genRequest({url:'Submitter/removeScore',
						  fields:{cookie:authCookie,
								   score_id:score.id}});
		       }));
    return ret;
  },
			   function() {
			     return new ButtonInputWidget(
							  [new TextInputWidget('',3),
							   new YearMonthWidget(),
							   new ConstantInputWidget(false),
							   new ConstantInputWidget(0)],
			     {value:new ButtonWidget('Add')},
							  function(a,b,c) {
							    return {value:a,
									    date:b.join('-'),
									    verified:false,
									    typeID:type_id};},
							  function(is,bs) {
							    return TR(TD(is[0]),
								      TD(is[1]),
								      TD(is[2]),
								      TD(is[3]),
								      TD(bs.value));}).
			       serverSaving(function(score) {
				 return genRequest({url:'Submitter/addScore',
							  fields:{cookie:authCookie,
									   value:score.value,
									   date:score.date,
									   verified:false,
									   type_id:score.typeID}});
			       }, true);   
			   }).dom;
}

function makeLetterTable(basicInfo,appInfo) {
  var reqnew = new CombinedInputWidget([
					new TextInputWidget('',30),
					new TextInputWidget('',40),
					new TextInputWidget('',20)],
				       function(name,inst,email) {return [TD(name),TD(inst),TD(email)];})
    .withButton(new ButtonWidget(appInfo.position.autoemail ? 'Request New' : 'Enter Reference'),function(ci,btn) {return [TR(ci,TD(btn))];})
    .serverSaving(function(val) {
      return genRequest(
      {url:'Submitter/requestReference',
	     fields:{cookie:authCookie,name:val[0],institution:val[1],email:val[2]}});
    });

  // Clear the input table
  reqnew.events.serverResponse.snapshot(reqnew.behaviors.inputElems)
    .lift_e(function(elts) { map(function(elt) { elt.value = ''; },elts); });

  var newLettersE = reqnew.events.serverResponse.filter_e(noErrors);
  var refsB = collect_b(appInfo.references,newLettersE,function(newref,existing) {return existing.concat([newref]);});
  var errorB = reqnew.events.serverResponse.transform_e(resultTrans(appInfo.position.autoemail ? 'Your letter writer has been contacted.' : '')).startsWith(SPAN());

  return DIVB(
	      errorB,
	      TABLEB({className:'input-table'},
		     appInfo.position.autoemail
		     ? THEAD(TR(TH('Name'),TH('Institution(s)'),TH('Email'),
				TH('Received?')))
		     : THEAD(TR(TH('Name'),TH('Institution(s)'),TH('Email'))),
		     TBODYB(
			    refsB.transform_b(function(refs) { return map(function(ref) {
			      return appInfo.position.autoemail
				? TR(TD(A({href:'letter.html?code='+ref.code},ref.name)),
				     TD(ref.email),
				     TD(ref.submitted?'Yes':'No'))
				: TR(TD(A({href:'letter.html?code='+ref.code},ref.name)),
				     TD(ref.institution),
				     TD(ref.email));
			    },refs);}),
			    reqnew.dom
			    )));
}

function submitTranscriptWidget(institution, appInfo) {
  return institution.transcript_official ?
    DIV('Official Received')
    :
    DIV({className:'stmtsub'},
	     (institution.lastSubmitted ? 
	      DIV('Submitted ' + institution.lastSubmittedStr + '.  Uploading will overwrite') 
	      :
	      DIV('Not submitted')),
	     FORM({enctype:'multipart/form-data',
			     encoding:'multipart/form-data',
			     action:'Submitter/submitTranscript',
			     method:'post',
			     target:'uptranscript'},
		  INPUT({type:'hidden',name:'id',value:institution.id}),
		  INPUT({type:'hidden',name:'cookie',value:authCookie}),
		  INPUT({type:'file',name:'transcript'}),
		  INPUT({type:'submit',value:'Upload'})));
}

function createInstitutionsDOM(institutions, basicInfo, appInfo) {
  return new ModListWidget(institutions,
			   TR(TH('Name'),TH('From'),TH('To'),TH('Major'),TH('Degree'),
			      TH('GPA'),TH('Out of'),TH('Transcript')),
			   function(inst) {
    ret = new ButtonInputWidget([],
	{del:new LinkWidget('Remove')},
			       function() {return inst;},
			       function(_,widg) {
				 return TR(TD(inst.name),
					   TD(inst.start_date),
					   TD(inst.end_date),
					   TD(inst.major),
					   TD(inst.degree.shortform),
					   TD(inst.gpa),
					   TD(inst.gpa_max),
					   submitTranscriptWidget(inst,appInfo),
					   TD(inst.transcript_official? '' : widg.del));
			       });
    ret.events.del = 
      getFilteredWSO_e(ret.events.del.transform_e(function(inst) {
	return genRequest({url:'Submitter/removeInstitution',
				 fields:{cookie:authCookie,
						  institution_id:inst.id}});
      }));
    return ret;
  }, //closes second arg to ModListWidget
			   function() {
			     return new ButtonInputWidget(
							  [new TextInputWidget('',10), //name
							   YearMonthWidget(),
							   YearMonthWidget(),
							   new TextInputWidget('',10), //major
							   new SelectWidget('--',
									    map(function(deg) {
									      return OPTION({value:deg.id},deg.shortform);
									      },basicInfo.degrees)), //degree
							   new TextInputWidget('',4),  // gpa
							   new TextInputWidget('',4),
							   new ConstantInputWidget(false)], // gpa_max
			     {value:new ButtonWidget('Add')},
							  function(a,b,c,d,e,f,g) {
							    return {
							    name:a,
								   start_date:b.join('-'),
								   end_date:c.join('-'),
								   major:d,
								   degree:e,
								   gpa:f,
								   gpa_max:g};},
							  function(is,bs) {
							    return TR(TD(is[0]),
								      TD(is[1]),
								      TD(is[2]),
								      TD(is[3]),
								      TD(is[4]),
								      TD(is[5]),
								      TD(is[6]),
								      TD(is[7]),
								      TD(bs.value));
							  }).
			       serverSaving(function(inst) {
				 return genRequest({url: 'Submitter/addInstitution',
							   fields:{cookie:authCookie,
									    name:inst.name,
									    start_date:inst.start_date,
									    end_date:inst.end_date,
									    major:inst.major,
									    degree_id:inst.degree,
									    gpa:inst.gpa,
									    gpa_max:inst.gpa_max}});
			       }, true);
			     
			   }).dom
							   
}

function createInstitutionsDOMa(institutions, basicInfo, appInfo) {
  return DIVB(
	     map(function(institution) {
	       return TABLE({className:'key-value'},
			    TR(TH("Name:"),TD(institution.name)),
			    TR(TH("Attended:"),TD(institution.start_date + 
						  " to " + 
						  institution.end_date)),
			    TR(TH("Major:"),TD(institution.major)),
			    TR(TH("Degree:"),TD(institution.degree.shortform)),
			    TR(TH("GPA:"),TD(institution.gpa + 
					     " of " + 
					     institution.gpa_max)),
			    TR(TH("Transcript:"),TD(institution.lastSubmitted == 0 ?
						    DIV('None yet - upload here',
							submitTranscriptWidget(institution))
						    :
						    DIV('Last submitted: ' + 
							institution.lastSubmittedStr,
						    DIV('Submit new (overwrites)',
							submitTranscriptWidget(institution))
							))),
			    TR(TH("Transcript Official?"), TD(institution.lastSubmitted == 0 ?
							      "N/A"
							      :
							      (institution.transcript_official ?
							       "YES" : "NO"))));
	       
	     },institutions));
}
		 

function makeInstitutionsTable(basicInfo, appInfo) {
  var institutions = appInfo.institutions;
  var existingInstitutions = createInstitutionsDOM(institutions, basicInfo, appInfo);
  //var newInstitution = createNewInstitutionDOM(institutions, basicInfo, appInfo);
  return DIVB(existingInstitutions);
}

function makeAppTable(basicInfo,appInfo) {
  var comps = toObj(appInfo.components,function(c) {return c.typeID;});
  var ciWidgets = [];
  var statementDoms = [];
  var scoreDoms = [];
  map(function(c) {
    if(c.type == 'statement') {
      var subWidg = INPUT({type:'submit',value:'OK'});
      var expandA = new ToggleWidget('[+]','[-]'); 
      var svisB = expandA.behaviors.toggled.transform_b(function(t) {return {className:'subnew',style:{display:(t ? 'block':'none')}};});
      var stmtDivB = DIVB(svisB,
			  FORM({target:'stmtsub',action:'Submitter/submitStatement',method:'post',encoding:'multipart/form-data'},
			       INPUT({type:'hidden',name:'cookie',value:authCookie}),
			       INPUT({type:'hidden',name:'comp',value:c.id}),
			       SPAN('Submit New: ',
				    IMG({src:'images/pdficon_small.gif',alt:'[PDF Files accepted]'}),
				    IMG({src:'images/word_icon_small.gif',alt:'[MS Word Files accepted]'}),
				    ' ',INPUT({type:'file',name:'newcomp'}),subWidg)));
      statementDoms.push(
			 TRB(
			     TH(c.name),
			     TD(comps[c.id] ? SPAN('Last submitted '+comps[c.id].lastSubmittedStr+'; file size '+comps[c.id].value+' bytes') : SPAN('Not Yet Submitted ')),
			     TDB(expandA.dom)));
      statementDoms.push(TRB(TDB({colSpan:3},stmtDivB)));
    }
    else if (c.type == 'test_score') {
      var scores = filter(function(ai_comp) {
	return ai_comp.typeID == c.id;
      }, appInfo.components);

      scoreDoms.push(H4(c.name));
      scoreDoms.push(makeScoreList(scores, c.id));

    }
    else {
      ciWidgets.push(new ContactInfoRowWidget(c,comps[c.id]));
    }
  },basicInfo.components);
	
  var ciTblB = new CombinedInputWidget(ciWidgets,function() {return TABLEB({className:'key-value'},TBODYB(slice (arguments,0)));})
    .serverSaving(
		  function(cifs) {
		    var fields = {cookie:authCookie};
		    map(function(c) {fields['comp-'+c.id] = c.value;},cifs);
		    return genRequest({	url:'Submitter/submitContactInfo',
					      fields:fields});
		  }).dom;
  
  return [ciTblB,
	  TABLEB({className:'app-components'},TBODYB(statementDoms)),
	  TABLEB(TBODYB(scoreDoms))];
}

$(function() {

  var flapjax = flapjaxInit();

  var theFrame;

  function makeBelayFrame() {
    var frame = $('<iframe></iframe>');
    frame.attr({
      'src': COMMON.belayFrame,
      'name': 'belay'
    });
    frame.css({
      display: 'none',
      width: '1px',
      height: '1px'
    });
    theFrame = frame;
    return frame;
  }
  function addFrame(frame) {
    $('#main').append(frame);
  }

  window.belay.belayInit(makeBelayFrame, addFrame);

  onBelayReady(function() {
    console.log('Belay is ready: ', launchInfo);
    launchInfo.get(function(r) {
      console.log('launched: ', r);
    });

  });

  ContactInfoRowWidget.prototype = new InputWidget();

  var onLoadTimeE = receiver_e();
  authCookie = getCookie('resumesession');
  var exceptsE = captureServerExcepts(); 
  exceptsE.filter_e(function(_) {return _.value == 'denied';}).transform_e(function(_) {window.location='login.html?expired=true'});

  var demoEventsE = receiver_e();
  document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);})};

  var stmtSubE = iframeLoad_e('stmtsub',exceptsE);
  var transSubE = iframeLoad_e('uptranscript',exceptsE);

  var basicInfoE = getBasicInfoE(onLoadTimeE);
  var basicInfoB = basicInfoE.startsWith(null);

  basicInfoE.transform_e(function(bi) {setHeadAndTitle(bi,'Edit Application',A({href:'login.html?logout='+authCookie},'Log Out'));});

  var appInfoB = merge_e(getFilteredWSO_e(onLoadTimeE.constant_e(genRequest(
					  {url:'Submitter/get',
						 fields:{cookie:authCookie}}))),
			 merge_e(stmtSubE.filter_e(noErrors).transform_e(function(ssc) {return ssc.app;}),
				 transSubE.filter_e(noErrors).transform_e(function(ssc) {return ssc.app;}))).startsWith(null);

  insertDomB(appInfoB.lift_b(function(info) {
    if (info && info.position && info.position.name) {
      //return "You are applying for the position of " + info.position.name + ".";
      return "";
    }
    else {
      return "";
    }
  }),'position');

  var contcompB = lift_b(function(bi,ai) {return (ai && bi) ? makeAppTable(bi,ai): [DIVB(),DIVB(),DIVB()];},
			 basicInfoB,appInfoB);
  var institutionsTableB = 
    lift_b(function(bi,ai) {return (ai && bi) ? makeInstitutionsTable(bi,ai): DIVB();},
	   basicInfoB, appInfoB);

  insertDomB(switch_b(contcompB.transform_b(function(_) {return _[0];})),'contact');
  insertDomB(switch_b(contcompB.transform_b(function(_) {return _[1];})),'materials');
  insertDomB(switch_b(contcompB.transform_b(function(_) {
    return _[2];})),'scores');
  insertDomB(switch_b(institutionsTableB),'institutions');
  insertDomB(switch_b(lift_b(function(bi,ai) {return (ai && bi) ? makeLetterTable(bi,ai) : DIVB();},
			     basicInfoB,appInfoB)),'letters');
  insertDomE(combine_eb(function(ssc,bi) {
    var rstr = 'Thank you for your submission!';
    if(!ssc.error)
      var rstr = 'We have received your '+ssc.component+'. '+rstr;
    return toResultDom(ssc,rstr);
  },stmtSubE,basicInfoB),'result');

  insertDomE(combine_eb(function(ssc,bi) {
    var rstr = 'Thank you for your submission!';
    if(!ssc.error)
      var rstr = 'We have received your transcript.  ' + rstr;
    return toResultDom(ssc,rstr);
  },transSubE,basicInfoB),'trans-result');
  
  onLoadTimeE.sendEvent('Loaded!');
  

});
