/*
Copyright (c) 2006-2008, the Flapjax Team All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.
* Neither the name of the Brown University, the Flapjax Team, nor the names
of its contributors may be used to endorse or promote products derived
from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

//flapjaxInit: [Boolean] -> {...}
//makeTopLevel defaults to true (all function names are in returned object instead of toplevel)
function flapjaxInit(makeTopLevel) {
  
  //compress via http://alex.dojotoolkit.org/shrinksafe/
  //make sure to change final eval call to use exported library renamed name
  
  var flapjax = {     
    version: 4, 
    lib: {}, //map, filter, member etc
    base: {}, //pulses
    engine: {}, //core nodes
    combinators: {}, // combinators yielding nodes
	behaviours: {},
    dom: {}, // dom convenience methods and combinators
    ajax: {}, // ajax convenience methods and combinators
  };
  
  //namespace shortcuts
  var l = flapjax.lib;
  var e = flapjax.engine;
  var b = flapjax.base;
  var c = flapjax.combinators;
	var be = flapjax.behaviours;
  var d = flapjax.dom;
  var a = flapjax.ajax;
  
	flapjax.pub = {util:flapjax};
  
	var annotate = function(fn,names,protoArg,protoObjs,protoNames) {
		for(var i=0; i<names.length;i++) {
			flapjax.pub[names[i]] = fn;
		}
		if(protoArg != undefined) {
			var pf = function() {
				var args = slice(arguments,0);
				args.splice(protoArg,0,this);
				return fn.apply(this,args);
			}
			for(var i=0; i<protoObjs.length; i++) {
				for(var j=0; j<protoNames.length;j++) {
					protoObjs[i][protoNames[j]] = pf;
				}
			}
		}
	}
  
	annotate(function() {return flapjax;},['getFlapjaxObj']);
  
	//credit 4umi
	//slice: Array a * Integer * Integer -> Array a
	l.slice = function (arr, start, stop) {
		var i, len = arr.length, r = [];
		if( !stop ) { stop = len; }
		if( stop < 0 ) { stop = len + stop; }
		if( start < 0 ) { start = len - start; }
		if( stop < start ) { i = start; start = stop; stop = i; }
		for( i = 0; i < stop - start; i++ ) { r[i] = arr[start+i]; }
		return r;
	}
	annotate(l.slice,['slice']);

	l.isEqual = function (a,b) {
		return (a == b) ||
			( (((typeof(a) == 'number') && isNaN(a)) || a == 'NaN') &&
			  (((typeof(b) == 'number') && isNaN(b)) || b == 'NaN') );
	};

	//member: a * Array b -> Boolean
	l.member = function(elt, lst) {
		for (var i = 0; i < lst.length; i++) { 
			if (l.isEqual(lst[i], elt)) {return true;} 
		}
		return false;
	};
	annotate(l.member,['member']);
  
	l.zip = function(arrays) {
		if (arrays.length == 0) return [];
		var ret = [];
		for(var i=0; i<arrays[0].length;i++) {
			ret.push([]);
			for(var j=0; j<arrays.length;j++) 
				ret[i].push(arrays[j][i]);
		}
		return ret;
	}

	//map: (a * ... -> z) * [a] * ... -> [z]
	l.map = function (fn) {
		var arrays = l.slice(arguments, 1);
		if (arrays.length === 0) { return []; }
		else if (arrays.length === 1) {
			var ret = [];
			for(var i=0; i<arrays[0].length; i++) {ret.push(fn(arrays[0][i]));}
			return ret;
		}
		else {
			var ret = l.zip(arrays);
			var o = new Object();
			for(var i=0; i<ret.length; i++) {ret[i] = fn.apply(o,ret[i]);}
			return ret;
		}
	};
	annotate(l.map,['map','forEach']);
  
	//filter: (a -> Boolean) * Array a -> Array a
	l.filter = function (predFn, arr) {
		var res = [];
		for (var i = 0; i < arr.length; i++) { 
			if (predFn(arr[i])) { res.push(arr[i]); }
		}
		return res;
	};
	annotate(l.filter,['filter']);
  
  //fold: (a * .... * accum -> accum) * accum * [a] * ... -> accum
  //fold over list(s), left to right
  l.ofold = function(fn, init /* arrays */) {
		var lists = l.slice(arguments, 2);
		if (lists.length === 0) { return init; }
		else {
			var acc = init;
			for (var i = 0; i < lists[0].length; i++)
			{
				var args = 
        l.map( 
          function (lst) { return lst[i];}, 
          lists);
				args.push(acc);
				acc = fn.apply({}, args);
			}
			return acc;
		}
	};
	annotate(l.ofold,['ofold']);
  
  //fold: (a * .... * accum -> accum) * accum * [a] * ... -> accum
  //fold over list(s), left to right
  l.fold = function(fn, init /* arrays */) {
		var lists = l.slice(arguments, 2);
		if (lists.length === 0) { return init; }
		else if(lists.length === 1) {
			var acc = init;
			for(var i = 0; i < lists[0].length; i++) {
				acc = fn(lists[0][i],acc);
			}
			return acc;
		}
		else {
			var acc = init;
			for (var i = 0; i < lists[0].length; i++) {
				var args = l.map( function (lst) { return lst[i];}, 
		          lists);
				args.push(acc);
				acc = fn.apply({}, args);
			}
			return acc;
		}
  };
	annotate(l.fold,['fold']);
  
  //foldR: (a * .... * accum -> accum) * accum * [a] * ... -> accum
	//fold over list(s), right to left, fold more memory efficient (left to right)
	l.foldR = function (fn, init /* arrays */) {
    var lists = l.slice(arguments, 2);
		if (lists.length === 0) { return init; }
		else if(lists.length === 1) {
			var acc = init;
			for(var i=lists[0].length - 1; i > -1; i--)
				acc = fn(lists[0][i],acc);
			return acc;
		}
		else {
			var acc = init;
			for (var i = lists[0].length - 1; i > -1; i--) {
				var args = l.map( function (lst) { return lst[i];}, 
		          lists);
				args.push(acc);
				acc = fn.apply({}, args);
			}
			return acc;     
		}
	};
	annotate(l.foldR,['foldR']);
  
  //Pulse: Stamp * Path * Obj
  flapjax.base.Pulse = function (stamp, value) {
    this.stamp = stamp;
    this.value = value;
  };
  
  //Probably can optimize as we expect increasing insert runs etc
  b.PQ = function () {
    var ctx = this;
    ctx.val = [];
    this.insert = function (kv) {
			ctx.val.push(kv);
			var kvpos = ctx.val.length-1;
			while(kvpos > 0 && kv.k < ctx.val[Math.floor((kvpos-1)/2)].k) {
				var oldpos = kvpos;
				kvpos = Math.floor((kvpos-1)/2);
				ctx.val[oldpos] = ctx.val[kvpos];
				ctx.val[kvpos] = kv;
			}
    };
    this.isEmpty = function () { 
      return ctx.val.length === 0; 
    };
    this.pop = function () {
			if(ctx.val.length == 1) {
				return ctx.val.pop();
			}
			var ret = ctx.val.shift();
			ctx.val.unshift(ctx.val.pop());
			var kvpos = 0;
			var kv = ctx.val[0];
			while(1) {
				var leftChild = (kvpos*2+1 < ctx.val.length ? ctx.val[kvpos*2+1].k : kv.k+1);
				var rightChild = (kvpos*2+2 < ctx.val.length ? ctx.val[kvpos*2+2].k : kv.k+1);
				if(leftChild > kv.k && rightChild > kv.k)
					break;
				else if(leftChild < rightChild) {
					ctx.val[kvpos] = ctx.val[kvpos*2+1];
					ctx.val[kvpos*2+1] = kv;
					kvpos = kvpos*2+1;
				}
				else {
					ctx.val[kvpos] = ctx.val[kvpos*2+2];
					ctx.val[kvpos*2+2] = kv;
					kvpos = kvpos*2+2;
				}
			}
			return ret;
		};
  };
  
  var lastRank = 0;
  var stamp = 1;
  var nextStamp = function () { return ++stamp; };
  
  //propagatePulse: Pulse * Array Node -> 
  //Send the pulse to each node 
  flapjax.base.propagatePulse = function (pulse, node) {
    var queue = new b.PQ(); //topological queue for current timestep
	queue.insert({k:node.rank,n:node,v:pulse});
	while(!(queue.isEmpty())) {
		var qv = queue.pop();
		qv.n.updater(function(nextPulse) {
			for(var i=0; i<qv.n.sendsTo.length;i++)
				queue.insert({k:qv.n.sendsTo[i].rank,n:qv.n.sendsTo[i],v:nextPulse});
		},new b.Pulse(qv.v.stamp,qv.v.value));
	}
  };
  
  //Event: Array Node b * ( (Pulse a -> Void) * Pulse b -> Void)
  e.Event = function (nodes,updater) {
    this.updater = updater;
    
    this.sendsTo = []; //forward link
    
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].sendsTo.push(this);
    }
    
    this.rank = ++lastRank;
  };
	e.Event.prototype = new Object();
  
	e.PubEvent = function(updater /* . nodes */) {
		e.Event.apply(this,[l.slice(arguments,1),updater]);
	}
	e.PubEvent.prototype = e.Event.prototype;
	annotate(e.PubEvent,['Event','Node']);
  
  //createNode: Array Node a * ( (Pulse b ->) * (Pulse a) -> Void) -> Node b
  e.createNode = function (nodes, updater) {
		return new e.Event(nodes,updater);
	};
	annotate(e.createNode,['event_e']);
  
  //attachListenerNode: Node * Node -> Voids
  //flow from node to dependent
  //note: does not add flow as counting for rank nor updates parent ranks
  e.attachListenerNode = function (node, dependent) {
    if (!(node instanceof e.Event)) { throw 'attachListenenerNode: expects event as first arg';} //SAFETY
    if (!(dependent instanceof e.Event)) { throw 'attachListenenerNode: expects event as second arg';} //SAFETY
    
    node.sendsTo.push(dependent);
		if(node.rank > dependent.rank) {
			var lowest = lastRank+1;
			var q = [dependent];
			while(q.length) {
				var cur = q.splice(0,1)[0];
				cur.rank = ++lastRank;
				q = q.concat(cur.sendsTo);
			}
		}
  };
	annotate(e.attachListenerNode,[],0,[e.Event.prototype],['attachListener']);
  
  //removeListenerNode: Node * Node -> Boolean
  //remove flow from node to dependent
  //note: does not remove flow as counting for rank nor updates parent ranks
  e.removeListenerNode = function (node, dependent)
  {
    if (!(node instanceof e.Event)) { throw 'removeListenerNode: expects event as first arg';} //SAFETY
    if (!(dependent instanceof e.Event)) { throw 'removeListenenerNode: expects event as second arg';} //SAFETY
    
    var foundSending = false;
    for (var i = 0; i < node.sendsTo.length && !foundSending; i++) {
      if (node.sendsTo[i] == dependent) {
        node.sendsTo.splice(i, 1);
        foundSending = true;
      }
    }
    
    return foundSending;
  };
	annotate(e.removeListenerNode,[],0,[e.Event.prototype],['removeListener']);
  
  //createConstantNode: Array Node U Node * a -> Node a
  e.createConstantNode = function (nodes, value) {
    return e.createNode(
      nodes instanceof Array ? nodes : [nodes], 
      function (send, pulse) {
        pulse.value = value;
        send(pulse);
      });
  };
	annotate(e.createConstantNode,['constant_e','replaceValue_e'],
    0,[e.Event.prototype],['constant_e','constant','replaceValue_e','replaceValue']);
  
	e.createTimeSyncNode = function(nodes) {
		var nqs = l.map(function(n) {
				var qpulse = [];
				return {q:qpulse,v:e.createNode([n],function(s,p) {qpulse.push(p.value); s(p);},nodes)};
    },nodes);
		return e.createNode(
      l.map(function(n) {return n.v;},nqs), function(s,p) {
        var allfull = l.fold(function(n,acc) {return n.q.length && acc;},true,nqs);
        if(allfull) {
          p.value = l.map(function(n) {return n.q.shift();},nqs);
          s(p);
      }});
	};
	annotate(e.createTimeSyncNode,['sync_e']);
  
	//This is up here so we can add things to its prototype that are in flapjax.combinators
  be.Behaviour = function (event, init, updateFn) {
   
    var behave = this;
    this.last = init;
    
    //sendEvent to this might impact other nodes that depend on this event
    //sendBehaviour defaults to this one
	if(event instanceof e.Event) {
		this.underlyingRaw = event;
    	this.underlying =
		    e.createNode(
		      [event], 
		      function (s, p) {
		        behave.last = p.value; 
		        s(p);
		      });
	}
	else {
		this.underlyingRaw = e.createNode(
			event,
			function(s, p) {
				behave.last = updateFn(p.value);
				p.value = behave.last;
				s(p);
			});
		this.underlying = this.underlyingRaw;
	}
	};
    //unexposed, sendEvent to this will only impact dependents of this behaviour
	be.Behaviour.prototype = new Object();
	annotate(be.Behaviour,['Behaviour','Behavior']);
  
  //good for leaves, easy hook to forward pulses
  c.createEventReceiver = function () {
    return e.createNode(
      [], 
      function(send, pulse) {send(pulse);});
  };
	annotate(c.createEventReceiver,['receiver_e']);
  
  //artificially send a pulse to a node, as if from a child
  //note that this creates a new timestamp and new event queue
  c.sendEvent = function (node, value) {
    if (!(node instanceof e.Event)) { throw 'sendEvent: expected Event as first arg'; } //SAFETY
    
    b.propagatePulse(
      new b.Pulse(nextStamp(), value),node);
  };
  annotate(c.sendEvent,['sendEvent'],0,[e.Event.prototype],['sendEvent']);
  
  c.sendPulse = function (node, value, pulseObserver) {
    //SAFETY
    if (!(node instanceof e.Event) &&
      !(node instanceof be.Behaviour)) { 
      throw 'sendPulse: expected Event or Behaviour as first arg'; }
      
      // get the Event part of the Behaviour, if that's what we have
      if (node instanceof be.Behaviour) {
        node = node.underlyingRaw;
      }
      
      var pulse = new b.Pulse(nextStamp(), value);
      pulseObserver(pulse);
      
      b.propagatePulse(pulse,node);
  };
  annotate(c.sendPulse,['sendPulse'],0,[e.Event.prototype,be.Behaviour.prototype],['sendPulse']);
  
  //TODO case event is a value
  //wrap the value of a node
  c.map_ev = function (proc, event) {
    if (!(proc instanceof Function)) { throw 'map_ev: expected function as first arg'; } //SAFETY
    if (!(event instanceof e.Event)) { throw 'map_ev: expected Event as second arg'; } //SAFETY
    
    return e.createNode([event], function (s, p) { p.value = proc(p.value); s(p); });
  };
  
  c.not_e = function (event) {
    if (!(event instanceof e.Event)) { throw 'not_e: expected Event as first arg'; } //SAFETY
    
    return c.map_ev(function (v) { return !v; }, event);
  };
  annotate(c.not_e,['not_e'],0,[e.Event.prototype],['not_e','not']);
  
  //wrap a node, filtering out pulses that fail a predicate on their value
  // MMG: allow time-varying pred?
  c.filter_ev = function (pred, event) {
    if (!(pred instanceof Function)) { throw 'filter_ev: expected pred as first arg'; } //SAFETY
    if (!(event instanceof e.Event)) { throw 'filter_ev: expected Event as second arg'; } //SAFETY
    
    return e.createNode(
      [event], 
      function (send, pulse) {if (pred(pulse.value)) { send(pulse); } });
  };
  annotate(c.filter_ev,['filter_e'],1,[e.Event.prototype],['filter_e','filter']);
  
  //allow any pulse from a group to  propagate out of a new node
  c.merge_e = function (/* . dependentNodes */ ) {
    var dependentNodes = 
    ((arguments.length === 0)? [] : l.slice(arguments, 0)); 
    return e.createNode(dependentNodes, function(s,p) {s(p);}); 
  };
  annotate(c.merge_e,['merge_e'],0,[e.Event.prototype],['merge','merge_e']);
  
  //allow a node to propagate only once
  c.once_e = function (event) {
    if (!(event instanceof e.Event)) { throw 'once_e: expected Event as first arg'; } //SAFETY
    
    var done = false;
    return e.createNode(
      [event],
      (function () {
          done = false;
          return function (send, pulse) {
            if (!done) {done = true; send(pulse); }
      }; })());
  };
  annotate(c.once_e,['once_e'],0,[e.Event.prototype],['once','once_e']);
  
  //skip first pulse - can be encoded as collect..
  c.skipFirst = function (event) {
    if (!(event instanceof e.Event)) { throw 'skipFirst_e: expected Event as first arg'; } //SAFETY
    
    return e.createNode(
      [event],
      (function () {
          var done = false;
          return function (send, pulse) {
            if (done) {send(pulse); }
            else {done = true; }
      }; })());
  };
  annotate(c.skipFirst,['skipFirst_e'],0,[e.Event.prototype],['skipFirst','skipFirst_e']);
  
  c.collect_ev = function (event, init, fold) {
    var acc = init;
    return c.map_ev(
      function (n) {
        var next = fold(n, acc);
        acc = next;
        return next;
      },
      event); 
  };
  annotate(c.collect_ev,['collect_e'],0,[e.Event.prototype],['collect_e','collect','transformWithMemory']);
  
  //switch_e: Event Event a -> Event a
  c.switch_e = function (eventStreamsE) {
    var prevSourceE = null;
    
		var receiverE = new c.createEventReceiver();
    
		//XXX could result in out-of-order propagation! Fix!
		e.createNode(
      [eventStreamsE],
      function (s, p) {
        if (!(p.value instanceof e.Event)) { throw 'switch_e: expected event as value of input event'; } //SAFETY
        if (prevSourceE != null) {
          e.removeListenerNode(prevSourceE, receiverE);
        }
        prevSourceE = p.value;
        e.attachListenerNode(prevSourceE, receiverE);
      });
    
    return receiverE;
  };
  annotate(c.switch_e,['switch_e'],0,[e.Event.prototype],['switch_e','forwardLatest']);
  
  //With topological evaluation, squeeze_e is a noop
  annotate(function(a) {return c.merge_e(a);},['squeeze_e'],0,[e.Event.prototype],['squeeze_e']);
  
  //warning: branches will get evaluated, just not propagated
  c.if_e = function (testNode, thenExpr, elseExpr) {
		if(testNode instanceof e.Event) {
			var testStamp = -1;
			var tVal = false; 
			e.createNode([testNode],function(s,p) {testStamp = p.stamp; tVal = p.value;});
			return c.merge_e(
        e.createNode([thenExpr],function(s,p) {if(tVal && (testStamp == p.stamp)) s(p);}),
        e.createNode([elseExpr],function(s,p) {if((!tVal) && (testStamp == p.stamp)) s(p);}));
		}
		else {
      return (testNode? thenExpr : elseExpr);
		}
  };
	annotate(c.if_e,['if_e','choose_e'],0,[e.Event.prototype],['if_e','choose_e','choose']);
  
  //TODO: test expr really should be a thunk as well
  //TODO: return undefined or null? currently undefined
  //TODO: special case last argument as an else? Its pred is fn.{return true}
  c.cond_e = function (/*. predValArrays */) {
    var predValArrays = l.slice(arguments, 0);
    var acc = e.createConstantNode([], undefined);
    for (var i = predValArrays.length - 1; i > -1; i--) {
      acc = c.if_e(predValArrays[i][0], predValArrays[i][1], acc);
    }
    return acc; 
  };
	annotate(c.cond_e,['cond_e']);
  
  //TODO when should it return false?
  //TODO fix sig
  //and_e: . Array [Node] Boolean -> Node Boolean
  c.and_e = function (/* . nodes */) {
    var nodes = l.slice(arguments, 0);
    
    var acc = (nodes.length > 0)? 
    nodes[nodes.length - 1] : e.createConstantNode([],true);
    
    for (var i = nodes.length - 2; i > -1; i--) {
      acc = c.if_e(
        nodes[i], 
        acc, 
        c.map_ev(function (_) {return false;}, nodes[i]));
    }
    return acc;
  };
	annotate(c.and_e,['and_e'],0,[e.Event.prototype],['and_e','and']);
  
  c.or_e = function () {
    var nodes = l.slice(arguments, 0);
    var acc = (nodes.length > 2)? 
    nodes[nodes.length - 1] : e.createConstantNode([],false);
    for (var i = nodes.length - 2; i > -1; i--) {
      acc = c.if_e(
        nodes[i],
        nodes[i],
        acc);
    }
    return acc;
  };  
	annotate(c.or_e,['or_e'],0,[e.Event.prototype],['or_e','or']);
  
  //TODO: manual timer management stinks.
  // TODO: Name turn off or somethin
  c.___timerID = 0;
  c.__getTimerId = function () { return ++c.___timerID; };    
  c.timerDisablers = [];
  
  c.disableTimerNode = function (node) { c.timerDisablers[node.__timerId](); };
  
  c.disableTimer = function (v) {
    if (v instanceof be.Behaviour) { 
      c.disableTimerNode(v.underlyingRaw); 
    } else if (v instanceof e.Event) {
      c.disableTimerNode(v);
    }
  };
	annotate(c.disableTimer,['disableTimer'],0,[e.Event.prototype],['disableTimer']);
  
  c.createTimerNodeStatic = function (interval) {
    var node = c.createEventReceiver();
    node.__timerId = c.__getTimerId();
    var fn = function () {c.sendEvent(node, (new Date()).getTime());};
    var timer = setInterval(fn, interval);
    c.timerDisablers[node.__timerId] = function () {clearInterval(timer); };
    return node;
  };
  
  c.createTimerNode = function (interval) {
    if (interval instanceof be.Behaviour) {
      var receiverE = c.createEventReceiver();
      
      //the return
      var res = c.switch_e(receiverE);
      
      //keep track of previous timer to disable it
      var prevE = c.createTimerNodeStatic(be.valueNow(interval));
      
      //init
      c.sendEvent(receiverE, prevE);
      
      //interval changes: collect old timer
      e.createNode(
        [be.changes(interval)],
        function (_, p) {
          c.disableTimerNode(prevE); 
          prevE = c.createTimerNodeStatic(p.value);
          c.sendEvent(receiverE, prevE);
        });
      
      res.__timerId = c.__getTimerId();
      c.timerDisablers[res.__timerId] = function () {
        c.disableTimerNode[prevE]();
        return;
      };
      
      return res;
    } else {
      return c.createTimerNodeStatic(interval);
    }
  };
	annotate(c.createTimerNode,['timer_e'],0,[be.Behaviour.prototype],['timer_e','asTimer_e']);
  
  c.delayStatic_e = function (event, time) {
    
    var resE = c.createEventReceiver();
    
    e.createNode(
      [event],
      function (s, p) { 
        setTimeout( 
          function () { c.sendEvent(resE, p.value);}, 
      time ); });
    
    return resE;
  };
  
  //delay_e: Event a * [Behaviour] Number ->  Event a
  c.delay_e = function (event, time) {
    if (time instanceof be.Behaviour) {
      
      var receiverEE = c.createEventReceiver();
      var link = 
      {
        from: event, 
        towards: c.delayStatic_e(event, be.valueNow(time))
      };
      
			//TODO: Change semantics such that we are always guaranteed to get an event going out?
      var switcherE = 
      e.createNode(
        [be.changes(time)],
        function (s, p) {
          e.removeListenerNode(link.from, link.towards); 
          link =
          {
            from: event, 
            towards: c.delayStatic_e(event, p.value)
          };
          c.sendEvent(receiverEE, link.towards);
        });
      
      var resE =
      c.switch_e(
        receiverEE);
      
      c.sendEvent(switcherE, be.valueNow(time));
      return resE;
      
        } else { return c.delayStatic_e(event, time); }
  };
	annotate(c.delay_e,['delay_e'],0,[e.Event.prototype],['delay','delay_e']);
  
  //lift_e: ([Event] (. Array a -> b)) . Array [Event] a -> [Event] b
  c.lift_e = function (fn /*, [node0 | val0], ...*/) {
    //      if (!(fn instanceof Function)) { throw 'lift_e: expected fn as second arg'; } //SAFETY
    
    var valsOrNodes = l.slice(arguments, 0);
    //selectors[i]() returns either the node or real val, optimize real vals
    var selectors = [];
    var selectI = 0;
    var nodes = [];
    for (var i = 0; i < valsOrNodes.length; i++) {
      if (valsOrNodes[i] instanceof e.Event) {
        nodes.push(valsOrNodes[i]);
        selectors.push( 
          (function(ii) {
              return function(realArgs) { 
                return realArgs[ii];
              };
          })(selectI));
        selectI++;
      } else {
        selectors.push( 
          (function(aa) { 
              return function () {
                return aa;
              }; 
          })(valsOrNodes[i]));
      } 
    }
    
    var context = this;
		var nofnodes = l.slice(selectors,1);
    
    if (nodes.length === 0) {
      return e.createConstantNode(
        [], 
        fn.apply(context, valsOrNodes));
    } else if ((nodes.length === 1) && (fn instanceof Function)) {
      return c.map_ev(
        function () {
          var args = arguments;
          return fn.apply(
            context, 
            l.map(function (s) {return s(args);}, nofnodes));
        }, 
        nodes[0]);
    } else if (nodes.length === 1) {
      return c.map_ev(
        function (v) {
          var args = arguments;
          return v.apply(
            context, 
            l.map(function (s) {return s(args);}, nofnodes));
        }, 
        fn);                
    } else if (fn instanceof Function) {
      return c.map_ev(
        function (arr) {
          return fn.apply(
            this,
            l.map(function (s) { return s(arr); }, nofnodes));
        },e.createTimeSyncNode(nodes));
    } else if (fn instanceof e.Event) {
      return c.map_ev(
        function (arr) {
          return arr[0].apply(
            this, 
            l.map(function (s) {return s(arr); }, nofnodes));
        },e.createTimeSyncNode(nodes));
        } else {throw 'unknown lift_e case';}
  };
	annotate(c.lift_e,['lift_e','transform_e','map_e','apply_e'],
    1,[e.Event.prototype],['lift_e','lift','transform_e','map_e','transform','apply_e']);
  
  //c.snapshot_e: Node a * Behaviour b -> Node b
  c.snapshot_e = function (triggerE, valueB) {
    return e.createNode(
      [triggerE],
      function (s, p) {
        p.value = be.valueNow(valueB);
        s(p);
      }
      ); 
  };
	annotate(c.snapshot_e,['snapshot_e'],0,[e.Event.prototype],['snapshot_e','snapshot','takeSnapshot']);
  
  //filterRepeats_e: Node a [* Maybe a] -> Node a
  c.filterRepeats_e = function (node, optStart) {
    if (!(node instanceof e.Event)) { throw 'filterRepeats_e: expected Event as first arg'; } //SAFETY
    
    return e.createNode(
      [node],
      function () {
				var hadFirst = optStart === undefined ? false : true;
        var prev = optStart;
        return function (s, p) {
          if ((!hadFirst) ||
            (!l.isEqual(prev, p.value))) {
          hadFirst = true;
          prev = p.value;
          s(p);
            }
        };
      }());
  };
	annotate(c.filterRepeats_e,['filterRepeats_e'],0,[e.Event.prototype],['filterRepeats_e','filterRepeats']);
  
  //credit Pete Hopkins
  c.calmStatic_e = function (triggerE, time) {
		var out = c.createEventReceiver();
    e.createNode(
      [triggerE],
      function() {
        var towards = null;
        return function (s, p) {
          if (towards !== null) { clearTimeout(towards); }
          towards = setTimeout( function () { towards = null; c.sendEvent(out,p.value) }, time );
        };
      }());
		return out;
  };
  
  //calm_e: Event a * [Behaviour] Number -> Event a
  c.calm_e = function (triggerE, time) {
    if (time instanceof be.Behaviour) {
			var out = c.createEventReceiver();
      e.createNode(
        [triggerE],
        function() {
          var towards = null;
          return function (s, p) {
            if (towards !== null) { clearTimeout(towards); }
            towards = setTimeout( function () { towards = null; c.sendEvent(out,p.value) }, be.valueNow(time));
          };
        }());
			return out;
    } else {
      return c.calmStatic_e.apply(this, arguments);       
    }
  };
	annotate(c.calm_e,['calm_e'],0,[e.Event.prototype],['calm_e','calm']);
  
  //blind_e: Event a * [Behaviour] Number -> Event a
  c.blind_e = function (triggerE, time) {
    return e.createNode(
      [triggerE],
      function () {
        var intervalFn = 
        time instanceof be.Behaviour?
        function () { return be.valueNow(time); }
        : function () { return time; };
        var lastSent = (new Date()).getTime() - intervalFn() - 1;
        return function (s, p) {
          var curTime = (new Date()).getTime();
          if (curTime - lastSent > intervalFn()) {
            lastSent = curTime;
            s(p);
          }
        };
      }());
  };
	annotate(c.blind_e,['blind_e'],0,[e.Event.prototype],['blind_e','blind']);
  
  be.hold = function (event, init) {
    if (!(event instanceof e.Event)) { throw 'hold: expected event as second arg'; } //SAFETY
    
    return new be.Behaviour(event, init);
  };
	annotate(be.hold,['hold'],
    0,[e.Event.prototype],['hold','toBehaviour','toBehavior','startsWith']);
  
  be.valueNow = function(behave) {return behave.last;};
	annotate(be.valueNow,['valueNow'],0,[be.Behaviour.prototype],['valueNow']);
  
  be.changes = function (behave) {return behave.underlying;};
	annotate(be.changes,['changes'],0,[be.Behaviour.prototype],['changes','toEvent']);
  
  //switch_b: Behaviour Behaviour a -> Behaviour a
  be.switch_b = function (behaviourCreatorsB) {       
    var init = be.valueNow(behaviourCreatorsB);
    
    var prevSourceE = null;
    
    var receiverE = new c.createEventReceiver();
    
		//XXX could result in out-of-order propagation! Fix!
    var makerE = 
    e.createNode(
      [be.changes(behaviourCreatorsB)],
      function (_, p) {
        if (!(p.value instanceof be.Behaviour)) { throw 'switch_b: expected Behaviour as value of Behaviour of first argument'; } //SAFETY
        if (prevSourceE != null) {
          e.removeListenerNode(prevSourceE, receiverE);
        }
        
        prevSourceE = be.changes(p.value);
        e.attachListenerNode(prevSourceE, receiverE);
        
        c.sendEvent(receiverE, be.valueNow(p.value));
      });
    
    if (init instanceof be.Behaviour) {
      c.sendEvent(makerE, init);
    }
    
    return be.hold(
      receiverE,
      init instanceof be.Behaviour? be.valueNow(init) : init);
  };
	annotate(be.switch_b,['switch_b'],0,[be.Behaviour.prototype],['switch_b','forwardLatest']);
  
  //TODO test, signature
  be.createTimerBehaviour = function (interval) {
    return be.hold(
      c.createTimerNode(interval), 
      (new Date()).getTime());
  };
	annotate(be.createTimerBehaviour,['timer_b'],0,[be.Behaviour.prototype],['timer_b','asTimer_b']);
  
  
  //TODO test, signature
  be.delayStatic_b = function (triggerB, time, init) {
    return be.hold(
      c.delayStatic_e(be.changes(triggerB), time),
      init);
  };
  
  //TODO test, signature
  be.delay_b = function (triggerB, time, init) {
    if (time instanceof be.Behaviour) {
      return be.hold(
        c.delay_e(
          be.changes(triggerB), 
          time),
        arguments.length > 3 ? init : be.valueNow(triggerB));
    } else {
      return be.delayStatic_b(
        triggerB, 
        time,
        arguments.length > 3 ? init : be.valueNow(triggerB));
    }
  };
	annotate(be.delay_b,['delay_b'],0,[be.Behaviour.prototype],['delay_b','delay']);
  
  //artificially send a pulse to underlying event node of a behaviour
  //note: in use, might want to use a receiver node as a proxy or an identity map
  be.sendBehaviour = function (behave, val) {
    if (!(behave instanceof be.Behaviour)) { throw 'sendBehaviour: expected Behaviour as first arg'; } //SAFETY
    c.sendEvent(behave.underlyingRaw, val);
  };
	annotate(be.sendBehaviour,['sendBehaviour','sendBehavior'],0,[be.Behaviour.prototype],['sendBehaviour','sendBehavior']);
  
  be.if_b = function (testB, trueB, falseB) {
    //TODO auto conversion for behaviour funcs
    if (!(testB instanceof be.Behaviour)) { testB = be.createConstantB(testB); }
    if (!(trueB instanceof be.Behaviour)) { trueB = be.createConstantB(trueB); }
    if (!(falseB instanceof be.Behaviour)) { falseB = be.createConstantB(falseB); }
    return be.lift_b(function(te,t,f) {if(te) return t; else return f;},testB,trueB,falseB);
  };
	annotate(be.if_b,['if_b','choose_b'],0,[be.Behaviour.prototype],['if_b','choose_b','choose']);
  
  //cond_b: . [Behaviour boolean, Behaviour a] -> Behaviour a
  be.cond_b = function (/* . pairs */ ) {
    var pairs = l.slice(arguments, 0);
	return be.lift_b.apply({},[function() {
			for(var i=0;i<pairs.length;i++) {
				if(arguments[i]) return arguments[pairs.length+i];
			}
			return undefined;
		}].concat(l.map(function(pair) {return pair[0];},pairs).concat(l.map(function(pair) {return pair[1];},pairs))));
  };
	annotate(be.cond_b,['cond_b']);
  
  //TODO optionally append to objects
  //createConstantB: a -> Behaviour a
  be.createConstantB = function (val) {
    return new be.Behaviour(
      c.createEventReceiver(), 
      val);
  };
	annotate(be.createConstantB,['constant_b','receiver_b']);
  
	be.lift_b = function (fn /* . behaves */) {
		var args = l.slice(arguments, 1);
		//dependencies
		var constituentsE =
			l.map(be.changes,
				l.filter(function (v) { return v instanceof be.Behaviour; },
			arguments));
        
	    //calculate new vals
    	var getCur = function (v) {
	      return v instanceof be.Behaviour ? v.last : v;
	    };
    	var ctx = this;
	    var getRes = function () {
    	  return getCur(fn).apply(ctx, l.map(getCur, args));
	    };
        //gen/send vals @ appropriate time
		return new be.Behaviour(constituentsE,getRes(),getRes);
	};
	annotate(be.lift_b,['lift_b','transform_b','apply_b'],
    1,[be.Behaviour.prototype],['lift_b','transform_b','apply_b','transform','lift']);
  
  //be.and_b: Array (Behaviour boolean) -> Behaviour boolean
  be.and_b = function (/* . behaves */) {
	return be.lift_b.apply({},[function() {
			for(var i=0; i<arguments.length; i++) {if(!arguments[i]) return false;}
			return true;
	}].concat(slice(arguments,0)));
  };
  annotate(be.and_b,['and_b'],0,[be.Behaviour.prototype],['and_b','and']);
  
  be.or_b = function (/* . behaves */ ) {
	return be.lift_b.apply({},[function() {
			for(var i=0; i<arguments.length; i++) {if(arguments[i]) return true;}
			return false;
	}].concat(slice(arguments,0)));
  };
  annotate(be.or_b,['or_b'],0,[be.Behaviour.prototype],['or_b','or']);
  
  be.not_b = function (behave) {
    return be.lift_b(function (v) { return !v; }, behave);
  };
  annotate(be.not_b,['not_b'],0,[be.Behaviour.prototype],['not_b','not']);
  
  //TODO E->B transform
  be.blind_b = function (triggerB, interval) {
    return be.hold(
      c.blind_e(be.changes(triggerB), interval),
      be.valueNow(triggerB));         
  };
	annotate(be.blind_b,['blind_b'],0,[be.Behaviour.prototype],['blind_b','blind']);
  
  be.calm_b = function (triggerB, interval) {
    return be.hold(
      c.calm_e(be.changes(triggerB), interval),
      be.valueNow(triggerB));         
  };
	annotate(be.calm_b,['calm_b'],0,[be.Behaviour.prototype],['calm_b','calm']);
  
  be.arrayB =  function (init, event) {
    
    //TODO if init is undefined, getting weird display [undefined init]
    
    //====setup
    var aBox = {arr: init instanceof Array? l.slice(init, 0) : []};
    var r = c.createEventReceiver(); //mutations
    
    var resB = new be.Behaviour(
      event instanceof e.Event ? 
      c.merge_e(
        r, 
        event) : r, 
      aBox.arr);
    
    //====functional interface
    
    //note that value change is propagated at merge above
    if (event instanceof e.Event) {
      c.lift_e(
        function (arr) {
          if (arr instanceof Array) {
            aBox.arr = arr; 
          } 
          else { throw 'array_b: tried to set to value that is not an array'; } //SAFETY
        }, 
        event);
    }
    
    //====mutation interface                
    resB.mutationsE = r;
    
    var addWrite = 
    function (fnName) {
      if (aBox.arr[fnName]){
        resB[fnName] = function () {
          var args = l.slice(arguments, 0);
          if (!(aBox.arr instanceof Array)) { throw ('previous to ' + fnName + ' arr not array');}
          aBox.arr[fnName].apply(aBox.arr, args);
          if (!(aBox.arr instanceof Array)) { throw ('post ' + fnName + ' arr not array');}
          c.sendEvent(r, aBox.arr);
        };
      }
    };
    
    var addRead = 
    function (propName) {
      if (aBox.arr[propName]){
        resB[propName + 'B'] =
        new be.Behaviour(
          c.lift_e(
            function(_) {return aBox.arr[propName];},
            r),
          aBox.arr[propName]);
      }
    };
    
    l.map(
      addWrite,
      ['push', 'pop', 'reverse', 'shift', 'slice', 'splice']);
    
    l.map(
      addRead,
      ['length']);
    
    //TODO REMOVE                
    resB.lengthB = be.lift_b(function(_){return aBox.arr.length;}, resB);
    
    return resB;
    
  };
	annotate(be.arrayB,['array_b']);
  
  //========== END BELONGS IN FSERVER.JS =====================================
	//credit Scott Andrew
	//usage: flapjax.lib.addEvent(myDomObj, "mouseover", event->void )
	//warning: do not use 'this' as meaning depends on browser (myDomObj vs window)
	//addEvent: Dom * String DomEventEnum * (DomEvent -> a) -> Void
	d.addEvent = function (obj, evType, fn) {
		//TODO encode mouseleave evt, formalize new evt interface
    
		if (obj.addEventListener) {
      obj.addEventListener(evType, fn, false); //TODO true fails on Opera
      return true;
		} else if (obj.attachEvent) {
      //some reason original had code bloat here
      return obj.attachEvent("on"+evType, fn); 
		} else {
      return false; 
		}
	};
	annotate(d.addEvent,['addEvent']);
  
	//credit Dustin Diaz 
	//note: node/tag optional
	//getElementsByClass: Regexp CSSSelector * Dom * String DomNodeEnum -> Array Dom
	d.getElementsByClass = function (searchClass, node, tag) {
		var classElements = [];
		if ( (node === null) || (node === undefined) ) { node = document; }
		if ( (tag === null) || (tag === undefined) ) { tag = '*'; }
		var els = node.getElementsByTagName(tag);
		var elsLen = els.length;
		var pattern = new RegExp("(^|\\s)"+searchClass+"(\\s|$)");
		for (var i = 0, j = 0; i < elsLen; i++) {
      if ( pattern.test(els[i].className) ) {
        classElements.push(els[i]);
      }
		}
		return classElements;
	};
	annotate(d.getElementsByClass,['getElementsByClass','$$']);
  
	//assumes IDs already preserved
	//swapDom: (Dom a U String) [* (Dom b U String)] -> Dom a
	d.swapDom = function(replaceMe, withMe) {
		if ((replaceMe === null) || (replaceMe === undefined)) { throw ('swapDom: expected dom node or id, received: ' + replaceMe); } //SAFETY
    
		var replaceMeD = flapjax.dom.getObj(replaceMe);
		if (!(replaceMeD.nodeType > 0)) { throw ('swapDom expected a Dom node as first arg, received ' + replaceMeD); } //SAFETY
    
		if (withMe) {
      var withMeD = flapjax.dom.getObj(withMe);
      if (!(withMeD.nodeType > 0)) { throw 'swapDom: can only swap with a DOM object'; } //SAFETY
      try {
        if(withMeD != replaceMeD) replaceMeD.parentNode.replaceChild(withMeD, replaceMeD);
      } catch (e) {
        throw('swapDom error in replace call: withMeD: ' + withMeD + ', replaceMe Parent: ' + replaceMeD + ', ' + e + ', parent: ' + replaceMeD.parentNode);                    
      }
		} else {
      replaceMeD.parentNode.removeChild(replaceMeD); //TODO isolate child and set innerHTML to "" to avoid psuedo-leaks?
		}
		return replaceMeD;
	};
	annotate(d.swapDom,['swapDom']);
  
	//getObj: String U Dom -> Dom
	//throws 
	//  'getObj: expects a Dom obj or Dom id as first arg'
	//  'getObj: flapjax: cannot access object'
	//  'getObj: no obj to get
	//also known as '$'
	//TODO Maybe alternative?
	d.getObj = function (name) {
		if (typeof(name) == 'object') { return name; }
		else if ((typeof(name) == 'null') || (typeof(name) == 'undefined')) {
      throw 'getObj: expects a Dom obj or Dom id as first arg';
		} else {
      
      var res = 
			document.getElementById ? document.getElementById(name) :
			document.all ? document.all[name] :
			document.layers ? document.layers[name] :
			(function(){ throw 'getObj: flapjax: cannot access object';})();
      if ((res === null) || (res === undefined)) { 
        throw ('getObj: no obj to get: ' + name); 
      }
      return res;
		}
	};
	annotate(d.getObj,['getObj','$']);
  
  //topE: Event alpha
  //alerts whenever an inserted dom changes
  d.topE = c.createEventReceiver(); 
	annotate(d.topE,['topE']);
  
  //helper to reduce obj look ups
  //getDynObj: domNode . Array (id) -> domObj
  //obj * [] ->  obj
  //obj * ['position'] ->  obj
  //obj * ['style', 'color'] ->  obj.style
  d.getMostDom = function (domObj, indices) {
    var acc = d.getObj(domObj);
    if ( (indices === null) ||
      (indices === undefined) ||
    (indices.length < 1)) {
    return acc;
    } else {
      for (var i = 0; i < indices.length - 1; i++) {
        acc = acc[indices[i]];
      }
      return acc;
    }       
  };
  
  d.getDomVal = function (domObj, indices) {
    var val = d.getMostDom(domObj, indices);
    if (indices && indices.length > 0) {
      val = val[indices[indices.length - 1]];
    }
    return val;
  };
  
	d.TagB = function(tagName,args) {
		this.resE = c.createEventReceiver();
		this.currentTag = document.createElement(tagName);
		this.extractParameters(args);
		this.insertChildrenNodes();
		this.styleHooks = [];
		this.styleChangedE = c.createEventReceiver();
		var ctx = this;
		c.map_ev(function(_) {
				var oldTag = ctx.currentTag;
				ctx.currentTag = document.createElement(tagName);
        while (oldTag.firstChild) {
          ctx.currentTag.appendChild(oldTag.removeChild(oldTag.firstChild));
				}
				while(ctx.styleHooks.length) e.removeListenerNode(ctx.styleHooks.pop(),ctx.styleChangedE);
        ctx.enstyle(ctx.currentTag,ctx.attribs);
        c.sendEvent(ctx.resE, ctx.currentTag);
		},this.styleChangedE);
		this.enstyle(this.currentTag,this.attribs);
    this.resB = be.hold(this.resE, this.currentTag);
	};
	d.TagB.prototype = {
    // Array [[Behaviour] Object *] [[Behaviour] Array] [Behaviour] Dom U String U undefined
    //   --> {attribs: Array [Behaviour] Object, arrs: Array [Behaviour] Array [Behaviour] Dom }
    // split an arguments array into:
    //   1. arrs: (coalesced, and possibly time varying) arrays of dom objects 
    //   2. attribs: attribute objects
		extractParameters: function(args) {
			this.arrs = [];
			var attribs = [];
      
			var curarr = [];
			this.arrs.push(curarr);
			for (var i = 0; i < args.length; i++) {
				if (args[i] instanceof be.Behaviour) {
					var vn = be.valueNow(args[i]);
					if (vn instanceof Array) {	        
						this.arrs.push(args[i]);
						curarr = [];
						this.arrs.push(curarr);
					} else {
						if ( ((typeof(vn) == 'object') && (vn.nodeType == 1)) ||
              (typeof(vn) == 'string') || (vn == undefined)) {
            curarr.push(args[i]);
              } else if (typeof(vn) == 'object') {
                attribs.push(args[i]);
              }
              else { throw ('createParameterizedTagB: unknown behaviour argument argument ' + i); } //SAFETY
					}
				} else {
					if (args[i] instanceof Array) {
						var arr = args[i];
						for (var j = 0; j < arr.length; j++) { curarr.push(arr[j]); }
					} else {
						var vn = args[i];
						if ( ((typeof(vn) == 'object') && (vn.nodeType == 1)) ||
              (typeof(vn) == 'string') || (vn == undefined)) {
						curarr.push(args[i]);
              } else if (typeof(vn) == 'object') {
                attribs.push(args[i]);
              }
					}
				}
			};
			if(attribs.length > 1) throw ('createParameterizedTagB ' + tagName + ': more than one attribute (' + attribs.length + ')');
			this.attribs = attribs.length > 0 ? attribs[0] : {};
		},
		insertChildrenNodes: function() {
			var ctx = this;
      
			function quickNode(e) { 
        if ((typeof(e) == 'object') && (e.nodeType))
					return e; 
        else if ( e == undefined )
					return document.createTextNode(''); 
        else 
          return document.createTextNode(e); 
      }
      
			function unBehaviourize(arr) {
				return l.map(function(n) {return (n instanceof be.Behaviour) ? be.valueNow(n) : n;},arr)
			}
      
			var lnodes = l.map(function() {return [];},this.arrs);
			var arrLastVals = l.map(unBehaviourize,unBehaviourize(this.arrs));
      
			var arrChangesE = c.createEventReceiver();
			var nodeChangesE = c.createEventReceiver();
			
			function attachNodes(i,arr) {
				for(var j=0;j<arr.length;j++) {
					var cnode = arr[j];
					if(cnode instanceof be.Behaviour) {
						var newnode = (function(jj) {
                return c.map_ev(function(n) {return {index:i,jdex:jj,val:n};},be.changes(cnode));
						})(j);
						lnodes[i].push(newnode);
						e.attachListenerNode(newnode,nodeChangesE);
						cnode = be.valueNow(cnode);
					}
				}
			}
      
			// Behaviour arrays change
			c.map_ev(function(ai) {
            	var i = ai.index;
	            var newarr = ai.val;
	            while(lnodes[i].length) {
	              var ln = lnodes[i].pop();
	              e.removeListenerNode(ln,nodeChangesE);
    	        }
	            var newvals = l.map(function(n) {return quickNode(n);},unBehaviourize(newarr));
	            for(var j=0;j<arrLastVals[i].length;j++)
	              ctx.currentTag.removeChild(arrLastVals[i][j]);
	            if(newvals.length) {
	              var nextNode = null;
	              for(ii = i+1; ii < arrLastVals.length && !(arrLastVals[ii].length) ; ii++);
	              if(ii < arrLastVals.length) nextNode = arrLastVals[ii][0];
	              for(var j=0; j<newvals.length; j++) ctx.currentTag.insertBefore(newvals[j],nextNode);
	            }
	            arrLastVals[i] = newvals;
	            attachNodes(i,newarr);
				c.sendEvent(ctx.resE,ctx.currentTag);
			},arrChangesE);
			c.map_ev(function(ni) {
            	var i = ni.index;
	            var j = ni.jdex;
	            var newnode = quickNode(ni.val);
	            d.swapDom(arrLastVals[i][j],newnode);
	            arrLastVals[i][j] = newnode;
				c.sendEvent(ctx.resE,ctx.currentTag);
			},nodeChangesE);
      
			for(var i=0; i<this.arrs.length;i++) {
				for(var j=0; j<arrLastVals[i].length; j++) {
					arrLastVals[i][j] = quickNode(arrLastVals[i][j]);
					this.currentTag.appendChild(arrLastVals[i][j]);
				}
				if(this.arrs[i] instanceof be.Behaviour) {
					attachNodes(i,be.valueNow(this.arrs[i]));
					var newnode = (function(ii) {return c.map_ev(function(na) {return {index:ii,val:na};},be.changes(ctx.arrs[ii]));})(i);
					e.attachListenerNode(newnode,arrChangesE);
				}
				else {
					attachNodes(i,this.arrs[i]);
				}
			}
		},
		enstyle: function(obj,vals) {
			//build & record hook if dynamic collection
			if (vals instanceof be.Behaviour) {
				if (!(typeof(be.valueNow(vals)) == 'object')) { throw 'enstyle: expected object literal as behaviour value'; } //SAFETY
				this.styleHooks.push(be.changes(vals));
				e.attachListenerNode(be.changes(vals),this.styleChangedE);
			}
			var valsV = vals instanceof be.Behaviour ? be.valueNow(vals) : vals;
			if (typeof(valsV) == 'object') {
				for (var i in valsV) {
					if (!(Object.prototype) || !(Object.prototype[i])) {
						this.enstyleProperty(obj,valsV, i);
					}
				}
			} 
			else { throw 'enstyle: expected object literals'; } //SAFETY
		},
    enstyleProperty: function (obj, vals, i) {
      if (vals[i] instanceof be.Behaviour) {
        if (typeof(be.valueNow(vals[i])) == 'object') {
          this.enstyle(obj[i], vals[i]);
        }
				else {
          obj[i] = be.valueNow(vals[i]);
					c.map_ev(function(v) {obj[i] = v;},be.changes(vals[i]));
				}
			}
			else {
        if (typeof(vals[i]) == 'object') {
          this.enstyle(obj[i], vals[i]);
        } else {
          obj[i] = vals[i];
        }
      }
    }
	};
  
	d.createParameterizedTagB = function(tagName) {
		return new d.TagB(tagName,l.slice(arguments,1)).resB;
	}
  
  d.enstyleStaticProperty = function (obj, props, index, oCache) {
    if (typeof(props[index]) == 'object') {
      for (var i in props[index]) {
        if (!(Object.prototype) || !(Object.prototype[i])) {
          d.enstyleStaticProperty(obj[index], props[index], i, oCache);
        }
      }
    } else {
      obj[index] = props[index];
			if (index == 'checked')	obj['defaultChecked'] = props[index]; /* TODO: this should maybe be elsewhere? */
			if (index == 'selected') obj['defaultSelected'] = props[index]; /* TODO: this should maybe be elsewhere? */
    }
  };
  
  d.staticTagMaker = function (tagName) {
    
    return function () {
      
      var tagD = document.createElement(tagName);
      if (!(tagD.nodeType > 0)) { throw (tagName + ': invalid tag name'); } //SAFETY
      
      //partition input
      
      //          if (arguments[1] === null || arguments[1] === undefined) { arguments[1] = {}; }
      var attribs = [];
      for (var i = 0; i < arguments.length; i++) {
        if (arguments[i] instanceof Array) {
          for (var j = 0; j < arguments[i].length; j++) {
            if (arguments[i][j]) {
              tagD.appendChild(
                (typeof(arguments[i][j]) == 'object' &&
                  arguments[i][j].nodeType > 0)?
                arguments[i][j] :
                document.createTextNode(arguments[i][j]));
            }
          }
        } else if (!arguments[i]) {
          //ignore
        } else if ((typeof(arguments[i]) == 'object') && 
          (arguments[i].nodeType > 0)) {
        tagD.appendChild(arguments[i]);
          } else if (typeof(arguments[i]) == 'object') {
            attribs.push(arguments[i]);
          } else {
            tagD.appendChild(document.createTextNode(arguments[i]));                    
          }
      }
      
      if (attribs.length == 1) { 
        for (var k in attribs[0]) {
          if (!(Object.prototype) || !(Object.prototype[k])) {
            d.enstyleStaticProperty(tagD, attribs[0], k);   
          }
        }
      } else if (attribs.length >  0) { 
        throw 'static enstyle: expected object literals'; //SAFETY
      } /* else {
      alert('no attribs on: ' + tagName);
      } */
      
      
      return tagD;
    };
  };
  
  
  
  var generatedTags = 
  [ "a", "b", "blockquote", "br", "button", "canvas", "div", "fieldset", 
  "form", "font", "h1", "h2", "h3", "h4", "hr", "img", "iframe", "input", 
  "label", "legend", "li", "ol", "optgroup", "option", 
  "p", "pre", "select", "span", "strong", "table", "tbody", 
  "td", "textarea", "tfoot", "th", "thead", "tr", "tt", "ul" ];
  
  l.map(
    function (tagName) { 
      
      var upper = tagName.toUpperCase();
      
      //d.<TAG>B
      d[upper + 'B'] = function () { 
        return d.createParameterizedTagB.apply(this, [tagName].concat(l.slice(arguments,0)));
      };          
			annotate(d[upper+'B'],[upper+'B']);
      
      //d.<TAG>
      d[upper] = d.staticTagMaker(tagName);  //faster, simple
      /*              function () {
      // 8/16/06 - leo - arguments bug
      // more forgiving: allows reactive children (just doesn't propagate them)
      var args = [b.maybeEmpty].concat(l.slice(arguments, 0)); 
      return be.valueNow(d[upper + 'B'].apply(this, args));
      }; */
			annotate(d[upper],[upper]);
    },
    generatedTags);
  
  //TEXTB: Behaviour a -> Behaviour Dom TextNode    
  d.TEXTB = function (strB) {
    //      if (!(strB instanceof be.Behaviour || typeof(strB) == 'string')) { throw 'TEXTB: expected Behaviour as second arg'; } //SAFETY
    if (!(strB instanceof be.Behaviour)) { strB = be.createConstantB(strB); }
    
    return be.hold(
      c.map_ev(
        function (txt) { return document.createTextNode(txt); },
        be.changes(strB)),
      document.createTextNode(be.valueNow(strB)));
  };
	annotate(d.TEXTB,['TEXTB']);
  
  d.TEXT = function (strB) {
    return be.valueNow(d.TEXTB(b.maybeEmpty, strB));
  };
	annotate(d.TEXT,['TEXT']);
  
  //tagRec: Array (EventName a) * 
  //      ( .Array (Event a) * Array (Event a) -> Behaviour Dom) -> Behaviour Dom
  //note: does not need to reconstruct if dom node did not change
  d.tagRec = function (eventNames, maker) {
    if (!(eventNames instanceof Array)) { throw 'tagRec: expected array of event names as first arg'; } //SAFETY
    if (!(maker instanceof Function)) { throw 'tagRec: expected function as second arg'; } //SAFETY
    
    var namedA = [];
    var receiversAEE = []; 
    
    var switches =
    l.map(
      function (eventName) {
        receiversAEE[eventName] = c.createEventReceiver();
        namedA[eventName] = c.switch_e(receiversAEE[eventName]);
        return namedA[eventName];
      },
      eventNames);
    
    var resB = maker.apply(this, switches);
    var prev = undefined; 
    var interceptE = 
    e.createNode(
      [be.changes(resB)],
      function (_, p) {
        if (!l.isEqual(p.value, prev)) {
          prev = p.value;
          for (var i = 0; i < eventNames.length; i++) {
            c.sendEvent(
              receiversAEE[eventNames[i]],
              d.extractEvent_e(p.value, eventNames[i]));
          }
        }
      });
    c.sendEvent(interceptE, be.valueNow(resB)); //TODO manual thread?
    return resB;
  };
	annotate(d.tagRec,['tagRec','nodeWithOwnEvents']);
  
  d.eventCounter = 0;
  d.getEventName = function (domObj) {
    var id = null;
    try {
      id = domObj.getAttribute('id');
        } catch (exn) {}
        if ( (id === null) || (id === undefined) || (id.length < 1)) {
          id = 'flapjaxDomEvent' + d.eventCounter++;
          domObj.id = id; //TODO check
        }
        return id;
  };
  
  d.domEvents = [];
  
  //extractEventStatic_e: Dom * String -> Event
  d.extractEventStatic_e = function (domObj, eventName) {
    domObj = d.getObj(domObj);
    var id = d.getEventName(domObj);
    
    if ((eventName === undefined) || (eventName === null)) { throw 'extractEvent_e: no evt name specified as third arg'; }
    
    if (!d.domEvents[id]) { d.domEvents[id] = []; }
    
    if (!d.domEvents[id][eventName]) {
      d.domEvents[id][eventName] = c.createEventReceiver();
      d.addEvent(
        domObj, 
        eventName, 
        function (evt) {
          var event = evt;
          if (!evt) { event = window.event; }
          //                  event.cancelBubble = true;
          //                  if (event.stopPropagation) {event.stopPropagation();}
          c.sendEvent(d.domEvents[id][eventName],event);
          return true; /* important for IE, false would prevent things like a checkbox actually checking */
        });
    }
    return c.map_ev(
      function (v) {return v; }, 
      d.domEvents[id][eventName]);
  };
  
  //extractEvent_e: [Behaviour] Dom * String -> Event
  d.extractEvent_e = function (domObjB, eventName) {
    if (!(domObjB instanceof be.Behaviour)) {
      return d.extractEventStatic_e.apply(this, arguments);
    } else {
      var r = c.createEventReceiver();
      var evtEE = c.map_ev( //Event Dom -> Event Event eventName
        function (domD) {
          return d.extractEventStatic_e(
            domD,
            eventName);
        },
        c.merge_e(be.changes(domObjB), r));
      var resultE = c.switch_e(evtEE);
      c.sendEvent( 
        r, 
        be.valueNow(domObjB));
      return resultE;
    }
  };
  annotate(d.extractEvent_e,['extractEvent_e','$EVT'],0,[be.Behaviour.prototype],['extractEvent_e','$EVT']);
  
  //extractEvents_e: 
  //      [Behaviour] Dom  
  //      . Array String
  //      -> Event
  // ex: extractEvents_e(m, 'body', 'mouseover', 'mouseout')
  d.extractEvents_e = function (domObj /* . eventNames */) {
    var eventNames = l.slice(arguments, 1);
    
    var events = l.map(
      function (eventName) {
        return d.extractEvent_e(domObj, eventName); 
      },
      eventNames.length === 0 ? [] : eventNames);
    
    return c.merge_e.apply(this, events);
  };
  annotate(d.extractEvents_e,['extractEvents_e'],0,[be.Behaviour.prototype],['extractEvents_e']);
  
  //value of dom form object during trigger
  d.extractValueOnEvent_e = function (triggerE, domObj) {
    if (!(triggerE instanceof e.Event)) { throw 'extractValueOnEvent_e: expected Event as first arg'; } //SAFETY
    
    return be.changes(d.extractValueOnEvent_b.apply(this, arguments));
    
  };
  annotate(d.extractValueOnEvent_e,['extractValueOnEvent_e']);
  
  //extractDomFieldOnEvent_e: Event * Dom U String . Array String -> Event a
  d.extractDomFieldOnEvent_e = function (triggerE, domObj /* . indices */) {
    if (!(triggerE instanceof e.Event)) { throw 'extractDomFieldOnEvent_e: expected Event as first arg'; } //SAFETY
    var indices = l.slice(arguments, 2);
    var res =
    c.map_ev(
      function () { return d.getDomVal(domObj, indices); }, 
      triggerE);
    return res;
  };
  
  d.extractValue_e = function (domObj) {
    return be.changes(d.extractValue_b.apply(this, arguments));
  };
  annotate(d.extractValue_e,['extractValue_e','$E']);
  
  //extractValueOnEvent_b: Event * DOM -> Behaviour
  // value of a dom form object, polled during trigger
  d.extractValueOnEvent_b = function (triggerE, domObj) {
    return d.extractValueStatic_b(domObj, triggerE);
  };
  annotate(d.extractValueOnEvent_b,['extractValueOnEvent_b']);
  
  //extractValueStatic_b: DOM [ * Event ] -> Behaviour a
  //If no trigger for extraction is specified, guess one
  d.extractValueStatic_b = function (domObj, triggerE) {
    
    var objD;
    try {
      objD = flapjax.dom.getObj(domObj);
	    //This is for IE
	    if(typeof(domObj) == 'string' && objD.id != domObj) {
	    	throw 'Make a radio group';
	    }
    } catch (e) {
      objD = {type: 'radio-group', name: domObj};
    }
    
    var getter; // get value at any current point in time
    
    
    switch (objD.type)  {
      
      //TODO: checkbox.value instead of status?
    case 'checkbox': 
      
      return be.hold(
        c.filterRepeats_e(
          d.extractDomFieldOnEvent_e(
            triggerE ? triggerE : 
            d.extractEvents_e(
              objD, 
              'click', 'keyup', 'change'),
            objD,
            'checked'),objD.checked),
        objD.checked);
      
      case 'select-one':
        
        getter = function (_) {                         
          return objD.selectedIndex > -1 ? 
          (objD.options[objD.selectedIndex].value ?
            objD.options[objD.selectedIndex].value :
            objD.options[objD.selectedIndex].innerText)
			    : undefined;
        };
        
        return be.hold(
          c.filterRepeats_e(
            c.map_ev(
              getter,
              triggerE ? triggerE :
              d.extractEvents_e(
                objD,
                'click', 'keyup', 'change')),getter()),
          getter());
        
        case 'select-multiple':
          //TODO ryan's cfilter adapted for equality check
          
          getter = function (_) {
            var res = [];
            for (var i = 0; i < objD.options.length; i++) {
              if (objD.options[i].selected) {
                res.push(objD.options[i].value ? objD.options[i].value : objD.options[i].innerText);
              }
            }
            return res;
          };
          
          
          return be.hold(
            c.map_ev(
              getter,
              triggerE ? triggerE : 
              d.extractEvents_e(
                objD,
                'click', 'keyup', 'change')),
            getter());
          
          case 'text':
          case 'textarea':
          case 'hidden':
          case 'password':
            
            return be.hold(
              c.filterRepeats_e(
                d.extractDomFieldOnEvent_e(
                  triggerE ? triggerE :
                  d.extractEvents_e(
                    objD, 
                    'click', 'keyup', 'change'),
                  objD,
                  'value'),objD.value),
              objD.value);
            
            case 'button': //same as above, but don't filter repeats
              
              return be.hold(
                d.extractDomFieldOnEvent_e(
                  triggerE ? triggerE :
                  d.extractEvents_e(
                    objD, 
                    'click', 'keyup', 'change'),
                  objD,
                  'value'),
                objD.value);
              
              
              case 'radio': 
              case 'radio-group':
                
                //TODO returns value of selected button, but if none specified,
                //      returns 'on', which is ambiguous. could return index,
                //      but that is probably more annoying
                
                var radiosAD = l.filter(
                  function (elt) { 
                    return (elt.type == 'radio') &&
                    (elt.getAttribute('name') == objD.name); 
                  },
                  document.getElementsByTagName('input'));
                
                getter = 
                objD.type == 'radio' ?
                
                function (_) {
                  return objD.checked;
                } :
                
                function (_) {
                  for (var i = 0; i < radiosAD.length; i++) {
                    if (radiosAD[i].checked) {
                      return radiosAD[i].value; 
                    }
                  }
                  return undefined; //TODO throw exn? 
                };
                
                var actualTriggerE = triggerE ? triggerE :
                c.merge_e.apply(
                  this,
                  l.map(
                    function (radio) { 
                      return d.extractEvents_e(
                        radio, 
                    'click', 'keyup', 'change'); },
                      radiosAD));
                
                return be.hold(
                  c.filterRepeats_e(
                    c.map_ev(
                      getter,
                      actualTriggerE),getter()),
                  getter());
                
                default:
                  
                  throw ('extractValueStatic_b: unknown value type "' + objD.type + '"');
    }
  };
  
  d.extractValue_b = function (domObj) {
    if (domObj instanceof be.Behaviour) {
      return be.switch_b(
        be.lift_b(
          function (dom) {
            return d.extractValueStatic_b(dom);                           
          },
          domObj));
    } else {
      return d.extractValueStatic_b(domObj);
    }
  };
	annotate(d.extractValue_b,['extractValue_b','$B'],0,[be.Behaviour.prototype],['extractValue_b','$B']);
  
  d.insertedValues = []; // insertedValues: Array Event alpha
  d.insertedDoms = []; // insertedDoms: 
  
  //TODO implement
  /*  d.insertEventE  = function () { throw 'not implemented'; };
  d.insertEventB  = function () { throw 'not implemented'; }; */
  
  //into[index] = deepValueNow(from) via descending from object and mutating each field
  d.deepStaticUpdate = function (into, from, index) {
    var fV = (from instanceof be.Behaviour)? be.valueNow(from) : from;
    if (typeof(fV) == 'object') {
      for (var i in fV) {
        if (!(Object.prototype) || !(Object.prototype[i])) {
          d.deepStaticUpdate(index? into[index] : into, fV[i], i);
        }
      }
    } else {
      var old = into[index];
      into[index] = fV;
      if (!l.isEqual(old, fV)) { d.topE.sendEvent(fV); }
    }
  };
  
  //note: no object may be time varying, just the fields
  //into[index] = from
  //only updates on changes
  d.deepDynamicUpdate = function (into, from, index) {
    var fV = (from instanceof be.Behaviour)? be.valueNow(from) : from;
    if (typeof(fV) == 'object') {
      if (from instanceof be.Behaviour) {
        throw 'deepDynamicUpdate: dynamic collections not supported';
      }
      for (var i in fV) {
        if (!(Object.prototype) || !(Object.prototype[i])) {
          d.deepDynamicUpdate(index? into[index] : into, fV[i], i);
        }
      }
    } else {
      if (from instanceof be.Behaviour) {
        e.createNode(
          [be.changes(from)],
          function (s, p) {
            if (index) { 
              var old = into[index];
              into[index] = p.value;
              if (!l.isEqual(old,p.value)) { d.topE.sendEvent(p.value); }
            }
            else { into = p.value; } //TODO notify topE?
          });
      }
    }
  };
  
	
  d.insertValue = function (val, domObj /* . indices */) {
    var indices = l.slice(arguments, 2);
    var parent = d.getMostDom(domObj, indices);
    d.deepStaticUpdate(parent, val, indices ? indices[indices.length - 1] : undefined);    	
  };
  annotate(d.insertValue,['insertValue']);
  
  //TODO convenience method (default to firstChild nodeValue) 
  d.insertValueE = function (triggerE, domObj /* . indices */) {
    if (!(triggerE instanceof e.Event)) { throw 'insertValueE: expected Event as first arg'; } //SAFETY
    
    var indices = l.slice(arguments, 2);
    var parent = d.getMostDom(domObj, indices);
    
    c.map_ev(
      function (v) {
        d.deepStaticUpdate(parent, v, indices? indices[indices.length - 1] : undefined);
      },
      triggerE);
  };
  annotate(d.insertValueE,['insertValueE'],0,[e.Event.prototype],['insertValueE']);
  
  //insertValueB: Behaviour * domeNode . Array (id) -> void
  //TODO notify adapter of initial state change?
  d.insertValueB = function (triggerB, domObj /* . indices */) { 
    
    var indices = l.slice(arguments, 2);
    var parent = d.getMostDom(domObj, indices);
    
    
    //NOW
    d.deepStaticUpdate(parent, triggerB, indices ? indices[indices.length - 1] : undefined);
    
    //LATER
    d.deepDynamicUpdate(parent, triggerB, indices? indices[indices.length -1] : undefined);
    
  };
  annotate(d.insertValueB,['insertValueB'],0,[be.Behaviour.prototype],['insertValueB']);
  
	//XXX does this function actually do anything?
  //d.insertValuesB: domObj . Array ([behave a, attrib1, ..]) -> void
  d.insertValuesB = function (domObj) {
    var attribsA = 
    l.map(
      function (arr) {return l.slice(arr, 1);},
      l.slice(arguments, 1));
    var triggersAB = 
    l.map(
      function (arr) {return arr[0];},
      l.slice(arguments, 1));
    
  };
  annotate(d.insertValuesB,['insertValuesB']);
  
  //TODO copy dom event call backs of original to new? i don't thinks so
  //  complication though: registration of call backs should be scoped
  d.insertDomE = function (triggerE, domObj) {
    
    if (!(triggerE instanceof e.Event)) { throw 'insertDomE: expected Event as first arg'; } //SAFETY
    
    var objD = d.getObj(domObj);
    
    var res = c.map_ev(
      function (newObj) {
        //TODO safer check
        if (!((typeof(newObj) == 'object') && (newObj.nodeType == 1))) { 
          newObj = d.SPAN({}, newObj);
        }
        d.swapDom(objD, newObj);
        objD = newObj;
        return newObj; // newObj;
      },
      triggerE);
    
    e.attachListenerNode(res, d.topE);
    
    return res;
  };
  annotate(d.insertDomE,['insertDomE'],0,[e.Event.prototype],['insertDomE']);
  
  //insertDom: dom 
  //          * dom 
  //          [* (null | undefined | 'over' | 'before' | 'after' | 'leftMost' | 'rightMost' | 'beginning' | 'end']
  //          -> void
  // TODO: for consistency, switch replaceWithD, hookD argument order
  d.insertDom = function (hookD, replaceWithD, optPosition) {
    switch (optPosition)
    {
    case undefined:
    case null:
    case 'over':
      d.swapDom(hookD,replaceWithD);
      break;
    case 'before':  
      hookD.parentNode.insertBefore(replaceWithD, hookD);
      break;
    case 'after':
      if (hookD.nextSibling) {
        hookD.parentNode.insertBefore(replaceWithD, hookD.nextSibling);
      } else {
        hookD.parentNode.appendChild(replaceWithD);
      }
      break;
    case 'leftMost':
      if (hookD.parentNode.firstChild) { 
        hookD.parentNode.insertBefore(
          replaceWithD, 
          hookD.parentNode.firstChild);
                } else { hookD.parentNode.appendChild(replaceWithD); }
                break;
              case 'rightMost':
                hookD.parentNode.appendChild(replaceWithD);
                break;
              case 'beginning':
                if (hookD.firstChild) { 
                  hookD.insertBefore(
                    replaceWithD, 
                    hookD.firstChild);
                } else { hookD.appendChild(replaceWithD); }
                break;
              case 'end':
                hookD.appendChild(replaceWithD);
                break;
              default:
                throw ('domInsert: unknown position: ' + optPosition);
    }
  };
  
  //insertDom: dom 
  //          * dom U String domID 
  //          [* (null | undefined | 'over' | 'before' | 'after' | 'leftMost' | 'rightMost' | 'beginning' | 'end']
  //          -> void
  d.insertDomClean = function (replaceWithD, hook, optPosition) {
    //TODO span of textnode instead of textnode?
    d.insertDom(
	    d.getObj(hook), 
	    ((typeof(replaceWithD) == 'object') && (replaceWithD.nodeType > 0)) ? replaceWithD :
      document.createTextNode(replaceWithD),	    
	    optPosition);     	    
  };
  annotate(d.insertDomClean,['insertDom']);
  
  //TODO test
  //insertDomB: 
  //      [Behaviour] String U Dom 
  //      [* ( id U null U undefined ) 
  //          [* ('before' U 'after' U 'leftMost' U 'rightMost' U 'over' U 'beginning' U 'end')]]
  //      -> Behaviour a
  //if optID not specified, id must be set in init val of trigger
  //if position is not specified, default to 'over'
  //performs initial swap onload    
  d.duid = 0; //created dom node IDs: 'flapjaxduidZZZ'
  d.insertDomB = function (initTriggerB, optID, optPosition) {
    
    if (!(initTriggerB instanceof be.Behaviour)) { 
      initTriggerB = be.createConstantB(initTriggerB);
    }
    
    var triggerB = 
    be.lift_b(
      function (d) { 
        if ((typeof(d) == 'object') && (d.nodeType >  0)) {
          return d;
        } else {
          var res = document.createElement('span'); //TODO createText instead
          res.appendChild(document.createTextNode(d));
          return res;
        }
      },
      initTriggerB);
    
    var initD = be.valueNow(triggerB);
    if (!((typeof(initD) == 'object') && (initD.nodeType == 1))) { throw ('insertDomB: initial value conversion failed: ' + initD); } //SAFETY	
    
    d.insertDom(
      optID === null || optID === undefined ? d.getObj(initD.getAttribute('id')) : d.getObj(optID), 
      initD, 
      optPosition);
    
    var resB = be.hold(
      d.insertDomE(
        be.changes(triggerB),
        initD), 
      initD);
    
    //c.sendEvent(d.topE, initD); //initial call set by insertDom
    return resB;
  };
  annotate(d.insertDomB,['insertDomB'],0,[be.Behaviour.prototype],['insertDomB']);
  
  
  //TODO get crazy [topE?]
  //TODO change to:  String [ * [Behaviour] dom], defaulting to topE 
  d.extractId_b = function (id, start)
  {
    return be.hold(
      e.createNode(
        start === undefined? [d.topE] :
        start instanceof be.Behaviour? [be.changes(start)] :
        [],
        function (s, p) {
          p.value = d.getObj(id);
          s(p);
        }),
      d.getObj(id));
  };
  annotate(d.insertDomB,['extractId_b'],1,[be.Behaviour.prototype],['extractId_b']);
  
  
  var m_b; 
  d.mouse_b = function (domObj /* . events */) {
    
    var eventNames = l.slice(arguments, 1);
    if (arguments.length < 2) { eventNames = ['mousemove']; }
    
    if ((domObj === undefined) || (domObj === null)) { domObj = document; }
    if ((m_b !== undefined) && 
      (arguments.length < 2) && 
    (domObj == document)) { 
    return m_b; 
    } 
    
    var triggerE = (eventNames.length == 1)?
    d.extractEvent_e(domObj, eventNames[0]) :
    c.merge_e.apply(
      this,
      l.map(
        function (evt) {
          return d.extractEvent_e(domObj, evt);
        },
        eventNames));
    
    var res = be.hold(
      c.map_ev(
        function (e) {
          return (e.pageX || e.pageY) ?  
          {left: e.pageX, top: e.pageY} :
          (e.clientX || e.clientY) ?
          {left: e.clientX + document.body.scrollLeft,
          top: e.clientY + document.body.scrollTop} :
          {left: 0, top: 0};
        },
        triggerE), 
      {left: 0, top: 0});
    
    if (arguments.length < 2 && domObj == document) { m_b = res; }
    
    return res; 
  };
	annotate(d.mouse_b,['mouse_b']);
  
  d.mouseLeft_b = function (domObj /* .events */) {
    return be.lift_b(
      function (posn) {  return posn.left; },
      d.mouse_b.apply(this, arguments));
  };
	annotate(d.mouseLeft_b,['mouseLeft_b']);
  
  d.mouseTop_b = function (domObj /* .events */) {
    return be.lift_b(
      function (posn) { return posn.top; },
      d.mouse_b.apply(this, arguments));
  };
	annotate(d.mouseTop_b,['mouseTop_b']);
  
	//credit Matt White
	a.getURLParam = function (param) {
    var lparam = param.toLowerCase();
    var aReturn = [];
    var strHref = window.location.href;
    var endstr = (strHref.indexOf('#') > -1) ? strHref.indexOf('#') : strHref.length;
    if ( strHref.indexOf("?") > -1 ) {
      var strQueryString = strHref.substring(strHref.indexOf("?")+1,endstr);
      l.map(function(qp) {
          var eq = qp.indexOf('=');
          var qname = qp.substr(0,eq+1).toLowerCase();
          if(qname == lparam+"=") aReturn.push(decodeURIComponent(qp.substr(eq+1)));
      },strQueryString.split("&"));
    }
    if (aReturn.length == 0) return undefined;
    else if(aReturn.length == 1) return aReturn[0];
    else return aReturn;
	};
	annotate(a.getURLParam,['getURLParam','$URL']);
  
	//credit: everywhere on the net, Jim  Ley (Jibbering)
	//getHTTPObject: -> httpobj | false
	a.getHTTPObject = function () {
		var xmlhttp = false;
    /*@cc_on @*/
    /*@if (@_jscript_version >= 5)
    try {
    xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e) {
    try {
    xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    } catch (E) {
    xmlhttp = false;
    }
    }
    @end @*/
		if (!xmlhttp && typeof XMLHttpRequest!='undefined') {
			try {
				xmlhttp = new XMLHttpRequest();
			} catch (e) {
				xmlhttp=false;
			}
		}
		if (!xmlhttp && window.createRequest) {
			try {
				xmlhttp = window.createRequest();
			} catch (e) {
				xmlhttp=false;
			}
		}
		return xmlhttp;
	};
	annotate(a.getHTTPObject,['getHTTPObject']);
  
	//credit Quirksmode
	//readCookie: String -> String U Undefined
	a.readCookie = function (name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for (var i=0; i < ca.length; i++) {
      var co = ca[i];
      while (co.charAt(0) == ' ') { co = co.substring(1, co.length); }
      if (co.indexOf(nameEQ) === 0) { 
        return co.substring(nameEQ.length, co.length);
      }
    }
    return undefined;       
	};
	annotate(a.readCookie,['readCookie']);
  
  //TODO generic form that specifies the full onsteadystatechange function?
  a.rpc = function (url, postData, httpReceiver, async) {
    var http = a.getHTTPObject();
    http.open("POST", url, (async === undefined)? true : async);
    http.setRequestHeader(
      "Content-type", 
      "application/x-www-form-urlencoded");
    http.onreadystatechange = function ()
    {
      if (http.readyState == 4) {
        httpReceiver(http);
      }
    };
    http.send(postData);
  };
	annotate(a.rpc,['rpc','rpcPost']);
  
  a.rpcGet = function (url, httpReceiver, async) {
    var http = a.getHTTPObject();
    http.open("GET", url, (async === undefined)? true : async);
    http.onreadystatechange= function() {
      if (http.readyState == 4) {
        httpReceiver(http);
      }
    };
    http.send(null); // null so no request header content-type
  };
	annotate(a.rpc,['rpc','rpcGet']);
  
  //httpRPC: Node {url, postData} [*  a -> b] -> Node b
  a.httpRPC_e = function (node, approx) {
    var rpcE = e.createNode(
      [node],
      function (s, p) {
        a.rpc(
          p.value.url,
          p.value.postData,
          function (http) {
          s(new b.Pulse(p.stamp, http.responseText)); });
      });
    
    return (approx instanceof Function) ?
    c.merge_e(
      c.map_ev(approx, node),
      rpcE) :
    rpcE;
  };
	annotate(a.httpRPC_e,['httpRPC_e'],1,[e.Event.prototype],['httpRPC_e']);
  
  //========== dynamic scripts ==========
  a.scriptCounter = 0;
  a.deleteScript = function (scriptID) {
    var scriptD = d.getObj(scriptID);
    scriptD.parentNode.removeChild(scriptD); //TODO isolate child and set innerHTML to "" to avoid psuedo-leaks?
  };
  
  // optional fn/param that gets polled until parm is defined
  a.runScript = function (url, fn, param) {
    var script = document.createElement("script");
    script.src = url;
    var scriptID = 'scriptFnRPC' + a.scriptCounter++;
    script.setAttribute('id', scriptID);
    document.getElementsByTagName("head").item(0).appendChild(script);
    var timer = {};
    var check = 
    function () {
      eval("try { if (" + param + "!== undefined) {var stat = " + param + ";}} catch (e) {}");
      if (stat !== undefined) {
        eval(param + " = undefined;");
        clearInterval(timer.timer);
        clearInterval(timer.timeout);
        if (fn instanceof Function) { fn(stat); }
        a.deleteScript(scriptID);
      }
    };
    timer.timer = setInterval(check, 3500);
    timer.timeout = 
    setTimeout( 
      function () { 
        try { clearInterval(timer.timer); }
        catch (e) {}
      },
      5000); //TODO make parameter?
  };
  
  //evalForeignScriptVal_e: Node {url, globalArg} -> Node a
  //load script @ url and poll until param is set, then pass it along
  a.evalForeignScriptVal_e = function (node) {
    return e.createNode(
      [node],
      function (s, p) {
        a.runScript(
          p.value.url,
          function (globalArg) {
            s(new b.Pulse(p.stamp, globalArg));
          },
          p.value.globalArg);
      });
  };
	annotate(a.evalForeignScriptVal_e,['evalForeignScriptVal_e'],0,[e.Event.prototype],['evalForeignScriptVal_e']);
  
  //evalForeignScriptFn_e: Node {String before, String after} -> Node a
  //load script with gap between before/after for the potential handler name
  a.evalForeignScriptFn_e = function (node) {
    return e.createNode(
      [node],
      function (s, p) {
        var fnName = 'scriptFnRPC' + a.scriptCounter++;
        eval(fnName + "= function (res){"+
             "s(new b.Pulse(p.stamp, res));"+
             "setTimeout(function(){a.deleteScript(\"" + fnName + 
             "\")},1000);}");
        var script = document.createElement("script");
        script.src = p.value.before + fnName + p.value.after;
        var scriptID = fnName;
        script.setAttribute('id', scriptID);
        document.getElementsByTagName("head").item(0).appendChild(script);
      });
  };
  annotate(a.evalForeignScriptFn_e,['evalForeignScriptFn_e'],0,[e.Event.prototype],['evalForeignScriptFn_e']);

  //============= JSONRPC variant ========/
  
  ///////// OPTIONALLY EXPORT PUBLIC FUNCTIONS TO GLOBAL NAMESPACE
  if (makeTopLevel !== false) {
    for (var zz in flapjax.pub) {
      window[zz] = flapjax.pub[zz]; // use eval instead so as to achieve Flash compatibility
    }
  }
  return flapjax.pub;
}
