var COMMON = (function(){
  var urlPrefix = '{{ site_name }}';
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

  var belayFrame = '{{ belay_location }}/belay-frame/';

  if(typeof String.prototype.trim === 'undefined') {
    String.prototype.trim = function(s) { return s; }
  }

  return { 
    urlPrefix : urlPrefix, 
    sessionRegExp : sessionRegExp,
    validateLoginInfo : validateLoginInfo,
    belayFrame: belayFrame
  };
}());
