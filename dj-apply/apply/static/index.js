$(function() {
  function makeBelayFrame() {
    var frame = $('<iframe></iframe>');
    frame.attr({
      'src': 'http://localhost:8000/static/belay-frame.html',
      'name': 'belay'
    });
    frame.css({
      border: 'none',
      width: '40em',
      height: '20em',
      padding: '3em'
    });
    return frame;
  }
  function addFrame(frame) {
    var right = $('.right-part');
    console.log('Adding frame');
    right.append(frame);
  }

  window.belay.belayInit(makeBelayFrame, addFrame);

  onBelayReady(function() {
    console.log('Belay is ready: ', belayBrowser);
    belayBrowser.becomeInstance.post({
      domain: 'http://localhost:8001',
      url: '/static/applicant.html',
      private_data: 'hello world!'
    });
    // expect capServer, storage, launchInfo, belayBrowser
    // use belayBrowser.become(New)Instance
  });

});

