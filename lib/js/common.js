var COMMON = (function(){
  var urlPrefix = window.location.protocol + '//' + window.location.host;
  var sessionRegExp = /.*session=([\-0-9a-zA-Z]+).*/;

  return { urlPrefix : urlPrefix, sessionRegExp : sessionRegExp }
}());
