if(!window.belay) window.belay = {};
window.belay.belayInit = (function() {
  var callbacks = [];
  console.log('initializing...');

  function frameInfo(frameMaker, frameAdder, email, showCreate) {
    function connect() {
      var frameWindow = frame[0].contentWindow;

      frame.unbind('load', connect);

      window.belay.port = makePostMessagePort(frameWindow, "belay");

      // TODO(joe): check args order of postMessage cross browser, use
      // $.pm() here if necessary
      var loc = window.location;
      var hash = window.location.hash;
      if (loc.hash === "" || loc.hash === "#") {
        hash = window.name;
      }
      var location = {
        hash: hash,
        hostname: loc.hostname,
        port: loc.port,
        pathname: loc.pathname,
        href: loc.href
      };
      $.pm({
        target: frameWindow,
        type: 'init',
        data: {
          clientLocation: location,
          email: email,
          showCreate: showCreate
        }
      });

      // Clear the hash ASAP
      window.location.hash = "";

      window.name = hash;
      window.belay.portReady();
    }

    var frame = frameMaker();
    frame.load(connect);
    frameAdder(frame);
  }

  return Object.freeze(frameInfo);
})();

