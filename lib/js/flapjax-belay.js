/*
  getE : EventStream[Capability[get: -> α]] -> EventStream[α]

  Given an event stream of capabilities, returns an event stream
  that:

  1. Invokes get() on the capability

  2. Fires when the capability invocations responds, with the result of the
     get.  Note:  Responses may not come in the same order as sends.

*/
function getE(capE) {
  var ws_e = receiver_e();
  capE.transform_e(function(cap) {
    console.log('Getting: ', cap);
    cap.get(function(result) { ws_e.sendEvent(result); });
  });
  return ws_e;
}

/* 
   postE : EventStream[{0 : Capability[post: β -> α],
                        1 : β}]
        -> EventStream[α]

   I wish JavaScript had tuples.  A two element array will have to do.
   Example:

    var cap = capServer.restore(serialized);
    var elt = ... create a fancy dom thing ...
    var doneThingsE = postE(elt.clicks_e().constant_e([cap, elt.value]));
    // doneThingsE fires on the response of the post

  Given an event stream of capabilities and arguments, returns an event stream
  that:

  1. Invokes post(args) on the capability

  2. Fires when the capability invocations responds, with the result of the
     get.  Note:  Responses may not come in the same order as sends.
*/
function postE(postPairE) {
  var ws_e = receiver_e();
  postPairE.transform_e(function(postPair) {
    postPair[0].post(postPair[1], function(result) { ws_e.sendEvent(result); });
  });
  return ws_e;
}

/*
  removeE : EventStream[Capability[remove: -> Undef]] -> EventStream[Undef]

*/
function removeE(capE) {
  var ws_e = receiver_e();
  capE.transform_e(function(cap) {
    cap.remove(function(_) { ws_e.sendEvent(undefined); });
  });
  return ws_e;
}

function belayGetWSO_e(objE, cap) {
  var ws_e = receiver_e();

  function toReceiver(val) {
    ws_e.sendEvent(val);
  }

  function get(obj) {
    cap.get(toReceiver);
  }

  function post(obj) {
    cap.post(obj.fields, toReceiver, function() {
      console.log("flapjax-belay: Failed to post: ", obj);
    });
  }

  function remove(obj) {
    cap.remove(toReceiver, function(err){
      console.log("flapjax-belay: Failed to get: ", err);
    });
  }

  objE.transform_e(function(obj) {
    var reqMethod;
    if (typeof obj.request !== 'undefined') {
      console.log("flapjax-belay: Choosing ", obj.request);
      reqMethod = obj.request === 'post' ? post : obj.request === 'delete' ? remove : get;
    } else {
      if (typeof obj.fields !== undefined) {
        console.log("flapjax-belay: Choosing Post");
        reqMethod = post;
      } else {
        console.log("flapjax-belay: Choosing get");
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
