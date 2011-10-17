if(!window.belay) window.belay = {};
window.belay.belayInit = (function() {
  var callbacks = [];
  console.log('initializing...');

  function frameInfo(frameMaker, frameAdder) {
    function connect() {
      var frameWindow = frame[0].contentWindow;

      frame.unbind('load', connect);

      window.belay.port = makePostMessagePort(frameWindow, "belay");

      // TODO(joe): check args order of postMessage cross browser, use
      // $.pm() here if necessary
      frameWindow.postMessage({
        clientLocation: JSON.parse(JSON.stringify(window.location))
      }, [], '*');

      window.belay.portReady();
    }

    var frame = frameMaker();
    frame.load(connect);
    frameAdder(frame);
  }

  return Object.freeze(frameInfo);
})();

