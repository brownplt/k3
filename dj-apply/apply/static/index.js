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

  function createAccount(email) {
    console.log('Becoming instance');
    belayBrowser.becomeInstance.post({
      domain: COMMON.urlPrefix,
      url: '/static/application.html',
      private_data: 'hello world!',
      public_data: 'Application for ' + email
    });
  }

  $('#create-relationship').click(function() {
    var email = $("#relationship-email").val();
    // TODO(joe): validate email
    createAccount(email);  
  });

  onBelayReady(function() {
    console.log('Belay is ready: ', belayBrowser);
//    theFrame.hide();
    var account = $('.make-account');
    account.show();
    // expect capServer, storage, launchInfo, belayBrowser
    // use belayBrowser.become(New)Instance
  });

});

