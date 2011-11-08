var COMMON = (function(){
  var urlPrefix = window.location.protocol + '//' + window.location.host;
  var sessionRegExp = /.*session=([\-0-9a-zA-Z]+).*/;

  var validateLoginInfo = function(username, password) {
    var allLegal = function(s) {
      var i = 0, len = s.length;
      for (; i < len; ++i) {
        if ((s.charCodeAt(i) < 33) || (s.charCodeAt(i) > 126)) {
          return false;
        }
      }
      return true;
    };

    return username.length > 0 && username.length <= 20 && 
      password.length >= 8 && allLegal(username) && allLegal(password);
  };

  var belayFrame = '{{ belay_location }}/static/belay-frame.html';

  return { 
    urlPrefix : urlPrefix, 
    sessionRegExp : sessionRegExp,
    validateLoginInfo : validateLoginInfo,
    belayFrame: belayFrame
  };
}());
