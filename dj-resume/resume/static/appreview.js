var fieldsUnlocked = false;

var basicInfo = { position: [ { name: 'Loading...' } ] }; // total hack

function makePositionOption(position) {
  return OPTION({ value: position.id.toString() }, position.name);
};

function disableInputs(rootElement,isDisabled) {
  var elts = rootElement.getElementsByTagName('input');
  for (var ix = 0; ix < elts.length; ix++) { elts[ix].disabled = isDisabled; };
};

function makeUnsubmittedRequest(letter, requestReference) {
  var requestAgain = A({ href: 'javascript:undefined' }, "request again");

  var requestLine = SPAN({ style: { fontSize: 'smaller' } },
    letter.lastRequested ? "(last requested on " + letter.lastRequestedStr + 
                           "; " 
                         : "(not yet requested; ",
    requestAgain,")");


  belayGetWSO_E(extractEvent_e(requestAgain,'click').lift_e(function(_) {
    requestLine.innerHTML = "(request sent)";
    }).constant_e(genRequest({fields:{id:letter.id}})), requestReference);
  return requestLine;
};

$(function() {
	var flapjax = flapjaxInit();
	var exceptsE = captureServerExcepts(); 
	exceptsE.filter_e(function(_) {return _.value == 'denied';}).transform_e(function(_) {window.location='login.html?expired=true'});

	var onLoadTimeE = receiver_e();

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
    console.log('adding frame to document: ', document);
    $(document.body).append(frame);
    console.log('done adding frame to document: ', document);
  }

  console.log('before belayInit');
  window.belay.belayInit(makeBelayFrame, addFrame);

  onBelayReady(function(readyBundle) {
    console.log('belay is ready: ', readyBundle);
    var launchInfo = readyBundle.launchInfo;

    demoEventsE = receiver_e();
    document.startDemo = function(cb) {demoEventsE.transform_e(function(evt) {cb(evt);})};

    var curAuthE = getAuthE(onLoadTimeE);

    var basicInfoE = getE(onLoadTimeE.constant_e(launchInfo.getBasic));

    basicInfoE.lift_e(function(v) { console.log('basicInfo: ', v); basicInfo = v; });
    
    var appReloadsE = receiver_e();
    var getApplicantE = belayGetWSO_e(merge_e(onLoadTimeE,extractEvent_e('upletter','load')).constant_e(genRequest(
      {request:'get',asynchronous: false})), launchInfo.getApplicant);
    var applicantB = merge_e(getApplicantE, appReloadsE).startsWith({name:'',highlights:{},areas:[],gender:'Unknown',position: { name: 'Loading...' }, ethnicity:'zu',components:[],email:'',uname:'',refletters:[],reviews:[],hiddenunames:[]});
    
    var revsB = belayGetWSO_e(onLoadTimeE.constant_e(genRequest(
        {request:'get'})), launchInfo.getReviewers).startsWith([]);


    var myInitRevB = getE(onLoadTimeE.constant_e(launchInfo.getReview)).startsWith(null);

    var unlockEdits = extractEvent_e('unlockClassificationEdits','click')
    .collect_e(true /* initially disabled */,function(_,disabled) {
       demoEventsE.sendEvent({ action: 'fieldsUnlocked' });
      $('unlockClassificationEdits').src = !disabled 
        ? 'images/locked.png' : 'images/unlocked.png';
      return !disabled;
    });

    lift_e(function(basicInfo,curAuth) {
      console.log('inside ginormous lift_e: basicInfo = ', basicInfo);
      console.log('inside ginormous lift_e: curAuth = ', curAuth);
      applicantB.transform_b(function(a) {
          setHeadAndTitle(basicInfo,a.name,
        [A({href:'login.html?logout='},'Log Out'),
        A({href:'reviewer.html'},'Back to List')])});

      insertDomB(applicantB.transform_b(function(a) {return H2(a.name,DIV({className:'sub'},'application'));}),'appname');

      insertDomB(applicantB.transform_b(function(ai) {
        var widget = new CheckboxListWidget(
        map(function(a) {return {k:a.id,v:a.name};},basicInfo.areas),
        map(function(a) {return a.id;},ai.areas)	
          ).belayServerSaving(function(careas) {
        demoEventsE.sendEvent({action:'areaSet'});
        return genRequest({fields:{areas:careas}});
          }, false, launchInfo.setAreas).dom;

        disableInputs(widget,true);

        unlockEdits.lift_e(function(v) { disableInputs(widget,v); });
        return DIV(H4('area'),widget);
      }),'area','beginning');
    
      insertDomB(applicantB.transform_b(function(ai) {
        var widget = new SelectWidget(ai.gender,
        map(function(g) {return OPTION({value:g},g);},basicInfo.genders))
        .belayServerSaving(function(gen) {
            return genRequest({fields:{gender:gen}});}, false, launchInfo.changeApplicant).dom;
        widget.disabled = true;
        unlockEdits.lift_e(function(v) { widget.disabled = v; });

        return DIV(H4('gender'),widget);
      }),'gender','beginning');

      insertDomB(applicantB.transform_b(function(ai) {
        var widget = new SelectWidget(ai.position.id,
          map(makePositionOption,basicInfo.positions))
          .belayServerSaving(function(gen) {
            return genRequest({
              fields: { id: gen } }); 
          }, false, launchInfo.setPosition).dom;
        widget.disabled = true;
            
        unlockEdits.lift_e(function(v) { widget.disabled = v; });  
        return DIV(H4('position'),widget);
      }),'position','beginning');
                       
    
      insertDomB(applicantB.transform_b(function(ai) {
        var ethopts = [];
        for(var k in basicInfo.ethnicities)
          if (basicInfo.ethnicities.hasOwnProperty(k))
            ethopts.push(OPTION({value:k},basicInfo.ethnicities[k]));
        var widget = new SelectWidget(ai.ethname,ethopts).belayServerSaving(function(eth) {
          return genRequest({fields:{ethnicity:eth}});}, false, launchInfo.changeApplicant).dom;

        widget.disabled = true;
        unlockEdits.lift_e(function(v) { widget.disabled = v; });
        return DIV(H4('ethnicity'),widget);
      }),'ethnicity','beginning');

      appCompsB = applicantB.transform_b(function(ai) {
        var ret = {id:ai.id,contact:[],statements:[]};
        var acs =  toObj(ai.components,function(c) {return c.typeID;});
        map(function(comp) {
            var cv = objCopy(comp);
            if(comp.type == 'statement') {
                cv.submitted = (acs[comp.id] ? acs[comp.id].lastSubmitted : 0);
                ret.statements.push(cv);
            }
            else {
                cv.value = (acs[comp.id] ? acs[comp.id].value : 0);
                ret.contact.push(cv);
            }
              },basicInfo.components);
        return ret;
      });

      insertDomB(appCompsB.transform_b(function(comps) {
      return DIV(
        H4('personal'),
        UL({className:'material-list'},
          map(function(stmt) {
            return stmt.submitted ?
              LI({className:'submitted'},A({href:'Applicant/'+comps.id+'/getStatement.pdf?cookie=none&comp='+stmt.id},stmt.name)) :
              LI({className:'unsubmitted'},stmt.name);
            },comps.statements),
          LI({style:{textAlign:'center'}},A({href:'Applicant/'+comps.id+'/getCombined.pdf?cookie='},IMG({src:'images/buddha.png',alt:'Get Combined PDF',border:0})))
          ));
      }),'personal','beginning');
    
      insertDomB(switch_b(applicantB.transform_b(function(ai) {
      return DIVB(
        H4('letters'),
        ULB({className:'material-list'},
          map(function(lttr) {
            if(lttr.submitted)
              return LI({className:'submitted'},A({href:'letter-'+lttr.id+'.pdf?cookie=none&id='+lttr.id},lttr.name), " (" + lttr.email + ")");
            else {
              if(curAuth.role == 'admin') {							
                upl = new ToggleWidget('(upload)','(close upload box)');
                uplBoxB = upl.behaviors.toggled.transform_b(function(tog) {
                    return tog ? DIV({className:'stmtsub'},'Upload Letter: ',
                  FORM({enctype:'multipart/form-data',
                      encoding:'multipart/form-data',
                      action:'submitLetter',
                      method:'post',target:'upletter'},
                      INPUT({type:'hidden',name:'id',value:lttr.id}),
                      INPUT({type:'hidden',name:'cookie'}),
                      INPUT({type:'file',name:'letter'}),
                      INPUT({type:'submit',value:'Upload'}))) : SPAN();});
                return LIB({className:'unsubmitted'},lttr.name, 
                           " (" + lttr.email + ") ", upl.dom,
                           uplBoxB,' ', makeUnsubmittedRequest(lttr, launchInfo.requestReference));
              }
              return LI({className:'unsubmitted'}, lttr.name);
            }
          },ai.refletters)));
      })),'letters','beginning');
    
    var contRowsB = appCompsB.transform_b(function(comps) {
      return map(function(cinfo) {
          return TR(TH(cinfo.name+':'),TD((cinfo.type == 'contactweb' && cinfo.value) ? A({href:showWebsite(cinfo.value), "target": "_blank" },cinfo.value) : cinfo.value));
          },comps.contact);});
    var emailCellB = applicantB.transform_b(function(ai) {
            return TD(ai.email,A({href:'mailto:'+ai.email},' ',IMG({className:'icon',src:'images/envelope.png',alt:'Send Mail'})));
              });

    insertDomB(TABLEB({className:'key-value'},TBODYB(
            TRB(TH('Email: '),emailCellB),
            contRowsB)),'contact','beginning');

    var saveBtn = new ButtonWidget('Save Draft');
    var subBtn = new ButtonWidget('Submit Review');
    var revBtn = new ButtonWidget('Revert to Submitted');

    var myRevB = merge_e(
      myInitRevB.changes(),
      belayGetWSO_e(revBtn.events.click
          .filter_e(function(_) {return confirm('Are you sure you want to replace your draft with your published review? All changes will be lost!');})
          .constant_e(genRequest(
        {request:'post', fields:{}})), launchInfo.revertReview)).startsWith(myInitRevB.valueNow());

    var cbw = new InputWidgetB(
      CombinedInputWidget,
      myRevB.transform_b(function(myrev) {
        if(!myrev) myrev = {scoreValues:[],comments:'',advocate:'none'}
        var scorewidg = new CombinedInputWidget(
            map(function(sc) {
          return new SelectWidget(undefined,
            [OPTION({value:-1},'No Score')].concat(map(function(sv) {
            return OPTION({value:sv.id,selected:inList(sv.id,myrev.scoreValues)},''+sv.number+
                (sv.explanation != '' ? ' - '+sv.explanation : ''));
            },sc.values))).toTableRow(sc.name);},basicInfo.scores),function() {return TABLE({className:'key-value'},TBODY(slice(arguments,0)));});
        return [new TextAreaWidget(myrev.comments,30,60),
          scorewidg,
          new RadioListWidget([
            {k:'comment',v:'This is a comment. (all scores are ignored)'},
            {k:'advocate',v:SPAN('I will advocate ',STRONG('for'),' this candidate.')},
            {k:'detract',v:SPAN('I will advocate ',STRONG('against'),' this candidate.')},
            {k:'none',v:'Neither, but save my scores and review.'}],
              myrev.advocate)
          ];}),
      constant_b(
          function(ta,sw,ad) {
          return DIV({className:'review-form'},STRONG({className:'enterrev'},'Enter A Review or Comment'),
        sw,ad,BR(),saveBtn.dom,subBtn.dom,revBtn.dom,ta);})
          );
    var cChangeE = cbw.behaviors.value.changes().calm_e(10000);
    cbw = cbw.belayDraftSaving(
      merge_e(merge_e(cChangeE,saveBtn.events.click).constant_e('save'),subBtn.events.click.constant_e('submit')),
      function(ss,info) {
        demoEventsE.sendEvent({action:'subreview'});
        return genRequest({url:'Applicant/'+$URL('id')+'/Review/submit',
          fields: {scores:filter(function(k) {return k != -1;},info[1]), comments:info[0], advdet:info[2],
            draft:(ss == 'save' ? true : false)}});
      }, launchInfo.submitReview);

    insertDomB(cbw.dom,'revform');

    var appRevsB = merge_e(applicantB.changes(),cbw.events.serverResponse).startsWith(applicantB.valueNow()).transform_b(function(app) {console.log('appRevsB fired, app = ', app); return app.reviews;});

    insertDomB(appRevsB.transform_b(function(revs) {
      function getScoreList(rev) {
          var slist = map(function(sid) {
        return basicInfo.svcs[sid].name + ': '+basicInfo.svnum[sid];
        },rev.svals);
          slist.sort();
          return ' '+slist.join(', ');
      }
      return UL({className:'review-list'},
          map(function(rev) {
          var advstr = (rev.advocate == 'detract' ?
                SPAN({style:{color:'#aa0000'}},' (detract)') : (rev.advocate == 'advocate' ? 
            SPAN({style:{color:'#00aa00'}},' (advocate)') : ''));
          return LI(STRONG(rev.reviewerName,(rev.advocate == 'comment' ? ' (Comment)' : getScoreList(rev)),advstr),
                paraString(rev.comments,'pre',0));
        },revs));}),'otherrevs');

    insertDomB(applicantB.transform_b(function(app) {
      if(app.highlights.length > 0) {
        var applist = fold(function(v, acc) {return (acc == '' ? v.highlighteeName : acc+', '+v.highlighteeName);},'',app.highlights);
        var remSelf = fold(function(v, acc) {return (v.highlighteeName == curAuth.username ? true : acc);},false,app.highlights);
        if(remSelf) {
          var rsLink = A({href:'javascript:undefined',className:'remself'},'(remove me)');
          belayGetWSO_e(extractEvent_e(rsLink,'click').constant_e(genRequest(
            {request:'post', fields:{}})), launchInfo.unhighlightApplicant).transform_e(function(unhl) {
               appReloadsE.sendEvent(unhl);
            });
        }
        else
          var rsLink = '';
        return P('This applicant has been brought to the attention of: ',applist,' ',rsLink);
      }
      else return SPAN();
    }),'highlight-list');

    insertDomB(
      switch_b(lift_b(function(app,revs) {
        var hls = toObj(app.highlights,function(a) {return a.highlighteeName;});
        var hladd = new SelectWidget(null,
          map(function(revr) {return OPTION({value:revr.id,disabled:hls[revr.uname]?true:false},revr.uname);},
            revs.sort(function(x,y) { return stringCmp(x.uname,y.uname); }))
        ).withButton(
            new ButtonWidget('OK'),
            function(sel,btn) {return P('Bring this applicant to the attention of ',sel,btn);}
        ).belayServerSaving(function(selectee) {
          return genRequest({fields:{highlightee:selectee}});
        }, false, launchInfo.highlightApplicant);
        hladd.events.serverResponse.transform_e(function(sr) {appReloadsE.sendEvent(sr);});
        return (hladd.dom instanceof Behaviour ? hladd.dom : constant_b(hladd.dom));
      },applicantB,revsB)),'highlight-add');

    insertDomB(
      switch_b(applicantB.transform_b(function(app) {
        if(curAuth.role == 'admin') {
          var rejectBox = new CheckboxWidget(app.rejected).belayServerSaving(function(rej) {
            return genRequest({fields:{reject:(rej?'yes':'no')}});
          }, false, launchInfo.rejectApplicant);
          return PB('Reject Applicant? ',rejectBox.dom);
        }
        else {
          return app.rejected ? PB(STRONG('This applicant has been rejected.')) : SPANB();
        }
      })),'reject');
    insertDomB(
      switch_b(applicantB.transform_b(function(app) {
        var isHidden = fold(function(v, acc) {return acc || v == curAuth.username;},false,app.hiddenunames);
        var hideBox = new CheckboxWidget(isHidden).belayServerSaving(function(hide) {
          return genRequest({fields:{hide:(hide?'yes':'no')}});
        }, false, launchInfo.hideApplicant);
        return PB('Hide Applicant? ',hideBox.dom,' (this will stop you from seeing this applicant ever again, unless you specifically check "show hidden applicants" when filtering the applicant list.)');
      })),'hide');
    insertDomE(iframeLoad_e('upletter').transform_e(resultTrans('You have successfully uploaded the reference letter.')),'ls-result');

    if(curAuth.role == 'admin')
        insertDomB(
      applicantB.transform_b(function(app) {
          return P(STRONG('username: '),SPAN(app.uname));
      }),'uname');
    },basicInfoE,curAuthE);
      onLoadTimeE.sendEvent('Loaded!');
  });
});
