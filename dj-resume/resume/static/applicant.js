function ContactInfoRowWidget(ct,comp) {
	if(ct.type == 'contactlong') {
	    TextAreaWidget.apply(this,[(comp ? comp.value : ''),5,40]);
	    this.dom = TR(TH(ct.name),TD(this.dom, BR(), SPAN({className: 'description'}, 'You can enter information that doesn\'t fit other categories here.')));
  }
	else if(ct.type == 'contactshort') {
	    TextInputWidget.apply(this,[(comp ? comp.value : ''),20]);
	    this.dom = TR(TH(ct.name),TD(this.dom));
  }
	else {
	    TextInputWidget.apply(this,[(comp ? comp.value : ''),40]);
	    this.dom = TR(TH(ct.name),TD(this.dom));
  }
	this.behaviors.value = this.behaviors.value.transform_b(function(v) {return {id:ct.id,value:v};});
}

function makeLetterTable(basicInfo,appInfo,refReq,reminders) {
  var minLetters = basicInfo.minLetters || 3;
  var verifier = function(args) {
    return args.email !== '' && args.name !== '' && args.institution !== '';
  };
  var nameVerifier = function() {
    return appInfo.firstname != '' && appInfo.lastname != '';
  };
  var toReqFn = function(val) {
			return genRequest(
				{fields:{name:val[0],institution:val[1],email:val[2]}});
  };

	var reqnew = new CombinedInputWidget([
			new TextInputWidget('',30),
			new TextInputWidget('',40),
			new TextInputWidget('',20)],
			function(name,inst,email) {return [TD(name),TD(inst),TD(email), SPAN()];})
	    .withButton(new ButtonWidget(appInfo.position.autoemail ? 'Add Reference' : 'Enter Reference'),function(ci,btn) {return [TR(ci,TD(btn))];})
		.belayServerSaving(toReqFn, true, refReq, function(args) { return verifier(args) && nameVerifier(); });

  var allNewLettersE = receiver_e();
  var allErrorsE = receiver_e();
  var mkNewReq = function() {
    var reqnew = new CombinedInputWidget([
			new TextInputWidget('',30),
			new TextInputWidget('',40),
			new TextInputWidget('',20)],
			function(name,inst,email) {return [TD(name),TD(inst),TD(email), SPAN()];})
	    .withButton(new ButtonWidget(appInfo.position.autoemail ? 'Add Reference' : 'Enter Reference'),function(ci,btn) {return [TR(ci,TD(btn))];})
		.belayServerSaving(toReqFn, true, refReq, function(args) { return verifier(args) && nameVerifier(); });
    var serverErrorE = reqnew.events.serverResponse.transform_e(resultTrans(appInfo.position.autoemail ? 'Your letter writer has been contacted.' : ''));
    var inputErrorE = reqnew.events.value.transform_e(toReqFn)
      .filter_e(function(v) {return !verifier(v.fields);})
      .transform_e(function(v) {return toResultDom({error : 'Please provide values for name, institution, and email'}, ''); })
    var nameErrorE = reqnew.events.value.transform_e(toReqFn)
      .filter_e(function(v) {return !nameVerifier(); })
      .transform_e(function(v) {return toResultDom({error : 'Please enter your first and last name so we can tell your reference who you are.'}, ''); })
    var errorsE = merge_e(serverErrorE, inputErrorE, nameErrorE).transform_e(function(v) { allErrorsE.sendEvent(v); });
	  var newLettersE = reqnew.events.serverResponse.filter_e(noErrors).transform_e(function(v) { allNewLettersE.sendEvent(v) });
    // Clear the input table
  	reqnew.events.serverResponse.snapshot(reqnew.behaviors.inputElems)
    .lift_e(function(elts) { map(function(elt) { elt.value = ''; },elts); });
    return reqnew.dom;
  }; 
  
	var refsB = collect_b(appInfo.references,allNewLettersE,function(newref,existing) {return existing.concat([newref]);});
  insertDomE(allErrorsE.transform_e(function(dom) {
    setTimeout(function() { $(dom).fadeOut(3000) }, 1000);
    return dom;
  }),'letter-result');

	return DIVB(
			TABLEB({className:'input-table'},
				appInfo.position.autoemail
          ? THEAD(TR(TH('Name'),TH('Institution(s)'),TH('Email'),
                  TH('Received?')))
          : THEAD(TR(TH('Name'),TH('Institution(s)'),TH('Email'))),
				TBODYB(
					refsB.transform_b(function(refs) {
            var existing = map(function(ref) {
              var remindCap = reminders[ref.email];
              if (!remindCap) { remindCap = ref.reminder; }
              var reminder = INPUT({disabled:ref.submitted,type:'button',value:'Send a Reminder'});
              var remindE = clicks_e(reminder).transform_e(function(_) { return [remindCap, {}]; });
              postE(remindE).transform_e(resultTrans('Your letter writer has been contacted.')).transform_e(function(v) { allErrorsE.sendEvent(v); });
              return appInfo.position.autoemail
                ? TR(TD(ref.name),TD(ref.institution),TD(ref.email),
                     TD(ref.submitted?'Yes':'No'),
                     ref.submitted ? SPAN() : reminder)
                : TR(TD(ref.name),TD(ref.institution),TD(ref.email), SPAN(), 
                     ref.submitted ? SPAN() : reminder);
            },refs);
            var existingLen = existing.length;
            for(var i = existingLen; i < minLetters; i++) {
              existing = existing.concat(mkNewReq());
            }
            if(existingLen >= minLetters) {
              existing = existing.concat(mkNewReq());
            }
            return existing;
          })
				)));
}

