function positionListB(basicInfo, addCap) {
  var positions = basicInfo.positions;
  return new ModListWidget(positions,
      TR(TH('Name'), TH('Abbr'), TH('Auto Email')), // header
      // Display a single position
      function(position) {
        var result = new ButtonInputWidget([ ],
          { del: new LinkWidget('Delete') },
          function() { return position; },
          function(_,bob) {
            return TR(TD(position.name), TD(position.shortform),
              TD(position.autoemail ? "Yes" : "No"), TD(bob.del));
          });
        result.events.del.lift_e(function() { alert('Not yet implemented'); });
        return result;
      },
      // Displays the entry box for a new position
      function() {
        return new ButtonInputWidget(
          [ new TextInputWidget('',20), new TextInputWidget('',5,5),
          new CheckboxWidget(false) ],
          { value: new ButtonWidget('Add') },
          function(name,shortform,autoEmail) { 
            return { cookie: authCookie, 
              name: name,
        shortform: shortform,
        autoemail: autoEmail
            };
          },
          function(is,bs) { 
            return TR(TD(is[0]),TD(is[1]),TD(is[2]),TD(bs.value));
          })
        .belayServerSaving(function(fields){
          console.log('position list add: fields = ', fields);
          return {fields:fields};
        }, true, addCap);
      }).dom;
};

function genAreasList(bi, addCap) {
  return new ModListWidget(bi.areas,
      TR(TH('Name'),TH('Abbr')),
      function(obj) {
        var ret = new ButtonInputWidget([],
          {del:new LinkWidget('Delete')},
          function() {return obj;},
          function(_,bob) {return TR(TD(obj.name),TD(obj.abbr),TD(bob.del));});
        ret.events.del = belayGetWSO_e(ret.events.del.transform_e(function(d) {
          return {request:'delete'};
        }), obj.del);
        return ret;
      },
      function() {
        return new ButtonInputWidget(
          [new TextInputWidget('',20),
          new TextInputWidget('',5,5)],
          {value:new ButtonWidget('Add')},
          function(n,a) {return {cookie:authCookie,name:n,abbr:a};},
          function(is,bs) {return TR(TD(is[0]),TD(is[1]),TD(bs.value));})
          .belayServerSaving(function(a) {return {fields:a};},true, addCap);
      }).dom;
}
function genStmtList(bi) {
  return new ModListWidget(filter(function(c) {return c.type == 'statement';},bi.components),
      TR(TH('Name'),TH('Short Name')),
      function(obj) {
        return new ButtonInputWidget([],
          {del:new LinkWidget('Delete')},
          function() {return obj;},
          function(_,bob) {return TR(TD(obj.name),TD(obj.shortname),TD(bob.del));});
      },
      function() {
        return new ButtonInputWidget(
          [new TextInputWidget('',20),
          new TextInputWidget('',5,5)],
          {value:new ButtonWidget('Add')},
          function(a,b) {return {name:a,shortname:b};},
          function(is,bs) {return TR(TD(is[0]),TD(is[1]),TD(bs.value));});
      }).dom;
}
function genContList(bi) {
  return new ModListWidget(filter(function(c) {return c.type == 'statement';},bi.components),
      TR(TH('Name'),TH('Short Name')),
      function(obj) {
        return new ButtonInputWidget([],
          {del:new  LinkWidget('Delete')},
          function() {return obj;},
          function(_,bob) {
            return TR(TD(obj.name),TD(obj.shortname),TD(
                obj.type == 'contactshort' ? 'Short Field' : (obj.type == 'contactlong' ? 'Long Field' : 'Website')
                ),TD(bob.del));});
      },
      function() {
        return new ButtonInputWidget(
          [new TextInputWidget('',20),
          new TextInputWidget('',5,5),
          new SelectWidget('contactshort',
            [OPTION({value:'contactshort'},'Short Field'),
            OPTION({value:'contactlong'},'Long Field'),
            OPTION({value:'contactweb'},'Website')])],
          {value:new ButtonWidget('Add')},
          function(n,v,t) {return {name:n,value:v,type:t};},
          function(is,bs) {return TR(TD(is[0]),TD(is[1]),TD(is[2]),TD(bs.value));});
      }).dom;
}
function genRCList(bi, addCap) {
  var editValueE = receiver_e();
  var rclB = new ModListWidget(bi.scores,
      TR(TH('Name'),TH('Abbr'),TH('Values')),
      function(obj) {
        var ln = A({href:'javascript:undefined'},''+obj.values[0]['number']+' - '+obj.values[obj.values.length-1]['number']);
        ln.onclick = function() {editValueE.sendEvent(obj);};
        var ret = new ButtonInputWidget(
          [new TextInputWidget(obj.name,20),
          new TextInputWidget(obj.shortform,4)],
          {value:	new ButtonWidget('Save Changes'),
            del:new LinkWidget('Delete')},
            function(n,s,agg) {return {name:n,shortform:s,cookie:authCookie,id:obj.id };},
            function(is,bs) {return TR(TD(is[0]),TD(is[1]),TD(ln),TD(bs.value),TD(bs.del));})
          .belayServerSaving(function(val) {
            return {fields:val}; }, true, obj.change);
        ret.events.del = belayGetWSO_e(ret.events.del.transform_e(function(){return {request:'delete'};}), obj.del);
        return ret;
      },
      function() {
        return new ButtonInputWidget(
          [new TextInputWidget('',20),
          new TextInputWidget('',4),
          new TextInputWidget('1',2,2),
          new TextInputWidget('10',2,2)],
          {value:new ButtonWidget('Add')},
          function(n,s,min,max,agg) {return {name:n,shortform:s,minval:min,maxval:max,aggregated:agg?'yes':'no',cookie:authCookie};},
          function(is,bs) {
            is[2].style.width = '1em';
            is[3].style.width = '1em';
            return TR(TD(is[0]),TD(is[1]),TD(is[2],' - ',is[3]),TD(is[4]),TD(bs.value));})
          .belayServerSaving(function(val) { return {fields:val}; }, true, addCap);
      }).dom;
  insertDomE(editValueE.transform_e(function(ev) {
    return DIV(
      H4('Values: ',ev.name),
      TABLE({className:'key-value'},
        TBODY(
          map(function(sv) {
            return new TextInputWidget(sv.explanation,20).toTableRow(''+sv['number']).belayServerSaving(function(sve) {
              sv.explanation = sve;
              return {fields:{explanation:sve, number:sv.number}};}, false, sv.change).dom;
          },ev.values))));
  }),'rcvals');
  return rclB;
}

