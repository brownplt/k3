function setCookie(name,days,value) {
    var dname = (''+window.location).split('/');
    dname = dname[dname.length-2];
    var cookiename = dname+'-'+name;
    var when = new Date();
    when.setTime(when.getTime()+(days*86400000));
    document.cookie = cookiename + '=' + escape(value) + '; expires='
    + when.toGMTString() +'; path=/';
}

function getCookie(name) {
    var dname = (''+window.location).split('/');
    dname = dname[dname.length-2];
    var cookiename = dname+'-'+name+'=';
    var result = fold(function(cookiepart,r) {
	    while (cookiepart.charAt(0)==' ') 
        cookiepart = cookiepart.substring(1,cookiepart.length);
	    if(cookiepart.indexOf(cookiename) == 0) 
        return cookiepart.substring(cookiename.length,cookiepart.length); 
      else
        return r;
    },undefined,document.cookie.split(';'));
  return result !== undefined ? unescape(result) : result;
}
