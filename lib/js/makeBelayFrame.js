if(!window.belay) window.belay = {};
window.belay.belayInit = (function() {
  var callbacks = [];
  console.log('initializing...');

  function frameInfo(frameMaker, frameAdder, extras) {
    var defaults = {
      email: false,
      useName: true,
      showCreate: true,
      createCap: null
    };
    function getDefault(name) {
      if (typeof extras !== 'object') return defaults[name];
      return extras.hasOwnProperty(name) ? extras[name] : defaults[name];
    }
    var email = getDefault('email');
    var useName = getDefault('useName');
    var showCreate = getDefault('showCreate');
    var createCap = getDefault('createCap');
    function connect() {
      var frameWindow = frame[0].contentWindow;

      frame.unbind('load', connect);

      window.belay.port = makePostMessagePort(frameWindow, "belay");

      // TODO(joe): check args order of postMessage cross browser, use
      // $.pm() here if necessary
      var loc = window.location;
      var hash = window.location.hash;
      if (useName && (loc.hash === "" || loc.hash === "#")) {
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
          showCreate: showCreate,
          createCap: createCap
        }
      });

      // Clear the hash ASAP
      window.location.hash = "#";

      if(useName) { window.name = hash; }
      window.belay.portReady();
    }

    var frame = frameMaker();
    frame.load(connect);
    frameAdder(frame);
  }

  return Object.freeze(frameInfo);
})();

