function makeNameUpdateBoxes(info, updateCap) {
  var nameBoxesB = DIVB([
    TR(['First Name: ', TD(new TextInputWidget(info.firstname, 20)
      .belayServerSaving(function(v) {
        console.log('saving first name: ', v);
        return {'fields' : {'firstname' : v}};
      }, true, updateCap).dom)]),
    TR(['Last Name: ', TD(new TextInputWidget(info.lastname, 20)
      .belayServerSaving(function(v) {
        console.log('saving last name: ', v);
        return {'fields' : {'lastname' : v}};
      }, true, updateCap).dom)])
  ]);
  insertDomB(nameBoxesB, 'nameboxes');
}

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

function makeLetterTable(basicInfo,appInfo,refReq) {
  var verifier = function(args) {
    return args.email !== '' && args.name !== '' && args.institution !== '';
  };
  var toReqFn = function(val) {
			return genRequest(
				{fields:{name:val[0],institution:val[1],email:val[2]}});
  };

	var reqnew = new CombinedInputWidget([
			new TextInputWidget('',30),
			new TextInputWidget('',40),
			new TextInputWidget('',20)],
			function(name,inst,email) {return [TD(name),TD(inst),TD(email)];})
	    .withButton(new ButtonWidget(appInfo.position.autoemail ? 'Add Reference' : 'Enter Reference'),function(ci,btn) {return [TR(ci,TD(btn))];})
		.belayServerSaving(toReqFn, true, refReq, verifier);

  // Clear the input table
	reqnew.events.serverResponse.snapshot(reqnew.behaviors.inputElems)
  .lift_e(function(elts) { map(function(elt) { elt.value = ''; },elts); });

	var newLettersE = reqnew.events.serverResponse.filter_e(noErrors);
	var refsB = collect_b(appInfo.references,newLettersE,function(newref,existing) {return existing.concat([newref]);});

  var serverErrorE = reqnew.events.serverResponse.transform_e(resultTrans(appInfo.position.autoemail ? 'Your letter writer has been contacted.' : ''));
  var clientErrorE = reqnew.events.value.transform_e(toReqFn)
    .filter_e(function(v) {return !verifier(v.fields);})
    .transform_e(function(v) {return toResultDom({error : 'Please provide values for name, institution, and email'}, ''); })
  var errorB = serverErrorE.merge_e(clientErrorE).startsWith(SPAN());

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
              ? TR(TD(ref.name),TD(ref.institution),TD(ref.email),
                   TD(ref.submitted?'Yes':'No'))
              : TR(TD(ref.name),TD(ref.institution),TD(ref.email));
          },refs);}),
					reqnew.dom
				)));
}

function makeAppTable(basicInfo,appInfo, submitContactInfo, submitStatement) {
	var comps = toObj(appInfo.components,function(c) {return c.typeID;});
	var ciWidgets = [];
	var statementDoms = [];
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
					TD(comps[c.id] ? SPAN('Last submitted '+comps[c.id].lastSubmittedStr+'; file size '+comps[c.id].value+' bytes') : SPAN('Not Yet Submitted ')),
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
								map(function(c) {fields['comp-'+c.id] = c.value;},cifs);
								return genRequest({
									url:'Submitter/submitContactInfo',
									fields:fields});
						}, true, submitContactInfo).dom;
	return [ciTblB,TABLEB({className:'app-components'},TBODYB(statementDoms))];
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

//    basicInfoE.transform_e(function(bi) {setHeadAndTitle(bi,'Edit Application',A({href:'login.html?logout='},'Log Out'));});

    var submitterGetE = getE(launchE.transform_e(function(pd) { return pd.get; }));
    var appInfoB = merge_e(submitterGetE,
      stmtSubE.filter_e(noErrors).transform_e(function(ssc) {return ssc.app;})).startsWith(null);

    launchE.transform_e(function(li) {
      appInfoB.lift_b(function(info) {
        if (info !== null) {
          console.log('calling makeNameUpdateBoxes: ', li.updateName);
          makeNameUpdateBoxes(info, li.updateName);
        }
      });
    });

    insertDomB(appInfoB.lift_b(function(info) {
      if (info && info.position && info.position.name) {
        return "You are applying for the position of " + info.position.name + ".";
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

    var refReqE = launchE.transform_e(function(pd) { return pd.requestReference; });
    var refReqB = refReqE.startsWith(null);
    insertDomB(switch_b(lift_b(function(bi,ai,refReq) {return (ai && bi && refReq) ? makeLetterTable(bi,ai,refReq) : DIVB();},
      basicInfoB,appInfoB, refReqB)),'letters');
    insertDomE(combine_eb(function(ssc,bi) {
          var rstr = 'Thank you for your submission!';
          if(!ssc.error)
            var rstr = 'We have received your '+ssc.component+'. '+rstr;
          return toResultDom(ssc,rstr);
    },stmtSubE,basicInfoB),'result');
    onLoadTimeE.sendEvent('Loaded!');
    ContactInfoRowWidget.prototype = new InputWidget();
  });


});
