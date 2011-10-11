// Copyright 2011 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/*

CapServer
  See: http://goo.gl/hBgTu

Globals used:
  JSON.stringify
  JSON.parse
  jQuery.ajax

*/

if (!('freeze' in Object)) {
  Object.freeze = function(x) { return x; };
}

var CAP_EXPORTS = (function() {

  // == UTILITIES ==

  var newUUIDv4 = function() {
    var r = function() { return Math.floor(Math.random() * 0x10000); };
    var s = function(x) { return ('000' + x.toString(16)).slice(-4); };
    var u = function() { return s(r()); };
    var v = function() { return s(r() & 0x0fff | 0x4000); };
    var w = function() { return s(r() & 0x3fff | 0x8000); };
    return u() + u() + '-' + u() + '-' + v() +
           '-' + w() + '-' + u() + u() + u();
  };

  var newCapID = newUUIDv4;
  var encodeSerialization = function(instID, capID) {
    return 'urn:x-cap:' + instID + ':' + capID;
  };
  var decodeSerialization = function(ser) {
    var m = ser.match(/^urn:x-cap:([-0-9a-f]{36}):([-0-9a-f]{36})$/);
    if (m) {
      m.shift();
    }
    return m;
  };
  var decodeInstID = function(ser) {
    var m = decodeSerialization(ser);
    return m ? m[0] : nullInstID;
  };
  var decodeCapID = function(ser) {
    var m = decodeSerialization(ser);
    return m ? m[1] : nullCapID;
  };

  var nullInstID = '00000000-0000-0000-0000-000000000000';
  var nullCapID = '00000000-0000-0000-0000-000000000000';
  var nullSer = encodeSerialization(nullInstID, nullCapID);


  var isURL = function(str) {
     return /^https?:/.test(str);
  }

  var makeAsyncAJAX = function(url, method, data, success, failure) {
     var xhr = new XMLHttpRequest();
     xhr.open(method, url);
     xhr.onreadystatechange = function() {
       if (xhr.readyState === 4) {
         if (xhr.status >= 200 && xhr.status < 300) {
           success(xhr.responseText);
         }
         else {
           failure({ status: xhr.status, message: xhr.statusText });
         }
       }
     };
     xhr.send(data);
   };

  // == IMPLEMENTATIONS ==

  var badRequest = Object.freeze(
      {status: 400, message: 'bad request'});
  var notFound = Object.freeze(
      {status: 404, message: 'not found'});
  var methodNotAllowed = Object.freeze(
      {status: 405, message: 'method not allowed'});
  var internalServerError = Object.freeze(
      {status: 500, message: 'internal server error'});

  var deadImpl = Object.freeze({
    invoke: function(method, d, sk, fk) {
      fk(notFound);
    }
  });

  var ImplHandler = function(server, handler) {
      this.server = server;
      this.handler = handler;
  };
  ImplHandler.prototype.invoke = function(method, data, sk, fk) {
    if (method == 'GET' || method == 'DELETE') {
      if (data !== undefined) {
        fk(badRequest);
        return;
      }
    }
    else {
      data = this.server.dataPostProcess(data);
    }

    var skk;
    if (method == 'PUT' || method == 'DELETE') {
      skk = function(result) {
        if (result === undefined) sk();
        else fk(internalServerError);
      }
    }
    else if (method == 'GET' || method == 'POST') {
      var server = this.server;
      skk = function(result) {
        sk(server.dataPreProcess(result));
      }
    }

    try {
      var h = this.handler;
      if (method == 'GET' && h.get) h.get(skk, fk);
      else if (method == 'PUT' && h.put) h.put(data, skk, fk);
      else if (method == 'POST' && h.post) h.post(data, skk, fk);
      else if (method == 'DELETE' && h.remove) h.remove(skk, fk);
      else fk(methodNotAllowed);
    }
    catch (e) {
      fk(internalServerError);
    }
  };

  var ImplURL = function(url) { this.url = url; };
  ImplURL.prototype.invoke = function(m, d, s, f) {
     makeAsyncAJAX(this.url, m, d, s, f);
  };

  var ImplWrap = function(server, innerCap) {
    this.server = server;
    this.inner = innerCap; };
  ImplWrap.prototype.invoke = function(m, d, s, f) {
    var me = this;
    var wrappedS = function(result) {
      return s(me.server.dataPreProcess(result));
    };
    this.inner.invoke(m, this.server.dataPostProcess(d), wrappedS, f);
  };







  var Capability = function(ser, server) {
    this.ser = ser;
    this.server = server;
  };
  Capability.prototype.invoke = function(method, data, success, failure) {
    var me = this;
    if (method == 'PUT' || method == 'POST') {
      data = this.server.dataPreProcess(data);
    }
    else {
      if (data !== undefined) {
        throw ('Capability.invoke ' + method +
               ' called with request data' + data);
      }
    }
    var wrappedSuccess = function(result) {
      if (success) {
        if (method == 'GET' || method == 'POST') {
          result = me.server.dataPostProcess(result);
        }
        else {
          result = undefined;
        }
        return success(result);
      }
      return undefined;
    };
    this.server.privateInterface.invoke(this.ser, method, data,
                                        wrappedSuccess, failure);
  };
  Capability.prototype.get = function(success, failure) {
    this.invoke('GET', undefined, success, failure);
  };
  Capability.prototype.put = function(data, success, failure) {
    this.invoke('PUT', data, success, failure);
  };
  Capability.prototype.post = function(data, success, failure) {
    this.invoke('POST', data, success, failure);
  };
  Capability.prototype.remove = function(success, failure) {
    this.invoke('DELETE', undefined, success, failure);
  };
  Capability.prototype.serialize = function() {
    return this.ser;
  };

  Object.freeze(Capability.prototype);
  Object.freeze(Capability);



  var CapServer = function(instanceID, snapshot) {
    this.reviveMap = {};  // map capID -> key or cap or url
    this.implMap = {};    // map capID -> impls
    this.reviver = null;
    this.sync = null;
    if (typeof instanceID === 'string') {
      this.instanceID = instanceID;
    }
    this.resolver = function(id) { return null; };
    if (snapshot) {
      snapshot = JSON.parse(snapshot);
      this.reviveMap = snapshot.map;
    }

    this.publicInterface = (function(me) {
      return Object.freeze({
        invoke: function(ser, method, data, success, failure) {
          me._getImpl(ser).invoke(method, data, success, failure);
        }
      });
    })(this);

    this.privateInterface = (function(me) {
      return Object.freeze({
        invoke: function(ser, method, data, success, failure) {
          if (isURL(ser)) {
            return makeAsyncAJAX(ser, method, data, success, failure);
          }

          var instID = decodeInstID(ser);
          if (instID == me.instanceID) {
            me._getImpl(ser).invoke(method, data, success, failure);
            return;
          } else {
            var publicInterface = me.resolver(instID);
            if (publicInterface) {
              publicInterface.invoke(ser, method, data, success, failure);
              return;
            }
          }

          return deadImpl.invoke(method, data, success, failure);
        }
      });
    })(this);
  };

  CapServer.prototype._sync = function() {
    if (this.sync) this.sync(this.snapshot());
  };

  CapServer.prototype._mint = function(capID) {
    if (!this.hasOwnProperty('instanceID')) {
      throw 'CapServer: no instanceID in mint()';
    }
    var ser = encodeSerialization(this.instanceID, capID);
    var cap = Object.freeze(new Capability(ser, this));
    return cap;
  };

  CapServer.prototype._getImpl = function(ser) {
    var capID = decodeCapID(ser);
    if (! (capID in this.implMap)) {
      var info = this.reviveMap[capID];
      if (info) {
        if (info.restoreKey) {
          if (this.reviver) {
            this.implMap[capID] = this.reviver(info.restoreKey);
          }
        }
        else if (info.restoreCap) {
          var innerCap = this.restore(info.restoreCap);
          this.implMap[capID] = new ImplWrap(this, innerCap);
        }
      }
    }
    return this.implMap[capID] || deadImpl;
  };

  CapServer.prototype._grant = function(impl, key) {
    var capID = newCapID();

    if (impl === null) { impl = deadImpl; }
    this.implMap[capID] = impl;
    if (key) { this.reviveMap[capID] = { restoreKey: key }; }
    this._sync();
    // TODO(mzero): should save URL and cap items in reviveMap

    return this._mint(capID);
  };

  CapServer.prototype.grant = function(item, key) {
    return this._grant(this.build(item), key);
  };

  CapServer.prototype.grantKey = function(key) {
    return this._grant(this.reviver(key), key);
  };

  // TODO(jpolitz): get rid of wrap?  get rid of resolvable?
  CapServer.prototype.wrap = function(innerCap, resolvable) {
    var capID = newCapID();

    this.implMap[capID] = new ImplWrap(this, innerCap);
    this.reviveMap[capID] = { restoreCap: innerCap.serialize() };

    return this._mint(capID);
  };

  CapServer.prototype.build = function(item) {
    var t = typeof item;

    var checkFnArgs = function(fn, params) {
      if (typeof fn === 'function' && typeof fn.length === 'number') {
        return fn.length >= params ? 'async' : 'sync';
      }
      return false;
    }

    var consistentHandler = function(obj) {
      var a = [checkFnArgs(obj.get, 1),
                checkFnArgs(obj.put, 2),
                checkFnArgs(obj.post, 2),
                checkFnArgs(obj.remove, 1)];

      var foundHandler = false;
      var handlerType = false;
      for (var i = 0; i < a.length; i++) {
        if (!foundHandler && a[i]) {
          foundHandler = true;
          handlerType = a[i];
        }
        else if (handlerType && a[i] && handlerType !== a[i]) {
          throw 'Inconsistent handlers';
        }
      }
      return foundHandler ? handlerType : false;
    }

    if (item === null) return deadImpl;
    else if (t === 'string' && isURL(item)) return this.buildURL(item);
    else if (t === 'function') {
      switch (checkFnArgs(item, 2)) {
        case 'sync': return this.buildSyncFunction(item);
        case 'async': return this.buildAsyncFunction(item);
        default: throw 'Invalid length on function';
      }
    }
    else if (t === 'object') {
      if (Object.getPrototypeOf(item) === Capability.prototype) {
        return new ImplWrap(this, item);
      }
      if (typeof item.invoke === 'function' &&
          item.invoke.length === 4) {
        return item;
      }
      switch (consistentHandler(item)) {
        case 'sync': return this.buildSyncHandler(item);
        case 'async': return this.buildAsyncHandler(item);
        default: throw 'build() given an object with no handlers';
      }
    }
    else return deadImpl;
  }

  CapServer.prototype.buildAsyncHandler = function(h) {
    return new ImplHandler(this, h);
  };

  CapServer.prototype.buildSyncHandler = function(h) {
    ah = {};
    if (h.get) ah.get = function(sk, fk)    { sk(h.get()); };
    if (h.put) ah.put = function(d, sk, fk) { sk(h.put(d)); };
    if (h.post) ah.post = function(d, sk, fk) { sk(h.post(d)); };
    if (h.remove) ah.remove = function(sk, fk)    { sk(h.remove()); };
    return new ImplHandler(this, ah);
  };

  CapServer.prototype.buildSyncFunction = function(f) {
    return new ImplHandler(this, {
      get: function(sk, fk)    { sk(f()); },
      put: function(d, sk, fk) { sk(f(d)); },
      post: function(d, sk, fk) { sk(f(d)); }
    });
  };

  CapServer.prototype.buildAsyncFunction = function(f) {
    return new ImplHandler(this, {
      get: function(sk, fk)    { f(undefined, sk, fk); },
      put: function(d, sk, fk) { f(d, sk, fk); },
      post: function(d, sk, fk) { f(d, sk, fk); }
    });
  };

  CapServer.prototype.buildURL = function(url) {
    if (typeof url !== 'string') { return deadImpl; }
    return new ImplURL(url);
  };




  CapServer.prototype.revoke = function(ser) {
    var capID = decodeCapID(ser);
    delete this.reviveMap[capID];
    delete this.implMap[capID];
    this._sync();
  };

  CapServer.prototype.revokeAll = function() {
    this.reviveMap = {};
    this.implMap = {};
    this._sync();
  };

  CapServer.prototype.restore = function(ser) {
    return Object.freeze(new Capability(ser, this));
  };

  CapServer.prototype.setReviver = function(r) { this.reviver = r; };

  CapServer.prototype.snapshot = function() {
    var snapshot = {
      id: this.instanceID,
      map: this.reviveMap
    };
    return JSON.stringify(snapshot);
  };

  CapServer.prototype.setResolver = function(resolver) {
    this.resolver = resolver;
  };

  CapServer.prototype.setSyncNotifier = function(sync) {
    this.sync = sync;
  };

  CapServer.prototype.dataPreProcess = function(w) {
    if (w === undefined) return w;
    return JSON.stringify({ value: w }, function(k, v) {
      if (typeof(v) == 'function') {
        throw new TypeError('Passing a function');
      }
      try {
        if (Object.getPrototypeOf(v) === Capability.prototype) {
          return { '@': v.serialize() };
        }
      } catch (e) { }
      return v;
    });
  };

  CapServer.prototype.dataPostProcess = function(w) {
    if (w === undefined || w.trim() === '') return undefined;
    var me = this;
    return JSON.parse(w, function(k, v) {
      try {
        var k = Object.keys(v);
        if (k.length == 1 && k[0] == '@') {
          return me.restore(v['@']);
        }
      }
      catch (e) { }
      return v;
    }).value;
  };

  Object.freeze(CapServer.prototype);
  Object.freeze(CapServer);

  function now() {
    return (new Date()).valueOf();
  }

  var CapTunnel = function(port) {
    var me = this;

    this.localResolver = function(instID) { return null; };
    this.remoteResolverProxy = function(instID) { return me.sendInterface; };
    this.transactions = {};
    this.txCounter = 1000;
    this.outpost = undefined;

    this.sendInterface = Object.freeze({
      invoke: function(ser, m, d, s, f) { me.sendInvoke(ser, m, d, s, f); }
    });

    var lastRecvTime = now();
    var lastSendTime = 0;

    this.postMessage = function(msg) {
      lastSendTime = now();
      port.postMessage(msg);
    }

    var lastRecvTime = now();

    port.onmessage = function(event) {
      lastRecvTime = now();
      var message = event.data;
      if (message.op == 'invoke') { me.handleInvoke(message); }
      else if (message.op == 'response') { me.handleResponse(message); }
      else if (message.op == 'outpost') { me.handleOutpost(message); }
      else if (message.op === 'ping') {
        me.postMessage('pong');
      }
      else if (message.op === 'pong') {
        // lastRecvTime is always updated; nothing to do
      }
    };

    var pingTimerID;
    // ensure SEND_INTERVAL < RECV_INTERVAL
    var SEND_INTERVAL = 1000; // send every 2s, ping if needed
    var RECV_INTERVAL = 2000; // ensure we recv every 5s

    var sendPingCheckRecv = function(_) {
      var t = now();
      if (lastRecvTime + RECV_INTERVAL < t) {
        clearInterval(pingTimerID);
        if (me.onclosed) { me.onclosed(); }
      }
      else if (lastSendTime + SEND_INTERVAL < t) {
        me.postMessage({ op: 'ping' });
      }
    };

//  TODO(joe): Why the F is this here?
//    pingTimerID = setInterval(sendPingCheckRecv, SEND_INTERVAL);
  };

  CapTunnel.prototype.sendOutpost = function(outpostData) {
    var message = {
      op: 'outpost',
      outpostData: outpostData
    };
    this.postMessage(message);
  };

  CapTunnel.prototype.handleOutpost = function(message) {
    this._outpostMessage = message;
    if (this.hasOwnProperty('_outpostHandler')) {
      this._outpostHandler(message.outpostData);
    }
  };

  CapTunnel.prototype.setOutpostHandler = function(callback) {
    this._outpostHandler = callback;
    if (this.hasOwnProperty('_outpostMessage')) {
      this._outpostHandler(this._outpostMessage.outpostData);
    }
  };

  CapTunnel.prototype.sendInvoke = function(ser, method, data, success, failure)
  {
    var txID = this.txCounter++;
    this.transactions[txID] = { success: success, failure: failure };
    var msg = {
      op: 'invoke',
      txID: txID,
      ser: ser,
      method: method,
      data: this.toWire(data)
    };
    this.postMessage(msg);
    // TODO(mzero): something with a timeout
  };

  CapTunnel.prototype.handleInvoke = function(message) {
    var iface = this.localResolver(decodeInstID(message.ser));
    if (iface) {
      var me = this;
      iface.invoke(message.ser, message.method, this.fromWire(message.data),
          function(data) { me.sendResponse(message.txID, 'success', data); },
          function(err) { me.sendResponse(message.txID, 'failure', err); });
    } else {
      this.sendResponse(message.txID, 'failure', { status: 404 });
    }
  };

  CapTunnel.prototype.sendResponse = function(txID, type, data) {
    var msg = {
      op: 'response',
      txID: txID,
      type: type,
      data: this.toWire(data)
    };
    this.postMessage(msg);
  };

  CapTunnel.prototype.handleResponse = function(message) {
    var tx = this.transactions[message.txID];
    if (tx) {
      delete this.transactions[message.txID];
      if (message.type == 'success') {
        if (tx.success) { tx.success(this.fromWire(message.data)); }
      }
      if (message.type == 'failure') {
        if (tx.failure) { tx.failure(this.fromWire(message.data)); }
      }
    }
  };

  CapTunnel.prototype.toWire = function(data) { return data; };
  CapTunnel.prototype.fromWire = function(data) { return data; };

  CapTunnel.prototype.setLocalResolver = function(resolver) {
    this.localResolver = resolver;
  };

  Object.freeze(CapTunnel.prototype);
  Object.freeze(CapTunnel);

  return {
    CapServer: CapServer,
    CapTunnel: CapTunnel,
    newUUIDv4: newUUIDv4
  };
})();

var CapServer = CAP_EXPORTS.CapServer;
var CapTunnel = CAP_EXPORTS.CapTunnel;
var newUUIDv4 = CAP_EXPORTS.newUUIDv4;

