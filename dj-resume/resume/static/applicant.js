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

function makeLetterTable(basicInfo,appInfo) {
	var reqnew = new CombinedInputWidget([
			new TextInputWidget('',30),
			new TextInputWidget('',40),
			new TextInputWidget('',20)],
			function(name,inst,email) {return [TD(name),TD(inst),TD(email)];})
	    .withButton(new ButtonWidget(appInfo.position.autoemail ? 'Add Reference' : 'Enter Reference'),function(ci,btn) {return [TR(ci,TD(btn))];})
		.serverSaving(function(val) {
			return genRequest(
				{url:'Submitter/requestReference',
				fields:{name:val[0],institution:val[1],email:val[2]}});
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
              ? TR(TD(ref.name),TD(ref.institution),TD(ref.email),
                   TD(ref.submitted?'Yes':'No'))
              : TR(TD(ref.name),TD(ref.institution),TD(ref.email));
          },refs);}),
					reqnew.dom
				)));
}

function makeAppTable(basicInfo,appInfo) {
	var comps = toObj(appInfo.components,function(c) {return c.typeID;});
	var ciWidgets = [];
	var statementDoms = [];
	map(function(c) {
		if(c.type == 'statement') {
			var subWidg = INPUT({type:'submit',value:'OK'});
			var expandA = new ToggleWidget('[+]','[-]'); 
			var svisB = expandA.behaviors.toggled.transform_b(function(t) {return {className:'subnew',style:{display:(t ? 'block':'none')}};});
			var stmtDivB = DIVB(svisB,
				FORM({target:'stmtsub',action:'Submitter/submitStatement',method:'post',encoding:'multipart/form-data'},
					INPUT({type:'hidden',name:'cookie'}),
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
		else {
			ciWidgets.push(new ContactInfoRowWidget(c,comps[c.id]));
		}
	},basicInfo.components);
	
	var ciTblB = new CombinedInputWidget(ciWidgets,function() {return TABLEB({className:'key-value'},TBODYB(slice (arguments,0)));})
						.serverSaving(
							function(cifs) {
								var fields = {};
								map(function(c) {fields['comp-'+c.id] = c.value;},cifs);
								return genRequest({
									url:'Submitter/submitContactInfo',
									fields:fields});
						}).dom;

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

  onBelayReady(function() {
    console.log('Belay is ready: ', launchInfo);

    var onLoadTimeE = receiver_e();

    var exceptsE = captureServerExcepts(); 
    exceptsE.filter_e(function(_) {return _.value == 'denied';}).transform_e(function(_) {window.location='login.html?expired=true'});

    var demoEventsE = receiver_e();
    document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);})};

    var stmtSubE = iframeLoad_e('stmtsub',exceptsE);

    var basicInfoE = getE(onLoadTimeE.constant_e(launchInfo)); 
    var basicInfoB = basicInfoE.startsWith(null);
    //var basicInfoE = getBasicInfoE(onLoadTimeE);
    //var basicInfoB = basicInfoE.startsWith(null);

    basicInfoE.transform_e(function(bi) {setHeadAndTitle(bi,'Edit Application',A({href:'login.html?logout='},'Log Out'));});

    var appInfoB = merge_e(getFilteredWSO_e(onLoadTimeE.constant_e(genRequest(
        {url:'Submitter/get',
        fields:{}}))),
      stmtSubE.filter_e(noErrors).transform_e(function(ssc) {return ssc.app;})).startsWith(null);

    insertDomB(appInfoB.lift_b(function(info) {
      if (info && info.position && info.position.name) {
        return "You are applying for the position of " + info.position.name + ".";
      }
      else {
        return "";
      }
    }),'position');

    var contcompB = lift_b(function(bi,ai) {return (ai && bi) ? makeAppTable(bi,ai): [DIVB(),DIVB()];},
            basicInfoB,appInfoB);
    insertDomB(switch_b(contcompB.transform_b(function(_) {return _[0];})),'contact');
    insertDomB(switch_b(contcompB.transform_b(function(_) {return _[1];})),'materials');
    insertDomB(switch_b(lift_b(function(bi,ai) {return (ai && bi) ? makeLetterTable(bi,ai) : DIVB();},
      basicInfoB,appInfoB)),'letters');
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
