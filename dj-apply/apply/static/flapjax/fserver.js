/*
Copyright (c) 2006, the Flapjax Team All rights reserved.

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

function initFlapjaxServerAPIs (flapjax, baseUrl, logB, makeTopLevel) {
    
    makeTopLevel = (makeTopLevel === undefined) ? true : makeTopLevel;
    baseUrl = baseUrl ? baseUrl : 'http://www.flapjax-lang.org/flapjax/servlets/';

    if (logB === undefined) { logB = {push: function (){}}; }

    var version = 3;
    if (flapjax.util.version != version) { 
        throw 'fserver.js (v' + version + ') out of sync with flapjax.js (v' + flapjax.util.version + ')';
    }

    var thisPageUrl = window.location.href;
    var appDivider = 'apps';
    var appName = thisPageUrl.substr(1 + appDivider.length + thisPageUrl.indexOf(appDivider));
    appName = appName.substr(0, appName.indexOf("/"));
    
    //$___sa: Array ( Annotation * String * Object)
    //Annotation: Object (
    //  [np: Boolean] - not public - do not add function to flapjax.pub, default false
    //  [b: Boolean] - behaviour - add function to behaviour prototype, default false
    //  [e: Boolean] - event - add function to event prototype, default false
    //  [a: Number] - argument - parameter position to replace with object when used in prototype, default: don't do it
    //)
    var $___sa = [];
    var $$___sa = function (a, n, fn) { $___sa.push(arguments); };
    
    $$___sa({}, '$___sdefs', $___sa);

    //CONSTANTS PRE
    var defaultUrl = baseUrl ? baseUrl : false;
    var defaultAsync = true;
    var defaultPoll = 0;
    var defaultProtocol;
    var defaultPermission = false;
    var defaultDeepRead = true;
    var maxLTS = 1000000;

    var urls = [];
    var $___pushUrl = function (url) { urls.push(url); defaultUrl = url; };
    $$___sa({}, 'pushUrl', $___pushUrl);
    
    var $___popUrl = function () { urls.pop(); defaultUrl = urls[urls.length - 1]; };
    $$___sa({}, 'popUrl', $___popUrl);
    
    $___pushUrl(defaultUrl);
    
    var $___getUrl = function () { return defaultUrl; };
    $$___sa({}, 'getUrl', $___getUrl);

    var fserver = {
        browser: undefined,
        marshall: undefined,
        server: undefined,
        client: undefined
    };
    
    flapjax.util.fserver = fserver;
    
    fserver.browser = {

        getSharingConsoleLink: function (app, user, object, path, subject, message, url) {
            if ((url === undefined) || (url === null)) {
                url = defaultUrl;
            }
           
            url += '/sharingConsole?';
          
            if (app !== undefined) { url += '&app=' + escape(app);}
            if (user !== undefined) { url += '&user=' + escape(user); }
            if (object !== undefined) { url += '&object=' + escape(object); }
            if (path !== undefined) { url += '&path=' + fserver.browser.toUrlStr(path); }
            if (subject !== undefined) { url += '&subject=' + escape(subject); }
            if (message !== undefined) { url += '&message=' + escape(message); }

            return url;
        },

    //ignore object case, and fix arrays only one layer deep
        toUrlStr: function (o) {
            return (typeof(o) == 'string')? escape(o) : 
                o instanceof Array? '[' + flapjax.util.lib.map(escape, o) + ']' :
                o;
        }
    };
    $$___sa({}, "getSharingConsoleLink", fserver.browser.getSharingConsoleLink);

    var $___loginChangeE = flapjax.util.combinators.createEventReceiver();
    var $___loginB = 
        new flapjax.util.behaviours.Behaviour(
            flapjax.util.combinators.map_ev(
                function (_) {
                    return flapjax.util.ajax.readCookie('uid');
                },
                $___loginChangeE),
            flapjax.util.ajax.readCookie('uid'));   
    $$___sa({}, 'uidB',  $___loginB);

    fserver.marshall = {
        handler: function (exnE, handler, val) { 
            var response = val.parseJSON(); 
            // TODO use exception stream 
            // TODO why doesn't the exception propagate?  remove the alert when debugged...
            if (response.error !== undefined) { 
                flapjax.util.combinators.sendEvent(exnE, response.error); 
            } else {
                var result = response.result;
                return handler(result);
            }
        },
        
        untieDeepRead: function (root, objects, cache) {
            cache = (cache === undefined) ? [] : cache;

            // if we have a flat value at the true root level, so return that
            if ((root.ref === undefined) && (root.oid === undefined)) { return root.val; }
            
            // since it doesn't have val, it must have a ref
            var ref = root.ref ? root.ref : root.oid;
            //logB.push('ref: ' + ref);
            if (cache[ref] !== undefined) { return cache[ref]; }
            var rootObj = objects[ref]; //in case item passed in was root instead of in objects

            // build the base object, which we'll fill in the recursion
            var obj = rootObj.isArray ? [] : {};
            cache[ref] = obj; // cache

            // set each subfield...
            var fields = rootObj.fields;
            for (var field in fields) {
                // ...by a recursive call
                if (Object.prototype[field] !== undefined) { continue; } /* play safe */
                //logB.push('field: ' + field);
                obj[field] = 
                    typeof(fields[field]) == 'string' ? 
                        fserver.marshall.untieDeepRead(objects[fields[field]], objects, cache) :
                    fields[field].ref ?
                        fserver.marshall.untieDeepRead(objects[fields[field].ref], objects, cache) :
                    fields[field].val;
                //logB.push('pushed: ' + obj[field]);
            }

            return obj;
        },

        tieDeepWrite: function (root, objects, cache, count) {
            cache = (cache === undefined) ? new flapjax.util.xlib.Hashtable () : cache;
            count = (count === undefined) ? {v: 0} : count;

            var assoc = cache.get(root);
            if (assoc !== undefined) { return { ref: assoc }; }

            switch (typeof(root)) {
                case 'function':
                    // ignore silently
                    return;
                case 'object':
                    var entry;
                    
                    if (root instanceof Array) {
                        entry = [];
                        for (var i = 0;i < root.length;i++) {
                            if (typeof(root[i]) == 'function') { continue; }
                            
        
                            entry.push(fserver.marshall.tieDeepWrite(root[i], objects, cache, count));
                        }
                    } else {
                        entry = {};
                        for (var field in root) {
                            if (typeof(root[field]) == 'function') { continue; }
                            if (Object.prototype[field] !== undefined) { continue; } /* play safe */
                            entry[field] = fserver.marshall.tieDeepWrite(root[field], objects, cache, count);
                        }
                    }

                    var id = count.v++;
                    cache.set(root, id);
                    objects[id] = entry;

                    return { ref: id };
                default:
                    return { val: root };
            }
        }
    };

    fserver.server = {
        // TODO update these docs -- they're way out of date
        /* CLIENT->SERVER API: URL * (HTTP ->) . Array String -> */
        /* adds version parameter to every request [last parameter if by position ]*/
        /* basicPost, basicGet, basicJson (POST) versions */

            //register: String U Undefined * (String -> ) * username:String * password:String ->
            //   User <username> created.
            //   failed to create user: could not add user because "<username>" is already taken

            //login: String U Undefined * (String -> ) * username:String * password:String ->
            //  User <username> logged in.
            //  identification failure (unknown username/password combination)

            //check: String U Undefined * (String -> ) ->
            //  Currently logged in as <username>
            //  Not currently logged in.

            //extend: String U Undefined * (String -> ) ->
            //  Session extended for leo.
            //  Not currently logged in.
            
            //logout: String U Undefined * (String -> ) ->
            //  Logged out <username>
            //  Not currently logged in.

            
            //listFields: String U Undefined * (Array String -> ) * object:ObjectName ->
/*
object <validObj> contains: 
( )
*/
/*
visible fields in <validObj>:
( <fieldName> )
*/
/*
visible fields in <validObj>:
( <fieldName> <fieldName> )
*/
/*
object <invalidObj> contains: 
( )
*/

            //setField: String U Undefined * (String -> ) 
            //      * object:ObjectName * field:FieldName * (val:String U ref:Ref)  ->

            //getField: String U Undefined * (String -> ) 
            //      * object:ObjectName * field:FieldName * (Response ({VAL: Val} U {REF: Ref}) ->) ->

            //newObject: String U Undefined * (String -> ) * 
            //      * parent:ObjectName * field:FieldName
            //  <objName>['<fieldName>'] = REF: <Ref>
            //  newObject failed: field <fieldName> already exists in object <validObj>
            //  newObject failed: <userName> cannot add to <invalidObj> (no such object or no permission)


        basicPost: { /* ... */ },
        basicGet: { /* ... */ },
        basicJson: { /* ... */ }

    };
    var server = fserver.server;

    fserver.pub = {
        
        fserver: fserver
        
    };

    var $___rpcSchemas  = /* TODO rpc returns still in flux, really should be new third arg here */
        [
        /*       method         args */
            ['login',       ['username', 'password'], ['uid', 'home']],
            ['check',       [], ['uid']],
            ['logout',      [], []],

            /* old, simple API for gets and sets */
            ['getMyHome',   [], ['object']],
//          ['listFields',  ['object']],
//          ['setField',    ['object', 'field', ['val', 'ref']]], 
//          ['getField',    ['object', 'field'], []], /* ref&isArray or val */
//          ['newObject',   ['parent', 'field', 'isArray'], ['oid']],
//          ['deleteField', ['object', 'field']],

            /* new API, with fancier args */
            /*listFields*/ ['inspect',     ['user', 'object', 'path']],
            /*getField*/   ['read',        ['user', 'object', 'path']],
                           ['deepRead',    ['user', 'object', 'path']],
            /*setField*/   ['write',       ['user', 'object', 'path', 'lts', ['val', 'ref']]],
                           ['deepWrite',   ['user', 'object', 'path', 'lts', 'content']],
            /*newObject*/  ['create',      ['user', 'object', 'path', 'isArray']],
            /*deleteField*/['remove',      ['user', 'object', 'path']],     
    
            /*untested */ 
            ['sendAuthEmail',   ['emailAddr', 'subject', 'message', 'params', 'durationSecs'], ['uid']],
            ['verifyEmail',     ['key', 'restrictIP', 'timeoutSecs', 'durationSecs']],
            ['pickUsernameAndPassword', ['username', 'password'], ['status']],

            /*access control */
            ['getDomain',      ['object'], ['creator', 'creatorUsername', 'name', 'amAdmin']],
            ['migrate',        ['object', 'creator', 'name']],
            ['getPermissions', ['user', 'object', 'path']]
            //['sharingConsole', ['app', 'user', 'object', 'path']]
        ];
    $$___sa({}, 'rpcSchemas', $___rpcSchemas);

    //=============MAKER HELPERS
    var wrapHandler = function (obj, fnName, middleHandler) {
        obj[fnName] =       
            (function () {
                var prevFn = obj[fnName];
                return function (url, userHandler, async, exnE /* . args */) {
                    prevFn.apply(this,
                        [url,
                         function (middleV) {
                            return userHandler(middleHandler(middleV));
                         },
                         async, exnE].concat(flapjax.util.xlib.slice(arguments, 3)));
                };
            })();
    };
    
    var checkLogin = function (v) {     
        flapjax.util.combinators.sendEvent($___loginChangeE, v);
        return v;
    };


    //=============POST
    //basicPostRpcMaker: String * Array (String a U Array String b)
    //      -> (String U Null U undefined) * Boolean * (String ->) * (. Array ((a: String) U (k: b, v: String)) -> 
    var basicPostRpcMaker = function (serviceName, params) {
        var objectPos;
        for (var i = 0; i < params.length; i++) {
            if (params[i] == 'object') { 
                objectPos = i;
                i = params.length;
            }
        }
    
        return function (url, handler, async, exnE /* . args */) {
            var args = flapjax.util.xlib.slice(arguments, 4);
            flapjax.rpcPost(
                (url ? url : defaultUrl ) + '/' + serviceName,
                flapjax.fold(
                    function (curr, param, acc) {
                        if ( param == 'path' ) { 
                             var hasObject =
                                ((objectPos !== undefined) && 
                                 (args.length > objectPos) &&
                                 (args[objectPos] !== undefined));
                            if (!hasObject) {
                                var len = curr.length;
                                if ( (len === 0) || (len > 0 && curr[0] != ".")) {
                                    curr = [appName].concat(curr);
                                } else {
                                    curr = flapjax.util.xlib.slice(curr, 1);
                                }
                            }                        
                        }
                        if ( typeof(param) == 'string' ) {
                            return acc + '&' + param + '=' + curr;
                        } else if (curr === undefined) {
                        } else {
                            if (typeof(curr) == 'object' && !flapjax.member(curr.k, param) ) { throw serviceName + ': unknown parameter option "' + curr.k + '"'; } //SAFETY
                            return acc +'&' + curr.k + '=' + curr.v;    
                        }
                    },
                    '&id=0&version=' + flapjax.util.version,
                    args, params),
                function (http) { return fserver.marshall.handler(exnE, handler, http.responseText); },
                async  === undefined? defaultAsync : async);
        };

    };
    
    flapjax.util.lib.forEach(
        function (tuple) {
            server.basicPost[tuple[0]] = basicPostRpcMaker.apply(this, tuple);          
        },
        $___rpcSchemas);
    
    wrapHandler(server.basicPost, 'login', checkLogin);
    wrapHandler(server.basicPost, 'extend', checkLogin);
    wrapHandler(server.basicPost, 'check', checkLogin);
    
    //=============GET
    
   
    //basicGetRpcMaker: String * Array (String a U Array String b)
    //      -> (String U Null U undefined) * Boolean * (String ->) * (. Array ((a: String) U (k: b, v: String)) -> 
    var basicGetRpcMaker = function (serviceName, params) {
        var objectPos;
        for (var i = 0; i < params.length; i++) {
            if (params[i] == 'object') { 
                objectPos = i;
                i = params.length;
            }
        }
        return function (url, handler, async, exnE /* . args */) {
            var args = flapjax.util.xlib.slice(arguments, 4);
            flapjax.rpcGet(             
                flapjax.fold(
                    function (curr, param, acc) {
                        if ( param == 'path' ) { 
                            var hasObject =
                                ((objectPos !== undefined) && 
                                 (args.length > objectPos) &&
                                 (args[objectPos] !== undefined));
                            if (!hasObject) {
                                var len = curr.length;
                                if ( (len === 0) || (len > 0 && curr[0] != ".")) {
                                    curr = [appName].concat(curr);
                                } else {
                                    curr = flapjax.util.xlib.slice(curr, 1);
                                }
                            }                       
                        }
                        if ( typeof(param) == 'string' ) {
                            return acc + 
                            '&' + escape(param) + '=' + fserver.browser.toUrlStr(curr);
                        } else if (curr === undefined) {
                        } else {
                            if (typeof(curr) == 'object' && !flapjax.member(curr.k, param) ) { throw serviceName + ': unknown parameter option "' + curr.k + '"'; } //SAFETY
                            return acc + '&' + escape(curr.k) + '=' + fserver.browser.toUrlStr(curr.v); 
                        }
                    },
                    (url ? url : defaultUrl ) + '/' + serviceName + '?id=3&version=' + flapjax.util.version,
                    args, params),
                function (http) { return fserver.marshall.handler(exnE, handler, http.responseText); },
                async  === undefined? defaultAsync : async);
        };
    };
            
    flapjax.util.lib.forEach(
        function (tuple) {
            server.basicGet[tuple[0]] = basicGetRpcMaker.apply(this, tuple);            
            wrapHandler(
                server.basicGet, 
                tuple[0],
                fserver.marshall.returnHandler);
        },
        $___rpcSchemas);
        
    wrapHandler(server.basicGet, 'login', checkLogin);
    wrapHandler(server.basicGet, 'extend', checkLogin);
    wrapHandler(server.basicGet, 'check', checkLogin);

    //=============JSON
    //basicJsonRpcMaker: String * Array (String a U Array String b)
    //      -> (String U Null U undefined) * Boolean * (String ->) * (. Array ((a: String) U (k: b, v: String)) -> 
    var basicJsonRpcMaker = function (serviceName, params) {
        var objectPos;
        for (var i = 0; i < params.length; i++) {
            if (params[i] == 'object') { 
                objectPos = i;
                i = params.length;
            }
        }

        return function (url, handler, async, exnE /* . args */) {
            var args = flapjax.util.xlib.slice(arguments, 4);
            flapjax.rpcPost(
                (url ? url : defaultUrl ) + '/jsonrpc',
                {method: serviceName,
                 params:
                     [flapjax.fold(
                        function (curr, param, acc) {
                            if ( param == 'path' ) { 
                                var hasObject =
                                    ((objectPos !== undefined) && 
                                    (args.length > objectPos) &&
                                    (args[objectPos] !== undefined));
                                if (!hasObject) {
                                    var len = curr.length;
                                    if ( (len === 0) || (len > 0 && curr[0] != ".")) {
                                        curr = [appName].concat(curr);
                                    } else {
                                        curr = flapjax.util.xlib.slice(curr, 1);
                                    }
                                }
                            }
                            if ( typeof(param) == 'string' ) {
                                acc[param] = curr;
                            } else if (curr === undefined) {
                            } else {
                                if (typeof(curr) == 'object' && !flapjax.member(curr.k, param) ) { throw serviceName + ': unknown parameter option "' + curr.k + '"'; } //SAFETY
                                acc[curr.k] = curr.v;
                            }
                            return acc;
                        },
                        {version: flapjax.util.version},
                        args, params)],
                 id: 3}.toJSONString(),  /* remove proto TODO flapjax.util.json.toJSONString */
                function (http) {return fserver.marshall.handler(exnE, handler, http.responseText); },
                async  === undefined? defaultAsync : async);
        };
    };

    flapjax.util.lib.forEach(
        function (tuple) {
            server.basicJson[tuple[0]] = basicJsonRpcMaker.apply(this, tuple);          
        },
        $___rpcSchemas);
    
    wrapHandler(server.basicJson, 'login', checkLogin);
    wrapHandler(server.basicJson, 'extend', checkLogin);
    wrapHandler(server.basicJson, 'check', checkLogin);

    //==============PUBLISH RPCS        
    flapjax.util.lib.forEach(
        function (tuple) {
            flapjax.util.lib.forEach(
                function (pre, type) {
                    $$___sa(
                        {}, 
                        pre + tuple[0].charAt(0).toUpperCase() + tuple[0].substring(1),
                        type[tuple[0]]);                        
                },
                ['post', 'get', 'json'],
                [server.basicPost, server.basicGet, server.basicJson]);
        },
        $___rpcSchemas);
    
    //=============
    //Array PathObject U Undefined * Array PathObject  -> int
    // 1 if new path, -1 if outdated path, 0 if same path
    // compares using global timestamps
    // if old undefined, returns 1 for new path
    var comparePaths = function (oldPath, newPath, writers) {
        if (oldPath === undefined) {
            logB.push('no path to compare');
            return 1;
        } else {
            logB.push('paths lens: ' + oldPath.length + ', ' + newPath.length);    
            for (var i = 0; i < Math.min(oldPath.length, newPath.length); i++) {
                logB.push('compare paths: ' + (oldPath[i].oid? oldPath[i].oid : oldPath[i].ref) + oldPath[i].gts + 'vs' + newPath[i].gts);
                if (oldPath[i].gts < newPath[i].gts) {
                   if (isLocalWrite(newPath[i], writers)) { continue; }
                   else { logB.push('found new path oid on i: ' + newPath[i].oid + ', ' + i); return 1; }
                } else if (oldPath[i].gts > newPath[i].gts) {
                    return -1;
                }
            }
            return 0;
        }
    };

    //sid == uid
    var isLocalWrite = function (obj, writers) {
        
	//TODO don't check sid because using nonce lts. can optimizing later.
	//  bug 10/10/06 - leo - login is uid, not sid
	/*if (obj.sid != flapjax.util.behaviours.valueNow($___loginB) ) { 
	    logB.push('---local: wrong sid: ' + obj.sid + ' vs ' + flapjax.util.behaviours.valueNow($___loginB) + '---');
            return false; 
        }*/
        for (var i = 0; i < writers.length; i++) {
            if (writers[i].lts == obj.lts) {
                return true;
            }
        }
        return false;
    };

    //traverse both in lockstep, breadth first. first one with a newer value wins.
    //cycle means same
    //if a new ref, would register as a change in current object, so do not worry
    //if all same, 0
    var isNewDeepObject = function (oldRead, newRead, writers) {           

        if (oldRead === undefined) { return true; }

        //VAL
        if (!(newRead.root.ref)) {
            if (oldRead.root.gts < newRead.root.gts) {
                return !isLocalWrite(newRead.root, writers);
            } else {
                return false;
            } 
        }

        //REF
        var queue = [newRead.root.ref];
        var refCache = [];

	//make sure traversing with newRead 
	//  can be diff obj but can be ignoring so far because of LTSs
	//  in this case, old may not have new fields, 
	//  and must do a recursive check that all fields have a known lts

        while (queue.length > 0) {
            var hdRef = queue.shift();
	   
            if (refCache[hdRef]) { 
                continue; 
            } else {
                refCache[hdRef] = true;
            }

            if (!oldRead.objects[hdRef]) { //new obj, so check lts
                if (!isLocalWrite(newRead.objects[hdRef], writers)) {
                    return true;
                }
            } else if (oldRead.objects[hdRef].gts < newRead.objects[hdRef].gts) {
                if (!isLocalWrite(newRead.objects[hdRef], writers)) {
                    return true;
                }
            } else if (oldRead.objects[hdRef].gts > newRead.objects[hdRef].gts) {
                return false; /* highly unlikely */
            } 
            if (newRead.objects[hdRef].fields) {
                for (var i in newRead.objects[hdRef].fields) {
                    if (Object.prototype[i] !== undefined) { continue; } /* play safe */
                    if (newRead.objects[hdRef].fields[i].ref) {
                        queue.push(newRead.objects[hdRef].fields[i].ref);
                    } else if (typeof(newRead.objects[hdRef].fields[i]) == 'string') {
                    //TODO remove case when protocol fixed
                        queue.push(newRead.objects[hdRef].fields[i]);
                    } 
                }
            }                
        }

        return false;
    };

    var isDeepRecentlyChanged = function (previousRead, currentRead, writers) {
	if (previousRead === undefined) { return true; }
        if (currentRead.root.ref && (currentRead.root.ref == previousRead.root.ref)) {
	    	logB.push('same root, checking deep');
		return isNewDeepObject(previousRead, currentRead, writers);
        } else {
            var comparison = 
                comparePaths(
                    previousRead.path.concat([previousRead.root]), 
                    currentRead.path.concat([currentRead.root]),
                    writers);
            if (comparison > 0) {
		logB.push('--- new > old ---');
                return true; /* may be a little conservative */
            } else if (comparison === 0) {
                if (currentRead.root.ref) {
                   // throw 'isDeepRecentlyChanged: different IDs, yet same paths';
		   // possible as local write to path counts as no change
		   return isNewDeepObject(previousRead, currentRead, writers);
                }
		logB.push('--- new = old ---');
                return isNewDeepObject(previousRead, currentRead, writers);    
            } else /* comparison < 0 */ {
            	logB.push('--- new < old ---');
	        return false;
            }
        }
    };

    var isShallowRecentlyChanged = function (previousRead, currentRead, writers) {
        if (currentRead.root.ref && currentRead.root.ref == previousRead.root.ref) {
            logB.push('---same root--');
	    if (currentRead.root.gts > previousRead.root.gts) {
                logB.push('---same roots, and global updated, so checking local---');
	        return !isLocalWrite(currentRead.root, writers);
            } else {
                return false;
            }
        } else {
            var comparison = 
                comparePaths(
                    previousRead.path.concat([previousRead.root]), 
                    currentRead.path.concat([currentRead.root]),
                    writers);
            if (comparison > 0) {
		logB.push('--- new > old ---');
                return true; /* may be a little conservative */
            } else if (comparison === 0) {
                if (currentRead.root.ref) { 
                    //throw 'isShallowRecentlyChanged: different IDs, yet same paths'; 
		    //possibly new path so new ref, but == 0 because lts's checked out
		    return false;
                }
		logB.push('--- new = old ---');
                return false;
		//!isLocalWrite(currentRead.root, writers);    
            } else /* comparison < 0 */ {
                logB.push('--- new < old ---');
                return false;
            }
        }
    };


    //=============CLIENTSIDE RECURSIVEREAD
    var recursiveReadProtocolMaker = 
        function (protocol) {
            return function (url, handler, async, exnE, user, object, path) {
                protocol.deepRead(
                    url,
                    function (result) {
                        var obj = fserver.marshall.untieDeepRead(result.root, result.objects);
                        return handler(obj);
                    },
                    async,
                    exnE,
                    user,
                    object,
                    path);
            };
        };

    var recursiveShallowReadProtocolMaker = 
        function (protocol) {
            return function (writers) { //stateful read         
                var previousRead;           
                return function (url, handler, async, exnE, user, object, path) {
                    protocol.deepRead(
                        url,
                        function (result) {
			    logB.push('-----snew----');
                            var fresh = 
                                (previousRead === undefined 
                                || isShallowRecentlyChanged(previousRead, result, writers));
                            logB.push('---fresh:' + fresh + '---');
			    previousRead = result;
                            if (fresh) {
                                var obj = fserver.marshall.untieDeepRead(result.root, result.objects);
                                //logB.push('fresh shallow read!');
                                return handler(obj);
                            }
                            logB.push('old shallow read');
                        },
                        async,
                        exnE,
                        user,
                        object,
                        path);
                };
            };
        };

    var recursiveDeepReadProtocolMaker = 
        function (protocol) {
            return function (writers) { //stateful read         
                var previousRead;           
                return function (url, handler, async, exnE, user, object, path) {
                    protocol.deepRead(
                        url,
                        function (result) {
                            logB.push('--dr--');
			    var fresh = 
                                (previousRead === undefined 
                                || isDeepRecentlyChanged(previousRead, result, writers));
                            logB.push('---fresh read: ' + fresh + '---');
                            previousRead = result;
                            if (fresh) {
                                var obj = fserver.marshall.untieDeepRead(result.root, result.objects);
                                //logB.push('---fresh: ' + (obj.bar !== undefined));
                                return handler(obj);
                            }
                        },
                        async,
                        exnE,
                        user,
                        object,
                        path);
                };
            };
        };
    
        
        
    flapjax.util.lib.forEach(
        function (protocol) { 
            protocol.recursiveRead = recursiveReadProtocolMaker(protocol); 
            protocol.makeRecursiveShallowRead = recursiveShallowReadProtocolMaker(protocol); 
            protocol.makeRecursiveDeepRead = recursiveDeepReadProtocolMaker(protocol); 
        },
        [server.basicGet, server.basicPost, server.basicJson]);

    //=============CLIENTSIDE RECURSIVEWRITE
    var recursiveWriteProtocolMaker = 
        function (protocol) {
            return function (url, handler, async, exnE, user, object, path, lts, value) {
                var objects = [];
                var root = fserver.marshall.tieDeepWrite(value, objects);

                protocol.deepWrite(
                    url,
                    function (result) {
                        return handler(result);
                    },
                    async,
                    exnE,
                    user,
                    object,
                    path,
                    lts,
                    { objects: objects, root: root });
            };
        };
    flapjax.util.lib.forEach(
        function (protocol) { protocol.recursiveWrite = recursiveWriteProtocolMaker(protocol); },
        [server.basicGet, server.basicPost, server.basicJson]);


    // String U Undefined -> Protocol
    var pickProtocol = function (optProtocol) { 
        switch (optProtocol) {
            case undefined:
            case 'json':
                return server.basicJson;
            case 'post':
                return server.basicPost;
            case 'get':
                return server.basicGet;
            default:
                return defaultProtocol;             
        }
    };
    

    //============= PERSISTENT BEHAVIOURS
    
    //TODO lift library->server calls 
    
    // updateEventStream is the read stream (probably a receiver_e() for some polling) from the
    // server.  objId and fieldName are the server values, and init is the value before the response
    // comes in.
    /*
        PersistentBehaviour:
              {     [blocking: Boolean] //later do local blocking, default false
                [initial: a] //default undefined
                [(mode: 'overwrite' U 'new')] //default new
                [poll: Number] // never if unspecified or <= 0
                [url: String] // default to url set by fserver, throw exn if doesn't exist
                object: String 
                fieldName: String
                [synchronizedWrite: Boolean] // default false: write only if
                    client copy of data matches server
                [blockingWrite: Boolean] //default: false
                [writeE: Event a]
                [protocol: 'post' U 'get' U 'json'] // default jsonPost
              }
              [* Event a]
        member fields: 
            {
               exceptionsE: Event String
            }
    */  
    
    var allWriters = []; //store any write stream, so nondiscriminating readers can check against LTSs here

    //TODO make a way to cancel
    //TODO take an exception stream parameter
    fserver.browser.pollingReadInjector = function (protocol, url, poll, async, user, object, path, valE, exnE, writers, deepRead) {

        var statefulReadFn = deepRead? 
            protocol.makeRecursiveDeepRead(writers) : protocol.makeRecursiveShallowRead(writers);

        var fire = function () {
                statefulReadFn(
                    url,
                    function (obj) {
                        flapjax.util.combinators.sendEvent(valE, obj);
                    },
                    async,
                    exnE,
                    user,
                    object,
                    path);
            };
        
        fire();
        if (poll > 0) { setInterval(fire, poll); }
    };

    fserver.browser.readPersistentObject = function (options) {
        options = options === undefined ? {} : options;

        var url = options.url ? options.url : defaultUrl;
        if (url === undefined) { throw 'readPersistentObject: no associated URL'; } //SAFETY
        
        var serverValueReadsE = flapjax.util.combinators.createEventReceiver();
        var beh = new flapjax.util.behaviours.Behaviour(serverValueReadsE, options.initial);      
        beh.exceptionsE = flapjax.util.combinators.createEventReceiver();
        beh.user = options.user; 
        beh.object = options.object;
        beh.path = options.path instanceof Array? options.path : [];
        beh.writers = options.writers ? options.writers : allWriters; 

        fserver.browser.pollingReadInjector(
            pickProtocol(options.protocol), 
            url,
            options.poll === undefined? defaultPoll : options.poll,
            (options.blocking === undefined? defaultAsync : !options.blocking),
            options.user, 
            beh.object,
            beh.path,
            serverValueReadsE,
            beh.exceptionsE,
            beh.writers,
            (options.deep === undefined)? defaultDeepRead : options.deep);

        return beh;
    };
    $$___sa({}, 'readPersistentObject', fserver.browser.readPersistentObject);
    

    //TODO cleanup
    fserver.browser.readPermissionsB = function (options /* {user, object, path [, init] [, protocol]} */) {
        if (options === undefined) { options = {}; }
        var serverValsE = flapjax.util.combinators.createEventReceiver();
        
        var beh = new flapjax.util.behaviours.Behaviour(
                serverValsE, options.init);
        beh.exceptionsE = flapjax.util.combinators.createEventReceiver();

        var url = options.url ? options.url : defaultUrl;
        if (url === undefined) { throw 'readPermissionsB: no associated URL'; } //SAFETY

        var poll = options.poll === undefined? defaultPoll : options.poll;

        var permissions = {}; //permissions.<name> :: behaviour boolean
        var registered = [];
        var arr = [];
        //TODO redo arrB as topologically evaluated with respect to has<permission>
        var arrB = flapjax.util.behaviours.createConstantB([]);
        beh.allB = arrB;
        
        var registerPermission = function (str, init) {
                var ustr = str.toUpperCase();
                registered.push(ustr);
                permissions[ustr] =
                flapjax.util.behaviours.createConstantB(
                    arguments.length == 1 ? defaultPermission : init);
        };

        beh.has = function (str, init) {
            var ustr = str.toUpperCase();
            if (permissions[ustr] === undefined) {
                /* slice because don't know whether init was specified */
                registerPermission.apply(this, flapjax.util.xlib.slice(arguments, 0));
            }
            return permissions[ustr];
        };
        
        var fire = function () {
               (pickProtocol(options.protocol)).getPermissions(
                    url,
                    function (res) {
                        for (var i = 0; i < res.length; i++) {
                            if (flapjax.util.lib.member(res[i], registered)) {
                                if (!(flapjax.util.behaviours.valueNow(permissions[res[i]] === true))) {
                                    flapjax.util.combinators.sendEvent(permissions[res[i]].underlyingRaw, true);
                                    logB.push('set ' + i + ' to true');
                                    logB.push('i valuenow: ' + flapjax.util.behaviours.valueNow(permissions[res[i]]));
                                }
                            } else {
                                registerPermission(res[i], true);
                            }
                        }
                        for (var j = 0; j < registered.length; j++) {
                            if (!flapjax.util.lib.member(registered[j], res)) {
                                flapjax.util.behaviours.sendBehaviour(permissions[registered[j]], false);
                                    logB.push('set ' + i + ' to false');
                            }
                        }
                        flapjax.util.behaviours.sendBehaviour(arrB, res);
                    },
                    options.blocking === undefined ? defaultAsync : !options.blocking,
                    beh.exceptionsE,
                    options.user,
                    options.object,
                    options.path instanceof Array? options.path : []);
            };
        fire();
        if (poll > 0) { setInterval(fire, poll); }
        return beh;
    };
    $$___sa({}, 'readPermissionsB', fserver.browser.readPermissionsB);

    fserver.browser.writePersistentObject = function (writeStreamE, options) {

        if (!(writeStreamE instanceof flapjax.util.engine.Node)) { throw 'writeStreamE argument must be an event stream'; }
        options = options === undefined ? {} : options;

        var res = 
            {
                exceptionsE: flapjax.util.combinators.createEventReceiver(),
                lts:  Math.floor(Math.random() * maxLTS),
                successesE: flapjax.util.combinators.createEventReceiver()
            };
        allWriters.push(res);

        var url = options.url ? options.url : defaultUrl;
        if (url === undefined) { throw 'writePersistentObject: no associated URL'; } //SAFETY

        //TODO use synchronized flag
        //TODO use mode flag
        //TODO in case of exn, should rollback LTS, and ideally propagate any relevenat arguments currently held up by it
        flapjax.util.engine.createNode(
            [writeStreamE],
            function (s, p) {
                (pickProtocol(options.protocol)).recursiveWrite(
                    url,
                    function (resp) { 
                        flapjax.util.combinators.sendEvent(res.successesE, resp);
                    },
                    options.blocking === undefined? defaultAsync : !options.blocking,
                    res.exceptionsE,
                    options.user,
                    options.object,
                    options.path instanceof Array ? options.path : [],
                    res.lts,
                    p.value);
            });

        return res;
    };

    $$___sa({e: true, a: 0}, 'writePersistentObject', fserver.browser.writePersistentObject);

    fserver.browser.bindPersistentBehaviour = function (object, fieldName, writeStreamE, options) {
        var readB = fserver.browser.readPersistentObject(object, fieldName, options);
        var writeExceptionsE = fserver.browser.writePersistentObject(object, fieldName, writeStreamE, options);
    
        readB.exceptions = flapjax.util.c.merge_e(readB.exceptions, writeExceptionsE);
        return readB;
    };
    $$___sa({e: true, a: 2}, 'bindPersistentBehaviour', fserver.browser.bindPersistentBehaviour);
    
    //============= CONSTANTS POST
    //should all be defined earlier
    
    defaultProtocol = server.basicJson;

    
    //============= PROCESS ANNOTATIONS & EXPORT

    for (var i = 0; i < $___sa.length; i++) {
        var tuple = $___sa[i];
        
        if (tuple[0].b) { 
            flapjax.util.annotations.addTupleToBehaviour(tuple); 
        }
        if (tuple[0].e) { 
            flapjax.util.annotations.addTupleToNode(tuple); 
        }

        if (tuple[0].np !== true) { 
            fserver.pub[tuple[1]] = tuple[2]; 
        }

    }

    if (makeTopLevel !== false) {
        for (var zz in fserver.pub) {
            eval(zz + " = fserver.pub." + zz + ";"); 
        }
    }

    fserver.pub.$___sdefs = $___sa;

    return fserver.pub;
}
