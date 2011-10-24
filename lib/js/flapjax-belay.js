function belayGetWSO_e(objE, cap) {
  var ws_e = receiver_e();

  function toReceiver(val) {
    ws_e.sendEvent(val);
  }

  function get(obj) {
    cap.get(toReceiver);
  }

  function post(obj) {
    cap.post(obj.fields, toReceiver);
  }

  function remove(obj) {
    cap.remove(toReceiver);
  }

  objE.transform_e(function(obj) {
    var reqMethod;
    if (typeof obj.request !== 'undefined') {
      reqMethod = obj.request === 'post' ? post : obj.request === 'delete' ? remove : get;
    } else {
      if (typeof obj.fields !== undefined) {
        reqMethod = post;
      } else {
        reqMethod = get;
      }
    }
    reqMethod(obj);
  });

  return ws_e;
}

InputWidget.prototype.belayServerSaving = function(toReqFn, replaceValue, cap) {
    var objE = this.behaviors.value.changes().calm_e(500).transform_e(toReqFn)
    this.events.serverResponse = belayGetWSO_e(objE, cap);
	var greyB = merge_e(
			this.events.serverResponse.constant_e(false),
			this.behaviors.value.changes().constant_e(true)
		).startsWith(false);
	if (replaceValue) this.behaviors.value = this.events.serverResponse.startsWith(this.behaviors.value.valueNow());
	return this.greyOutable(greyB);
};
