var plug_e = function(c,in_e) {
	if(c._canPlug) {
		in_e.transform_e(function(_) {c.sendEvent(_);});
		c._canAdd = false;
		c._canPlug = false;
	}
	else {
		throw 'plug_e: cannot plug into this consumer';
	}
	return c;
}
var add_e = function(c,in_e) {
	if(c._canAdd) {
		in_e.transform_e(function(_) {c.sendEvent(_);});
		c._canPlug = false;
	}
	else {
		throw 'add_e: cannot add to this consumer';
	}
	return c;
}
var consumer_e = function() {
	var co = receiver_e();
	co._canAdd = true;
	co._canPlug = true;
	co.plug_e = function(in_e) {return plug_e(co,in_e);}
	co.add_e = function(in_e) {return add_e(co,in_e);}
	return co;
}
var rec_e = function(trans) {
	var co = consumer_e();
	co.plug_e(trans(co));
	return co;
}
