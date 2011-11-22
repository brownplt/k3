$(function() {

  COMMON.setContact(contactURL);

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

  var capServer = new CapServer();
  var hash = window.location.hash;
  window.location.hash = "#";
  var createCapSer = hash.substr(1);

  var createCap = capServer.restore(createCapSer);
  createCap.get(function(email) {
    window.belay.belayInit(makeBelayFrame, addFrame, {useName: false,
                                                      createCap: createCapSer,
                                                      email: email});
  });

  onBelayReady(function(readyBundle) {
    console.log('Belay is ready');
    if(readyBundle.belayBrowser.hasInstances) { return; }
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