function makeAppTable(basicInfo, appInfo, submitContactInfo, submitStatement) {
	var comps = toObj(appInfo.components,function(c) {return c.typeID;});
	var ciWidgets = [];
	var statementDoms = [];
        ciWidgets.push(new ContactInfoRowWidget({ id: 'firstname', name: 'First Name', type: 'contactshort' },
                                                { value: appInfo.firstname }))
        ciWidgets.push(new ContactInfoRowWidget({ id: 'lastname', name: 'Last Name', type: 'contactshort' },
                                                { value: appInfo.lastname }));
	map(function(c) {
		if(c.type == 'statement') {
			var subWidg = INPUT({type:'submit',value:'OK'});
      var fileInputWidg = INPUT({type:'file',name:'statement'});
			var expandA = new ToggleWidget('[+]','[-]'); 
			var svisB = expandA.behaviors.toggled.transform_b(function(t) {return {className:'subnew',style:{display:(t ? 'block':'none')}};});
			var stmtDivB = DIVB(svisB,
				//FORM({target:'stmtsub',action:'Submitter/submitStatement',method:'post',encoding:'multipart/form-data'},
				FORM({target:'stmtsub',action:submitStatement.serialize(),method:'post',encoding:'multipart/form-data'},
					INPUT({type:'hidden',name:'comp',value:c.id}),
					SPAN('Submit New: ',
						IMG({src:'/static/images/pdficon_small.gif',alt:'[PDF Files accepted]'}),
						IMG({src:'/static/images/word_icon_small.gif',alt:'[MS Word Files accepted]'}),
						' ',fileInputWidg,subWidg)));
      console.log('stmtDivB: ', stmtDivB);
			statementDoms.push(
				TRB(
					TH(c.name),
					TD(comps[c.id] ? 
             DIV(SPAN('Submitted '+comps[c.id].lastSubmittedStr), 
                 BR(),
                 SPAN('File size '+comps[c.id].value+' bytes')) :
             SPAN('Not yet submitted ')),
					TDB(expandA.dom)));
			statementDoms.push(TRB(TDB({colSpan:3},stmtDivB)));
		}
		else {
			ciWidgets.push(new ContactInfoRowWidget(c,comps[c.id]));
		}
	},basicInfo.components);
	

	var ciTblB = new CombinedInputWidget(ciWidgets,function() {return TABLEB({className:'key-value'},TBODYB(slice (arguments,0)));})
						.belayServerSaving(
							function(cifs) {
								var fields = {};
								map(function(c) {
                  fields['comp-'+c.id] = c.value;
                  if(c.id === 'firstname') { appInfo.firstname = c.value; }
                  else if(c.id === 'lastname') { appInfo.lastname = c.value; }
                  else { comps[c.id] = c.value; }
                },cifs);
								return genRequest({fields:fields});
						}, true, submitContactInfo).dom;
	return [ciTblB,TABLEB({className:'app-components'},TBODYB(statementDoms)),appInfo];
}

