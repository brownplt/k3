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
      height: '50%',
      'margin-top': '5em',
      'margin-left': '3em',
    });
    theFrame = frame;
    return frame;
  }
  function addFrame(frame) {
    var right = $('.right-part');
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
            $('#success').show();
          },
          function(err) {
            var elt = $('#failure');
            if(err.message) elt.text(err.message);
            else {
              elt.text("Oops!  There was an error on our end.  Send " +
                       "an email to the address below to let us know, we're " + 
                       "already on it.");
            }
            elt.show();
          });
    });
  });
  
});

