function getWebServiceObject_e(objE) {
	function genRequest(f) {
		var req = '';
		function addToReq(key,val) {
			if(req != '')
				req += '&';
			req += key + '=' + encodeURIComponent(val);
		}
		for (var key in f) {
			if ((f[key] != null &&	f[key] != undefined &&
				typeof f[key] != 'function') &&
					(!f.prototype || !f.prototype.key)) {
				if (!(typeof f[key] == 'string') && f[key].length) {
					for(var i=0;i<f[key].length;i++)
						addToReq(key,f[key][i]);
				}
				else {
					addToReq(key,f[key]);
				}
			}
		};
		return req;
	}
	var ws_e = receiver_e();
	objE.transform_e(
		function (obj) {
			var body = '';
			var method = 'get';
			var url = obj.url;
			var reqType = obj.request ? obj.request :
				obj.fields ? 'post' : 'get';
			if (obj.request == 'get') {
				url += "?" + genRequest(obj.fields);
				body = '';
				method = 'GET';
			} else if (obj.request == 'post') {
				body = genRequest(obj.fields);
				method = 'POST';
			} else if (obj.request == 'rawPost') {
				body = obj.body;
				method = 'POST';
			}
			var xhr;
			function sendJSON() {
			//Sometimes trying to parse the responseText caused an error --- perhaps a race-condition in loading
			//the various javascript files? This should (hopefully) fix that problem.
				ws_e.sendEvent(xhr.responseText.parseJSON());
			}
			if (window.XMLHttpRequest && !(window.ActiveXObject)) {
			 	xhr = new XMLHttpRequest();
				if(obj.serviceType == 'jsonLiteral')
					xhr.onload = sendJSON;
				else if(obj.serviceType == 'xml')
					xhr.onload = function() {ws_e.sendEvent(xhr.responseXML);};
			}
			else if(window.ActiveXObject) {
				try {
					xhr = new ActiveXObject("Msxml2.XMLHTTP");
				} catch(e) {
					xhr = new ActiveXObject("Microsoft.XMLHTTP");
				}
				if(obj.serviceType == 'jsonLiteral')
					xhr.onreadystatechange = function() {if(xhr.readyState==4) sendJSON();};
				else if(obj.serviceType == 'xml')
					xhr.onreadystatechange = function() {if(xhr.readyState==4) ws_e.sendEvent(xhr.responseXML);};
			}
			xhr.open(method,url,obj.asynchronous);
			if(obj.request == 'post')
				xhr.setRequestHeader('content-type','application/x-www-form-urlencoded');
			xhr.send(body);
	});
	return ws_e;
}