$(function () {
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

  onBelayReady(function(readyBundle) {
    var launchInfo = readyBundle.launchInfo;
    var capServer = readyBundle.capServer;

    console.log('Belay is ready: ', launchInfo);

    var onLoadTimeE = receiver_e();

    var exceptsE = captureServerExcepts(); 
    exceptsE.filter_e(function(_) {return _.value == 'denied';}).transform_e(function(_) {window.location='login.html?expired=true'});

    var demoEventsE = receiver_e();
    document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);})};

    var stmtSubE = iframeLoad_e('stmtsub',exceptsE).transform_e(function(v){
      return capServer.dataPostProcess(toJSONString(v));
    });;

    var launchE = getE(onLoadTimeE.constant_e(launchInfo)); 
    var basicInfoE = getE(launchE.transform_e(function(pd) { return pd.getBasic; }));
    var basicInfoB = basicInfoE.startsWith(null);
    var remindersB = launchE.transform_e(function(li) { return li.reminders; }).startsWith({});

    basicInfoE.transform_e(function(bi) {
      COMMON.setContact(bi.contact);
    });

   

//    basicInfoE.transform_e(function(bi) {setHeadAndTitle(bi,'Edit Application',A({href:'login.html?logout='},'Log Out'));});

    var submitterGetE = getE(launchE.transform_e(function(pd) { return pd.get; }));
    var appInfoB = merge_e(submitterGetE,
      stmtSubE.filter_e(noErrors).transform_e(function(ssc) {return ssc.app;})).startsWith(null);

    insertDomB(DIVB({className: 'sub'}, appInfoB.lift_b(function(ai) { return ai ? ai.email : ""; })), 'title-email');

    insertDomB(appInfoB.lift_b(function(info) {
      if (info && info.position && info.position.name) {
        return "";
//        return "You are applying for the position of " + info.position.name + ".";
      }
      else {
        return "";
      }
    }),'position');

    var submitContactB = launchE.transform_e(function(pd){return pd.submitContactInfo;}).startsWith(null);
    var submitStatementB = launchE.transform_e(function(pd){return pd.submitStatement;}).startsWith(null);

    var contcompB = lift_b(function(bi,ai,submitC,submitS) {
      console.log('Building new contcompB out of: ', [bi, ai]);
      return (ai && bi && submitC && submitS) ? makeAppTable(bi,ai,submitC,submitS): [DIVB(),DIVB()];},
            basicInfoB,appInfoB,submitContactB, submitStatementB);
    insertDomB(switch_b(contcompB.transform_b(function(_) {return _[0];})),'contact');
    insertDomB(switch_b(contcompB.transform_b(function(_) {return _[1];})),'materials');
    var updatedAppInfoB = contcompB.transform_b(function(_) {return _[2];});

    var refReqE = launchE.transform_e(function(pd) { return pd.requestReference; });
    var refReqB = refReqE.startsWith(null);
    insertDomB(switch_b(lift_b(function(bi,ai,refReq,rms) {return (ai && bi && refReq && rms) ? makeLetterTable(bi,ai,refReq,rms) : DIVB();},
      basicInfoB,updatedAppInfoB, refReqB, remindersB)),'letters');
    insertDomE(combine_eb(function(ssc,bi) {
          var rstr = '';
          if(!ssc.error)
            var rstr = 'We have received your '+ssc.component+'. '+rstr;
          var result = toResultDom(ssc,rstr);
          setTimeout(function() { $(result).fadeOut(3000) }, 1000);
          return result;
    },stmtSubE,basicInfoB),'result');
    onLoadTimeE.sendEvent('Loaded!');
    ContactInfoRowWidget.prototype = new InputWidget();
  });


});
