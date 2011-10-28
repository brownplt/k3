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
      width: '40em',
      height: '20em',
      padding: '3em'
    });
    theFrame = frame;
    return frame;
  }
  function addFrame(frame) {
    var right = $('.right-part');
    right.append(frame);
  }

  window.belay.belayInit(makeBelayFrame, addFrame);

  function addApplicant(email, addCap) {
    addCap.post({email : email}, function(response) {
      // TODO(matt): hide box & button, show 'check your email' message
      console.log('add with position response: ', response);
    });
  }

  onBelayReady(function() {
    console.log('Belay is ready: ', belayBrowser);
//    theFrame.hide();
    var account = $('.make-account');
    account.show();

    var createApplicantCap = capServer.restore(createApplicantCapURL);
    createApplicantCap.get(function(response) {
      console.log('createApplicantCap get response: ', response);
      var positions = Object.keys(response);
      if (positions.length === 0) {
        console.log('Error: no applicant positions!');
        return;
      }
      // TODO: if multiple positions, pick from dropdown
      if (positions.length !== 1) {
        console.log('Warning: multiple position support NYI');
      }

      console.log('position: ', positions[0]);
      var addWithPosCap = response[positions[0]];

      $('#create-relationship').click(function() {
        var email = $("#relationship-email").val();
        // TODO(joe): validate email
        addApplicant(email, addWithPosCap);  
      });
    });
    // expect capServer, storage, launchInfo, belayBrowser
    // use belayBrowser.become(New)Instance
  });

});