function RevEntry(rev,cols) {
  var me = this;
  this.obj = rev;
  this.doms = null;
  this.getObj = function() {return this.obj;};
  this.getDoms = function() {
    if(this.doms == null)
      this.doms = [TR(map(function(col) {var c = col.makeTD(me.getObj(),authCookie); c.className=col.className; return c;},cols))];
    return this.doms;
  }
}

function stringCmp(a,b) {return (a > b) ? 1 : (b > a) ? -1 : 0;}
function reviewerTable(allrevs) {
  var cols = [
    // NOTE(joe): The full name can become a log-in-as link (or some other ui)
    makeColumn('name','Full Name',function(a, b) {return stringCmp(a.name,b.name);},function(r, cookie) {return TD(r.name);}),
    makeColumn('email','Email',function(a, b) {return stringCmp(a.email,b.email);},function(r, cookie) {return TD(r.email);}),
    makeColumn('admin','Admin?',
        function(a, b) {return (a.role == 'admin' ? 1 : 0) + (b.role == 'admin' ? -1 : 0);},
        function(r,cookie) {return TD(r.role == 'admin' ? 'Yes' : 'No');}),
    makeColumn('numrevs','Revs',
        function(a, b) {return a.numrevs - b.numrevs;},
        function(r,cookie) {return TD(''+(r.numrevs || 0));})
      ];
  var reventsB = constant_b(map(function(r) {return new RevEntry(r,cols);},allrevs));
  return new TableWidget(reventsB,'reviewer',cols).dom;
}

