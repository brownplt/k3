$(function() {
  var theFrame;
  function makeBelayFrame() {
    var frame = $('<iframe></iframe>');
    frame.attr({
      'src': COMMON.belayFrame,
      'name': 'belay'
    });
    frame.css({
      border: 'none',
      width: '80%',
      height: '100%',
      'min-height': '24em',
      'margin-top': '1em',
      'margin-left': '3em'
    });
    theFrame = frame;
    return frame;
  }
  function addFrame(frame) {
    var right = $('.left-part');
    right.append(frame);
  }

  window.belay.belayInit(makeBelayFrame, addFrame);

  var capServer = new CapServer();
  $('#create-relationship').click(function() {
    // TODO(joe): assuming a single position
    createApplicant = capServer.restore(createApplicantCapURL);
    createApplicant.get(function(positionCaps) {
      var thePos;
      for(var i in positionCaps) {
        if(!positionCaps.hasOwnProperty(i)) continue;
        thePos = positionCaps[i];
        break;
      }
      var email = $('#relationship-email').val();
      thePos.post({email: email}, function (response) {
            if(response.emailError) {
              var elt = $('#failure');
              elt.text(response.message);
              elt.fadeIn();
              $('#success').hide();
              return;
            }
            $('#success').fadeIn();
            $('#failure').hide();
          },
          function(err) {
          });
    });
  });

  onBelayReady(function(readyBundle) {
    console.log('Belay is ready');
    $('#start-new').fadeIn();
    $('#newapp').click(function() {
      createApplicant = capServer.restore(createApplicantCapURL);
      createApplicant.get(function(positionCaps) {
        var thePos;
        for(var i in positionCaps) {
          if(!positionCaps.hasOwnProperty(i)) continue;
          thePos = positionCaps[i];
          break;
        }
        console.log('thePos: ', thePos);
        console.log('thePos: ', readyBundle);
        thePos.post({email: readyBundle.belayBrowser.loginEmail}, function(response) {
          response.create_cap.get(function(emailAndCreate) {
            console.log('EAndC: ', emailAndCreate);
            emailAndCreate.create.post({}, function(launchInfo) {
              console.log('launch: ', emailAndCreate);
              readyBundle.belayBrowser.becomeInstance.post(launchInfo);
            });
          });
        });
      });
    })
  });
  
});