$(function() {
  var flapjax = flapjaxInit();
  var exceptsE = captureServerExcepts(); 
  exceptsE.filter_e(function(_) {return _.value == 'denied';}).transform_e(function(_) {window.location='login.html?expired=true'});

  var onLoadTimeE = receiver_e();

  var theFrame;

  function makeBelayFrame() {
    var frame = $('<iframe></iframe>');
    frame.attr({
      'src': COMMON.belayFrame,
      'name': 'belay'
    });
    frame.css({
      display: 'none',
      width: '30em',
      height: '30em'
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

    console.log('Belay is ready: ', launchInfo);

    launchInfo.get(function(r) {
      r.getBasic.get(function(basicInfo) {
        var basicInfoE = onLoadTimeE.constant_e(basicInfo);
        r.getReviewers.get(function(reviewers) {
          var allrevsE = onLoadTimeE.constant_e(reviewers);
          r.UnverifiedUserGetPending.get(function(pending) {
            var pendingE = onLoadTimeE.constant_e(pending);
            doRestAdmin(basicInfoE, allrevsE, pendingE, r);
          });
        });
      });
    });
  });


  authCookie = $URL('cookie');

  function doRestAdmin(basicInfoE, allrevsE, pendingE, launchInfo) {
    lift_e(function(basicInfo,allRevs) {
      console.log('ALLREVS: ', allRevs);

      insertDomB(reviewerTable(allRevs),'revlist');

      insertDomB(genAreasList(basicInfo, launchInfo.AreaAdd),'arealist');
      insertDomB(genStmtList(basicInfo),'stmtlist');
      insertDomB(genContList(basicInfo),'contlist');
      insertDomB(genRCList(basicInfo, launchInfo.ScoreCategoryAdd),'rclist');
      insertDomB(positionListB(basicInfo, launchInfo.ApplicantPositionAdd),'applicantPositions');


      insertDom(
        new CombinedInputWidget(
          [new TextInputWidget(basicInfo.info.contactName,20).toTableRow('Contact Name'),
          new TextInputWidget(basicInfo.info.contactEmail,20).toTableRow('Contact Email'),
          new TextInputWidget(basicInfo.info.techEmail,20).toTableRow('Maintainer Email')],
          function(cname,cemail,temail) {return TABLE({className:'key-value'},TBODY(cname,cemail,temail));}).belayServerSaving(
          function(cinfo) {
            return {fields:{contactName:cinfo[0], contactEmail:cinfo[1], techEmail:cinfo[2]}}
          }, false, launchInfo.changeContacts).dom, 'cinfo');
    },basicInfoE,allrevsE);

    insertDomE(
        belayGetWSO_e(snapshot_e(extractEvent_e('lwbut','click'),$B('lwemail')).transform_e(function(email) {
          return {fields:{email:email}};
        }), launchInfo.findRefs).transform_e(function(results) {
          if (results.length > 0) return UL(
            map(function(apl) {
              return LI(
                SPAN(apl.appname + ": "),
                A({href:apl.submitlink, target: '_blank'},'Submit Reference'),
                A({href:'mailto:'+apl.appemail},' ',IMG({border:0,src:'/static/images/envelope.png',alt:'Email Candidate'})));
            },results)); else return P('No requests have gone to that email address.');}),'lwresults');

    insertDomB(switch_b(pendingE.transform_e(function(pending) {
      return new ModListWidget(pending,
        TR(TH('Name'),TH('Email'),TH('Admin?')),
        function(obj) {
          var ret = new ButtonInputWidget([],
            {del:new LinkWidget('Delete')},
            function(_) {return obj;},
            function(_,bob) {
              return TR(TD(obj.name),TD(obj.email),TD(obj.role == 'admin' ? 'Yes' : 'No'),TD(bob.del));
            });
          ret.events.del = belayGetWSO_e(ret.events.del.transform_e(function(d) {
            return {request:'delete', fields:{id:d.id}};}),
            obj.del);
          return ret;
        },
        function() {
          return new ButtonInputWidget(
            [new TextInputWidget('',20),
            new TextInputWidget('',20),
            new CheckboxWidget(false)],
            {value:new ButtonWidget('Add')},
            function(n,e,a) {
              return {cookie:authCookie,name:n,email:e,role:a?'admin':'reviewer'};
            },
            function(is,bs) {
              return TR(TD(is[0]),TD(is[1]),TD(is[2]),TD(bs.value));
            })
          .belayServerSaving(
              function(v) {
                return {fields : v};
              },
              true,
              launchInfo.UnverifiedUserAddRev
              );
        }).dom;}).startsWith(SPANB())),'pending');

    onLoadTimeE.sendEvent('Loaded!');
  }
});
