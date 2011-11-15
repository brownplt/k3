
function stringCmp(a,b) {return (a > b) ? 1 : (b > a) ? -1 : 0;}

/*
 * General Utility Functions
 */

/*
 * Get an object's true x and y position.
 */
function getDomXY(domobj) {
	var xy = [domobj.offsetLeft,domobj.offsetTop]
	while(domobj.offsetParent && domobj.offsetParent != domobj) {
		domobj = domobj.offsetParent;
		xy[0] += domobj.offsetLeft;
		xy[1] += domobj.offsetTop;
	}
	return xy;
}

/*
 * Is a given value in a list? (using == instead of ===)
 */
function inList(val, list) {
	return fold( function(v, acc) {
		return acc || v == val;
		}, false, list);
}

/*
 * Return a list of all integers such that low <= num < high
 */
function range(low,high) {
	var ret = [];
	for(var i = low; i < high; i++) ret.push(i);
	return ret;
}

/*
 * Take a list lst and turn it into a dictionary, such that dict[key(k)] = k
 * for all k in lst.
 */
function toObj(lst,key) {
	var ret = {}
	map(function (li) {ret[key(li)] = li;},lst);
	return ret;
}

/*
 * Shallow copy an object: create a new object with a different identity but
 * the same attributes.
 */
function objCopy(obj) {
	var newObj = {};
	for(var k in obj) {
		newObj[k] = obj[k];
	}
	return newObj;
}

/*
 * Strip all leading and trailing spaces from a string
 */
function strip(str) {
	var m,n;
	for(m=0;m < str.length && (str[m] == ' ' || str[m] == ',');m++);
	for(n=str.length;n>0 && (str[n-1] == ' ' || str[n-1] == ',');n--);
	if(m >= n) return ''; else return str.substr(m,n-m);
}

/* collect_b :: b * Event a * (a * b -> b) -> Behaviour b
 * 
 * Collect events into a behaviour. 
 */
function collect_b(initval,evt,funct) {
	return evt.collect_e(initval,funct).startsWith(initval);
}

/* focus_b :: Behaviour Object x String -> Behaviour a
 *
 * Take a time-varying object, and return the current value of one of its
 * attributes as a time-varying value.
 */
function focus_b(objB,fieldName) {
	return objB.transform_b(function(obj) {return obj[fieldName];});
}

/* toResultDom :: a x String -> Dom
 *
 * Take an object and a success message, and return a DOM object that displays
 * either error or success appropriately.
 */
function toResultDom(v,successMsg) {
	if(v.error) return P({className:'error'},v.error); else return P({className:'feedback-success'},successMsg);
}

/* resultTrans :: String -> (a -> Dom)
 *
 * Take a success message, and returns a function that converts and object to
 * an error/success DOM
 */
function resultTrans(successMsg) {
	return function(v) {return toResultDom(v,successMsg);};}

/* onlyErrors :: a -> Boolean
 * Return true if input is an error
 */
function onlyErrors(_) {return _.error;}

/* noErrors :: a -> Boolean
 * Return true if input is not error
 */
function noErrors(_) {return !_.error;}

/*
 * Take an unformatted string, and format it using paragraphs and linebreaks
 * so that it can be inserted into the DOM. Takes the string to format and the
 * class name to give the outer DIV that gets returned
 */
function paraString(str,dcl,blen) {
	if (str == undefined) str = 'undefined';
	if (blen == undefined) blen = 80;
	var lines = str.split('\n');
	var allparas = [];
	var thispara = [];
	var tab = String.fromCharCode(160); tab = tab+tab; tab=tab+tab; tab=tab+tab;
	var breakUpLine = function(line) {
		if(line.length < blen) {
			procLine(line);
			return;
		}
		var nextJ = function(j) {
			if(j > blen) return (j < line.length) ? j+1 : -1
			else if(j == 0) return blen+1;
			else return j-1;
		}
		for(var j=blen;j!=-1;j=nextJ(j)) {
			if(line.substr(j,1) == ' ' || line.substr(j,1) == '\t') {
				procLine(line.substring(0,j));
				breakUpLine(line.substring(j+1,line.length));
				return;
			}
		}
	}
	var procLine = function(line) {
		var lblank = true;
		var lout = '';
		if(blen && line.length > blen+20) {
			breakUpLine(line);
			return;
		}
		for(var j=0;j<line.length;j++) {
			if (line.substring(j,j+1) == ' ') {
				if((j>0  && line.substring(j-1,j) == ' ') || (j<line.length && line.substring(j+1,j+2) == ' '))
					lout += String.fromCharCode(160);
				else
					lout += ' ';
			}
			else if(line.substring(j,j+1) == '\t')
				lout += tab;
			else if(line.substring(j,j+1) == '\r');
			else {
				lblank = false;
				lout += line.substring(j,j+1);
			}
		}
		if(!lblank) {
			thispara.push(lout);
			thispara.push(BR());
			}
		else if (thispara.length > 0) {
			allparas.push(P(thispara));
			thispara = [];
		}
	}
	for(var i=0;i<lines.length;i++) {
		procLine(lines[i]);
	}
	if (thispara.length > 0)
		allparas.push(P(thispara))
	return DIV({className:dcl},allparas);
}

/*
 * Add a class (word) to a list of classes (space-separated words).
 */
function addClass(clist,ncls) {
	if (clist == '')
		return clist + ncls;
	else
		return clist + ' ' + ncls;
}

/*
 * Remove a class (word) from a list of classes (space-separated words).
 */
function remClass(clist,cls) {
	return fold(function(v, acc) {if(v != cls) return acc + (acc == '' ? '' : ' ') + v; else return acc;},'',clist.split(' '));
}

/*
 * Make a constructor inherit from a given constructor, but without invoking
 * the superclass constructor.
 */
function inheritFrom(subfn,superfn) {
	var r = function () {}
	r.prototype = superfn.prototype;
	subfn.prototype = new r();
}

/*
 * Widgets
 */

/*
 * Base Widget class. A Widget is a DOM object that has events or behaviours
 * associated to it. A Widget object has three members:
 * 		dom: [Behaviour] DOM
 * 		behaviors: Object whose members are behaviours
 * 		events: Object whose members are events
 */
function Widget() {
	this.dom = '';
	this.behaviors = {};
	this.events = {};
}
Widget.prototype = new Object();

/* ToggleWidget :: String * String
 *
 * Create a widget that displays as a link and acts as a "toggle".
 * ontxt: The text to display on the "turn on" link (i.e. when the current
 * 		state is "off")
 * offtxt: The text to display on the "turn off" link
 *
 * Exposes events:
 * 		-toggleOn: fires whenever the "on" link is clicked
 * 		-toggleOff: fires whenever the "off" link is clicked
 * 		-toggle: fires whenever either link is clicked
 * Exposes behaviour:
 * 		-toggled: "true" when the widget is in the "on" state, and "false"
 * 			when it is in the "off" state.
 */
function ToggleWidget(ontxt,offtxt) {
	Widget.apply(this);
	var onlink = A({href:'javascript:undefined'},ontxt);
	var offlink = A({href:'javascript:undefined'},offtxt);
	this.events.toggleOn = extractEvent_e(onlink,'click').constant_e(true);
	this.events.toggleOff = extractEvent_e(offlink,'click').constant_e(false);
	this.events.toggle = merge_e(this.events.toggleOn,this.events.toggleOff);
	this.behaviors.toggled = this.events.toggle.startsWith(false);
	this.dom = this.behaviors.toggled.transform_b(function(t) {return t ? offlink : onlink;});
}
inheritFrom(ToggleWidget,Widget);

/* InputWidget :: DOM
 *
 * Base class for input widgets. An InputWidget is a widget that takes user
 * input, and exposes it as a value. InputWidgets have a behavior inputElems,
 * that contains all of the elements used to get input from the user.
 * Additionally, each InputWidget has a behaviour named "value" that holds the
 * current value of the user input.
 *
 * To create an InputWidget, invoke this constructor with any DOM object that
 * $B accepts (i.e. an INPUT, SELECT or TEXTAREA) or use one of the subclasses.
 */
function InputWidget(ielem) {
	Widget.apply(this);
	this.behaviors.value = $B(ielem);
	this.dom = ielem;
	this.behaviors.inputElems = constant_b([ielem]);
}
inheritFrom(InputWidget,Widget);

/* TextInputWidget :: String * Integer * Integer
 *
 * Create a text-field input widget with a given initial value, size, and
 * maximum input length.
 */
function TextInputWidget(initVal,size,maxLength) {
	var props = {type:'text', value:initVal};
	if(size) props.size = size;
	if(maxLength) props.maxLength = maxLength;
	InputWidget.apply(this,[INPUT(props)]);
}
inheritFrom(TextInputWidget,InputWidget);

/* TextAreaWidget :: String * Integer * Integer
 *
 * Create a TEXTAREA input widget.
 */
function TextAreaWidget(initVal,rows,cols) {
	InputWidget.apply(this,[TEXTAREA({rows:rows,cols:cols},initVal)]);
}
inheritFrom(TextAreaWidget,InputWidget);

/* CheckboxWidget :: Boolean
 *
 * Create an input widget with a single checkbox.
 */
function CheckboxWidget(initVal) {
	InputWidget.apply(this,[INPUT({type:'checkbox','checked':(initVal ? true : false)})]);
}
inheritFrom(CheckboxWidget,InputWidget);

/* SelectWidget :: a * [Dom]
 *
 * Create a SELECT input widget. Takes an initial value and a list of OPTION
 * elements. The initially selected OPTION will be the one whose "value"
 * attribute is equal to the supplied initVal.
 */
function SelectWidget(initVal,options) {
	map(function(o) {if(o.value == initVal) o.selected = true;},options);
	InputWidget.apply(this,[SELECT(options)]);
}
inheritFrom(SelectWidget,InputWidget);

/* DateWidget :: Integer
 *
 * Create a widget for inputting dates and times in HH:MM DD-MM-YYYY format.
 * This widget's values are expressed in UNIX-timestamp format, as the number
 * of seconds since the epoch.
 */
function DateWidget(initVal) {
	Widget.apply(this);

	var theDate = new Date(initVal * 1000);

	function twodigits(inint) {
		if(inint <= 0 && inint < 10)
			return '0' + inint;
		else
			return ''+inint;
	}

	var hoursBox = INPUT({type:'text',size:2,maxLength:2,value:initVal?theDate.getUTCHours():''});	
	var minutesBox = INPUT({type:'text',size:2,maxLength:2,value:initVal?twodigits(theDate.getUTCMinutes()):''});	
	var dateBox = INPUT({type:'text',size:2,maxLength:2,value:initVal?theDate.getUTCDate():''});	
	var monthBox = INPUT({type:'text',size:2,maxLength:2,value:initVal?theDate.getUTCMonth()+1:''});	
	var yearBox = INPUT({type:'text',size:4,maxLength:4,value:initVal?theDate.getUTCFullYear():''});

	this.behaviors.dateObj = lift_b(function(h,m,dd,mm,yyyy) {
		var theDate = new Date();
		theDate.setUTCFullYear(yyyy);
		theDate.setUTCMonth(mm-1);
		theDate.setUTCDate(dd);
		theDate.setUTCHours(h);
		theDate.setUTCMinutes(m);
		return theDate;
	},$B(hoursBox),$B(minutesBox),$B(dateBox),$B(monthBox),$B(yearBox));
	this.behaviors.value = this.behaviors.dateObj.transform_b(function(dbj) {return parseInt(dbj.getTime() / 1000);});
	this.dom = SPAN(hoursBox,' : ',minutesBox,' UTC ',dateBox,' - ',monthBox,' - ',yearBox);
	this.behaviors.inputElems = constant_b([hoursBox,minutesBox,dateBox,monthBox,yearBox]);
}
inheritFrom(DateWidget,InputWidget);

var startnum = 1;
/* CheckboxListWidget :: [{k:a, v:String}] * [a]
 *
 * Create a list of checkboxes. The CheckboxListWidget constructor takes two
 * arguments. The first is a list of objects, where each object has a "k"
 * attribute and a "v" attribute. The "v" attribute will be displayed to the
 * user next to its associated checkbox. The second is a list of the "k"
 * attributes of all the checkboxes that should be selected initially.
 * The value of the widget is a list of the "k" attributes of all of the
 * selected checkboxes.
 */
function CheckboxListWidget(cbkvs,init) {
	Widget.apply(this);
	var widg = this;

	var cbvals = {};
	var inputElems = [];

	map(function(cbkv) {cbvals[cbkv.k] = false;},cbkvs);
	map(function(iv) {cbvals[iv] = true;},init);
	var evts = [];
	this.dom = UL({className:'checkbox-list'},map(function(cbkv) {
		var cb = INPUT({type:'checkbox',name:'cblistwidget-'+startnum,checked:cbvals[cbkv.k]});
		inputElems.push(cb);
		evts.push($E(cb).transform_e(function(_) {return {k:cbkv.k,v:_};}));
		return LI(cb,cbkv.v);
	},cbkvs));
	this.behaviors.value = merge_e.apply({},evts).transform_e(function(ne) {
		cbvals[ne.k] = ne.v;
		return cbvals;
	}).startsWith(cbvals).transform_b(function(cbvs) {return fold(function(v, acc) {if (cbvs[v.k]) acc.push(v.k); return acc;},[],cbkvs);});
	this.behaviors.inputElems = constant_b(inputElems);
	startnum += 1;
}
inheritFrom(CheckboxListWidget,InputWidget);

/* RadioListWidget :: [{k:a, v:String}] * a
 *
 * Create a list of radio buttons. The constructor takes a list of objects like
 * the CheckboxListWidget constructor above, and a single "k" value to set the
 * initially selected radio button. The widget's value is the "k" value of the
 * currently selected radio button.
 */
function RadioListWidget(cbkvs,init) {
	Widget.apply(this);
	var widg = this;

	var inputElems = [];
	var triggerE = consumer_e();
	this.dom = UL({className:'checkbox-list'},map(function(cbkv) {
		if(document.all && !window.opera && document.createElement) /* Yay for IE! */
			var cb = document.createElement('<input type="radio" name="cblistwidget-'+startnum+'" value="'+cbkv.k+'" '+(cbkv.k == init ? 'checked>' : '>'));
		else
			var cb = INPUT({type:'radio',name:'cblistwidget-'+startnum,value:cbkv.k,checked:(cbkv.k==init)});
		inputElems.push(cb);
		cb.onclick = function(_) {triggerE.sendEvent('');};
		return LI(cb,cbkv.v);
	},cbkvs));
	this.behaviors.value = triggerE.transform_e(function(ne) {
		return fold(function(v,acc) {if (v.checked) return v.value; else return acc;},undefined,inputElems);
	}).startsWith(init);
	this.behaviors.inputElems = constant_b(inputElems);
	startnum += 1;
}
inheritFrom(RadioListWidget,InputWidget);

/* LinkListWidget :: [{k: a, v: String}] * a * Boolean
 *
 * Create a list of links. The constructor takes a list of objects like the
 * CheckboxListWidget constructor above, and a single "k" value to set the
 * initially selected link. It also takes a boolean that determines whether
 * the list will have "Previous" and "Next" links. The widget's value is the
 * value of the currently selected link.
 */
function LinkListWidget(values,initial,prevnext) {
	Widget.apply(this);
	var choiceE = receiver_e();
	var inputElems = [];
	var widg = this;
	function makeChooser(idx,k,v) {
		var d = A({href:'javascript:undefined'},v);
		d.onclick = function() {choiceE.sendEvent(idx);};
		inputElems.push(d);
		return {index:idx,k:k,v:v,dom:LI({className:'choose-one'},d)};
	}
	var choosers = [];
	var initIdx = 0;
	for (i=0;i<values.length;i++) {
		choosers.push(makeChooser(i,values[i].k,values[i].v));
		if(values[i].k == initial) initIdx = i;
	}

	if(prevnext) {
		this.events.prevnext = receiver_e();
		var newElem = receiver_e();
		this.makePrevBtn = function() {
			var p = A({href:'javascript:undefined'});
			p.innerHTML='&larr;&nbsp;Previous&nbsp;&nbsp;';
			var altp = SPAN({style:{color:'#666'}});
			altp.innerHTML='&larr;&nbsp;Previous&nbsp;&nbsp;';
			p.onclick = function() {widg.events.prevnext.sendEvent('prev');};
			newElem.sendEvent(p);
			return choiceIdxB.transform_b(function(cch) {return cch == 0 ? altp : p;});
		};
		this.makeNextBtn = function() {
			var n = A({href:'javascript:undefined'});
			var altn = SPAN({style:{color:'#666'}});
			n.innerHTML='&nbsp;Next&nbsp;&rarr;';
			altn.innerHTML='&nbsp;Next&nbsp;&rarr;';
			n.onclick = function() {widg.events.prevnext.sendEvent('next');};
			newElem.sendEvent(n);
			return choiceIdxB.transform_b(function(cch) {return cch == (choosers.length-1) ? altn : n;});
		};
		var choiceIdxB = merge_e(choiceE,this.events.prevnext).
			collect_e(initIdx,function(next,last) {
					if(next == 'next') return last+1; else if(next == 'prev') return last-1; else return next;}).startsWith(initIdx);
		this.dom = ULB(LIB({className:'choose-prev'},this.makePrevBtn()),
					choiceIdxB.transform_b(function(cch) {
						return map(function(ch) {return (cch == ch.index) ? LI({className:'choose-one current'},ch.v) : ch.dom;},choosers);
					}),
					LIB({className:'choose-next'}, this.makeNextBtn()));
		this.behaviors.inputElems = collect_b(inputElems,newElem,function(v,acc) {return acc.concat(v);});
	}
	else {
		var choiceIdxB = choiceE.startsWith(initIdx);
		this.dom = ULB(choiceIdxB.transform_b(function(cch) {
						return map(function(ch) {return (cch == ch.index) ? LI({className:'choose-one current'},ch.v) : ch.dom;},choosers);
					}));
		this.behaviors.inputElems = constant_b(inputElems);
	}
	this.behaviors.value = choiceIdxB.transform_b(function(idx) {return choosers[idx].k;});
}
inheritFrom(LinkListWidget,InputWidget);

/* ConstantInputWidget :: a
 *
 * Create a "dummy" widget with a constant value and no DOM.
 * value: the widget's value.
 */
function ConstantInputWidget(value) {
	Widget.apply(this);
	this.behaviors.value = constant_b(value);
	this.behaviors.inputElems = [];
	this.dom = SPAN();
}
inheritFrom(ConstantInputWidget,InputWidget);

/* ClickWidget :: DOM * a
 *
 * Create a widget with a "Click" event.
 */
function ClickWidget(dom,value) {
	Widget.apply(this);
	this.btn = dom;
	this.dom = dom;
	this.events.click = extractEvent_e(this.btn,'click').constant_e(value);
}
inheritFrom(ClickWidget,Widget);

/* ButtonWidget :: String * a
 *
 * Create a button widget.
 */
function ButtonWidget(text,value) {
	ClickWidget.apply(this,[INPUT({type:'button',value:text}),value]);
}
inheritFrom(ButtonWidget,ClickWidget);

/* disableMsg :: String * Behaviour bool -> ButtonWidget
 *
 * Make the button appear disabled--and have different text--whenever a certain
 * behaviour is troe.
 */
ButtonWidget.prototype.disableMsg = function(msg,disB) {
	insertValueB(disB.transform_b(function(_) {return _ ? true : false;}),this.btn,'disabled');
	var btnVal = this.btn.value;
	insertValueB(disB.transform_b(function(_) {return _ ? msg : btnVal;}),this.btn,'value');
	return this;
}

/* LinkWidget :: String * a
 *
 * Create a link widget.
 */
function LinkWidget(text,value) {
	ClickWidget.apply(this,[A({href:'javascript:undefined'},text),value]);
}
inheritFrom(LinkWidget,ClickWidget);

/* disableMsg :: String * Behaviour bool -> ButtonWidget
 *
 * Make the button appear disabled--and have different text--whenever a certain
 * behaviour is troe.
 */
LinkWidget.prototype.disableMsg = function(msg,disB) {
	this.dom = disB.transform_b(function(_) {
		return _ ? this.btn : SPAN(msg);
	});
	return this;
}

/* ButtonInputWidget :: [InputWidget] * {ClickWidget} * (. Array a -> b) * ([DOM] * {DOM} -> DOM)
 */
function ButtonInputWidget(wdict,cdict,valfn,domfn) {
	Widget.apply(this);

	this.behaviors.value = lift_b.apply({},[function() {
		return valfn.apply({},slice(arguments,0));
	}].concat(map(function(w) {return w.behaviors.value;},wdict)));

	this.behaviors.inputElems = lift_b.apply({},[function() {
		return fold(function(v, acc) {return acc.concat(v);},[],arguments);
	}].concat(map(function(w) {return w.behaviors.inputElems;},wdict)));

	this.clickWidgets = [];
	var domobj = {};
	for (var n in cdict) {
		if (cdict.hasOwnProperty(n)) {
			this.events[n] = cdict[n].events.click.snapshot_e(this.behaviors.value);
			domobj[n] = cdict[n].dom;
			this.clickWidgets.push(cdict[n]);
		}
	}
	
	this.dom = domfn(map(function(w) {return w.dom;},wdict),domobj);
	
	if (this.events.value)
		this.behaviors.value = this.events.value.startsWith(this.behaviors.value.valueNow());
}
inheritFrom(ButtonInputWidget,InputWidget);
ButtonInputWidget.prototype.disableMsg = function(msg,disB) {
	this.disabling(disB);
	map(function(cw) {
		cw.disableMsg(msg,disB);
	},this.clickWidgets);
	return this;
}

/* CombinedInputWidget :: [InputWidget] * (. Array DOM -> DOM)
 *
 * Create an input widget as a combination of a numer of other input widgets.
 */
function CombinedInputWidget(wdict,domfn) {
	if (!domfn) domfn = function() {return slice(arguments,0);};
	ButtonInputWidget.apply(this,[wdict,{},function() {return slice(arguments,0);},function(l) {return domfn.apply({},l);}]);
}
inheritFrom(CombinedInputWidget,ButtonInputWidget);


/*
 * Widget mixins
 */

/* modDom :: Widget * (DOM -> DOM) -> Widget
 *
 * Transform the DOM of a widget by passing it through a supplied function.
 */
Widget.prototype.modDom = function(dfn) {
	this.dom = dfn(this.dom);
	return this;
}

/* toTableRow :: Widget * String -> Widget
 *
 * Turn the widget into a row in a 2-column table.
 */
Widget.prototype.toTableRow = function(label) {
	this.dom = TR(TH(label),TD(this.dom));
	return this;
}

/* modValue :: InputWidget * (a -> b) -> InputWidget
 *
 * Take an input widget, and transform its value
 */
InputWidget.prototype.modValue = function(valtrans) {
	this.behaviors.value = lift_b(valtrans,this.behaviors.value);
	return this;
}

/* serverSaving :: InputWidget * (a -> Request) * Boolean -> InputWidget
 * 
 * Produce an InputWidget that saves its value to a server. Takes a function
 * that transforms the widget's value to a request. The InputWidget will
 * display to the user that it is saving whenever its value has changed but the
 * server's response has not yet returned. If replaceValue is true, its value
 * will be replaced by the server's response.
 */
InputWidget.prototype.serverSaving = function(toReqFn,replaceValue) {
	this.events.serverResponse = getFilteredWSO_e(this.behaviors.value.changes().calm_e(500).transform_e(toReqFn));
	var greyB = merge_e(
			this.events.serverResponse.constant_e(false),
			this.behaviors.value.changes().constant_e(true)
		).startsWith(false);
	if (replaceValue) this.behaviors.value = this.events.serverResponse.startsWith(this.behaviors.value.valueNow());
	return this.greyOutable(greyB);
}

/* draftSaving :: InputWidget * Event b * (a * b -> Request) -> InputWidget
 * 
 * Produce a widget such that, whenever a given event occurs, it saves
 * its value to the server. It will also mark widgets as "unsaved" between the
 * time that they change and the time that the event fires.
 */
InputWidget.prototype.draftSaving = function(reqEvt,toReqFn) {
	this.events.serverResponse = getFilteredWSO_e(combine_eb(toReqFn,reqEvt,this.behaviors.value));
	return this.greyOutable(this.events.serverResponse.startsWith(false),true);
}

/* greyOutable :: InputWidget * Behaviour Boolean * Boolean -> InputWidget
 *
 * Make an InputWidget that sometimes tells the user that it has unsaved
 * information. Whenever greyB is true, all of the InputWidget's input elements
 * will be given a red outline, and each will have a small box to it that says
 * "Unsaved".
 *
 * if ieChange is set, then input elements will be marked individually as they change,
 * and will be unmarked whenever greyB changes.
 */
InputWidget.prototype.greyOutable = function(greyB,ieChange) {
	var gdom = this.dom;
	var whenB = greyB;
	var chE = receiver_e();
	if(ieChange)
		whenB = merge_e(chE,greyB.changes().constant_e(false)).startsWith(false);
	this.behaviors.inputElems.transform_b(function(ies) {	
		map(function(elem) {
			if(!inList('greyable',elem.className.split(' '))) {
				var curclasses = elem.className+' greyable';
				if(ieChange) {
					var elemChangeE = $B(elem).changes().constant_e(true)
					var whenB = merge_e(elemChangeE,greyB.changes().constant_e(false)).startsWith(false);
					elemChangeE.transform_e(function(_) {chE.sendEvent(true);});
				}
				else
					whenB = greyB;
				insertValueB(whenB.transform_b(function(_) {return _ ? curclasses+' saving' : curclasses;}),elem,'className');
			}
		},ies);
	});
	insertDomB(whenB.transform_b(function(_) {
				return _ ? DIV({className:'savingIndicator',style:{top:'0',left:document.documentElement.clientWidth-100+'px'}},'Unsaved Data') : SPAN();
	}),document.getElementsByTagName('body')[0],'end');
	return this;
}

/* disabling :: InputWidget * Behaviour Boolean -> InputWidget
 *
 * Make an InputWidget's elements become disabled whenever a given behaviour
 * has the value "true".
 */
InputWidget.prototype.disabling = function(disB) {
	lift_b(function(iels) {
		map(function(elem) {
			insertValueB(disB,elem,'disabled');
		},iels);
	},this.behaviors.inputElems);
	return this;
};

/* withButton :: InputWidget * ClickWidget * (DOM * DOM -> DOM) -> ButtonInputWidget
 *
 * Add a button to a widget, such that the resulting
 * InputWidget's value is updated only when the button is pressed. 
 */
InputWidget.prototype.withButton = function(bwidg,domfn) {
	return new ButtonInputWidget([this],{value:bwidg},
    function(a) { return a; },
    function(a,b) { return domfn(a[0],b.value); }
  );
}	

InputWidget.prototype.withEvtButton = function(bwidg,evtname,domfn) {
	var o = {};
	o[evtname] = bwidg;
	return new ButtonInputWidget([this],o,function(a) {return a;},function(a,b) {return domfn(a[0],b[evtname]);});
}

/* ModListWidget :: 
 *  [a] * 
 *  DOM *
 *  (a * -> InputWidget) *
 *  (-> InputWidget)
 *
 *  Create an addable, deletable, changeable list of objects. Its value is the
 *  list of objects in the list at a given time. The constructor takes:
 *  	-the initial list of objects,
 *  	-The DOM to use as the header,
 *  	-an "empty" ect, used as the basis for newly-created objects,
 *  	-A function that should turn an object into an DelInputWidget.whose DOM
 *  	will be inserted into the ModList table,
 *  	-A function that will create the "addition" widget.
 */
function ModListWidget(initObjs,header,widgetFn,addWidgetFn) {
	Widget.apply(this);

	var nextId = 0;

	var eventsE = consumer_e();
	var registerDel = function(obj) {
		eventsE.add_e(obj.widget.events.del.transform_e(function(del) {
			return {action:'delete',
					id:obj.id};
		}));
	}
	var addWidgetB;
	var additionsE = rec_e(function(arE) {
		addWidgetB = arE.filter_e(noErrors).transform_e(function(aw) {return addWidgetFn();}).startsWith(addWidgetFn());
		var outE = consumer_e();
		addWidgetB.transform_b(function(awb) {outE.add_e(awb.behaviors.value.changes());});
		return outE.transform_e(function(ov) {
			return {action:'add',
				  	value: ov,
					id:nextId++};
		});
	});
	eventsE.add_e(additionsE);
	
	var widgs = map(function(io) {
			var w = {id:nextId++,widget:widgetFn(io)};
			registerDel(w);
			return w;
	},initObjs);

	var widgsB = collect_b(widgs,eventsE.filter_e(noErrors),function(evt,oldWidgs) {
		if(evt.action == 'delete') {
			return filter(function (obj) {return obj.id != evt.id;},oldWidgs);
		}
		else if(evt.action == 'add') {
			oldWidgs.push({id:evt.id,widget:widgetFn(evt.value)});
			registerDel(oldWidgs[oldWidgs.length-1]);
			return oldWidgs;
		}
	});

	this.behaviors.value = switch_b(widgsB.transform_b(function(widgs) {
			return lift_b.apply({},
				[function() {
					return slice(arguments,0);
				}].concat(map(function(widg) {
					return widg.widget.behaviors.value;},widgs)));
	}));
	this.events.errors = eventsE.filter_e(onlyErrors);

	this.dom = TABLEB({className:'key-value modlist'},
			THEADB(header),
			TBODYB(
				widgsB.transform_b(function(ow) {
					return map(function(w) {return w.widget.dom;},ow);}),
				switch_b(addWidgetB.transform_b(function(aw) {return aw.dom instanceof Behaviour ? aw.dom : constant_b(aw.dom);}))));
}
inheritFrom(ModListWidget,InputWidget);

/*
 * Table Generation
 */
function makeColumn(className,headerText,originalCmp,makeTD,customHeader) {
  var sortFn;
  var sortOrder = -1; // unfortunately, we need this for sortFn

  if (!customHeader) {
    sortFn = function(x,y) { return sortOrder * originalCmp(x,y); }; 
  }
  else {
    sortFn =  originalCmp;
  }


  return {
    className: className,
    headerText: headerText,
    customHeaderMaker: function(thisIndex,colB) { 
      if (customHeader) {
        return customHeader;
      }
      else {
        var link = A({href: 'javascript:undefined'},headerText);
        var indicatorB = colB.lift_b(function(colOrder) {
          return (colOrder.length > 0 && colOrder[0].col == thisIndex)
            ? (sortOrder == 1 ? IMG({src: "/static/images/bullet_arrow_up.png"}) 
                              : IMG({src: "/static/images/bullet_arrow_down.png"}))
            : "";
        });

        return {
          sortE: clicks_e(link).lift_e(function() {
            sortOrder *= -1;
            return true;
          }),
          changeE: receiver_e(), // zero_e
          dom: SPANB({style: { whiteSpace: "nowrap" } },link,indicatorB)
        };
      }
    },
    sortFn: sortFn,
    makeTD: makeTD
  };
};

function PaginatorWidget(numPapersB,classPrefix,initSize,initPage) {
	Widget.apply(this);
	function numsToList(nums) {
		return map(function(n) {return {k:n,v:''+n};},nums);
	}
	function makeSizeChooser(numPapers,initVal) {
		return new LinkListWidget(
				filter(function(_) {return _.k < numPapers},numsToList([5,10,25,50,75,100,200,300])).concat([{v:'All',k:numPapers}]),
				Math.min(initVal,numPapers)
		);
	}
	var sizeChooserB = collect_b(makeSizeChooser(numPapersB.valueNow(),initSize),numPapersB.changes(),function(newPapers,oldChooser) {
		var oldchoice = oldChooser.behaviors.value.valueNow();
		if (!inList(oldchoice,[5,10,25,50,75,100,200,300]))
			if(oldchoice < initSize)
				oldchoice = initSize;
			else
				oldchoice = newPapers;
		return makeSizeChooser(newPapers,oldchoice);
	});
	
	var scChoiceB = switch_b(sizeChooserB.transform_b(function(sc) {return sc.behaviors.value;}));
	var scDomB = switch_b(sizeChooserB.transform_b(function(sc) {return sc.dom;}));

	var numPagesB = lift_b(function(s) {var n = numPapersB.valueNow(); return (n ? Math.max(1,Math.ceil(n / s)) : 1);},scChoiceB);

	var ipSat = false;
	var realInitPage = 1;
	if(numPagesB.valueNow() >= initPage) {ipSat = true; realInitPage = initPage;}
	var pageChooserB = collect_b(
			new LinkListWidget(numsToList(range(1,numPagesB.valueNow()+1)),realInitPage,true),
			numPagesB.changes(),
			function(numPages,oldChooser) {
				var newPage = Math.min(oldChooser.behaviors.value.valueNow(),numPages);
				if(!ipSat && numPages >= initPage) {
					ipSat = true;
					newPage = initPage;
				}
				return new LinkListWidget(numsToList(range(1,numPages+1)),newPage,true);
			}
	);
	var pcdB = switch_b(pageChooserB.transform_b(function(pc) {return pc.dom;}));

	this.extraPrev = switch_b(pageChooserB.transform_b(function(pc) {return pc.makePrevBtn();}));
	this.extraNext = switch_b(pageChooserB.transform_b(function(pc) {return pc.makeNextBtn();}));

	this.dom = lift_b(function(pcd,scd,np) {
		return DIV({className:classPrefix+'-paginator'},
				DIV({className:classPrefix+'-movement'},'Page: ',
					pcd),
				DIV({className:classPrefix+'-count'},'Show ',
					scd,' of ',''+np));
	},pcdB,scDomB,numPapersB);
	this.behaviors.size = scChoiceB.changes().filterRepeats().startsWith(scChoiceB.valueNow());
	this.behaviors.page = switch_b(pageChooserB.transform_b(function(pc) {return pc.behaviors.value;})).changes().filterRepeats().startsWith(1);
}
inheritFrom(PaginatorWidget,Widget);

function HeaderSortWidget(columns,initSort) {
	Widget.apply(this);


	var headerClicksE = consumer_e();
	
	var tableHeadCols = [];
	var defaultCol = 0;
	
  if(!initSort) initSort = [{col:defaultCol,order:1}];
	var colB = collect_b(initSort,headerClicksE,function(newcol,cols) {
    return [{ col: newcol, order: 1 }];
		if (newcol == defaultCol) {
	    return [{col:defaultCol,order:1}];
    }
		else {
			for(var i=0;i<cols.length;i++)
				if(cols[i].col == newcol) break;
			if (i == cols.length)
				return [{col:newcol,order:1}].concat(cols);
			else if (i == 0) {
				return cols;
			}
			else {
				cols.splice(i,1);
				return [{col:newcol,order:1}].concat(cols);
			}
		}
  });

  this.behaviors.cols = colB;

 
  columns.eachWithIndex(function(i,column) {
    var header = column.customHeaderMaker(i,colB);
    header.sortE.lift_e(function(_) { headerClicksE.sendEvent(i); });

    header.changeE.lift_e(
      function(_) { headerClicksE.sendEvent(i); });

		
    tableHeadCols.push(THB({className:column.className,scope:'col'},
                           header.dom));
		if(column.defaultSort) defaultCol = i;
    
  });

	this.behaviors.sortFn = this.behaviors.cols.transform_b(function(cols) {
		return function(a, b) {
			for(var i=0;i<cols.length;i++) {
				var j = columns[cols[i].col].sortFn(a,b);
				if(j) return j*cols[i].order;
			}
			return 0;
		}
	});
	this.dom = THEADB(TRB(tableHeadCols));
}
inheritFrom(HeaderSortWidget,Widget);

function TableWidget(papersB,classPrefix,columns,filterB,tableTitle) {
	Widget.apply(this);
	if(!tableTitle) tableTitle = '';
  if (!filterB) {
    filterB = function() { return true; };
  }
	
	var sorter = this.makeSorter(columns);
	
	this.behaviors.showPapers = lift_b(function(papers,sortFn,filterFn) {
		return filter(filterFn,papers.sort(function(a,b) {return sortFn(a.getObj(),b.getObj());}));
	},papersB,sorter.behaviors.sortFn,filterB);

	var numPapersB = this.behaviors.showPapers.transform_b(function(sp) {return fold(function(v, acc) {return acc+1;},0,sp);}); // wtf: dot-length maybe?
	
	var paginator = this.makePaginator(numPapersB,classPrefix+'-list');

	this.behaviors.cols = sorter.behaviors.cols;
	this.dom = this.makeDom(tableTitle,paginator,sorter,classPrefix,this.behaviors.showPapers);
}
inheritFrom(TableWidget,Widget);

TableWidget.prototype.makePaginator = function(numPapersB,cl) {return new PaginatorWidget(numPapersB,cl,10,1)};
TableWidget.prototype.makeSorter = function(columns) {return new HeaderSortWidget(columns);}
TableWidget.prototype.makeDom = function(ttl,paginator,sorter,classPrefix,showPapersB) {
	return DIVB({className:classPrefix+'-list'},
		ttl,
		paginator.dom,
		TABLEB(
			{className:classPrefix+'-list-table'},
			sorter.dom,
			TBODYB(lift_b(function(showPapers,page,size) {
				return fold(function(v,acc) {
						return acc.concat(v.getDoms());},[],
				slice(showPapers,Math.min((page-1)*size,showPapers.length),Math.min(page*size,showPapers.length)));
			},showPapersB,paginator.behaviors.page,paginator.behaviors.size)),
		DIVB({className:classPrefix+'-bottom',style:{textAlign:'right',padding:'0.5em 1em'}},paginator.extraNext)));
};

/*
 * Dealing with Requests
 */

function genRequest(obj) {
	if(obj.asynchronous == undefined)
		obj.asynchronous = true;
	if(obj.serviceType == undefined)
		obj.serviceType = 'jsonLiteral';
	if(obj.request == undefined)
		obj.request = 'post';
	return obj;
}
function filterExceptions(objE,exceptsE) {
	if(exceptsE) exceptsE.add_e(objE.filter_e(function(w) {return ((w instanceof Object) && (w.exception == 'exception'));}));
	return objE.filter_e(function(w) {return (!(w instanceof Object) || (w.exception != 'exception'));});
}

function getFilteredWSO_e(queryE,exceptsE) {
	return filterExceptions(getWebServiceObject_e(queryE),exceptsE);
}
function iframeLoad_e(iid,exceptsE) {
	var theIframe = getObj(iid);
	var lv = extractEvent_e(theIframe,'load')
		.filter_e(function(_) {
      var location = new String(window.frames[iid].location);
      return !location.match(/static\/blank\.html$/);
    })
		.transform_e(function(_) {
			var child = window.frames[iid].document.body.childNodes[0];
			window.frames[iid].location = '/static/blank.html'; 
                        if(child) {
			  return child.innerHTML.parseJSON();
                        } else {
                          return {value: {error: 'Empty iframe'}};
                        }
		});
	return filterExceptions(lv,exceptsE);
}
function captureServerExcepts() {
	var ogfw = getFilteredWSO_e;
	var oil = iframeLoad_e 
	var exceptsE = consumer_e();
	getFilteredWSO_e = function(q) {return ogfw(q,exceptsE);}
	iframeLoad_e = function(q) {return oil(q,exceptsE);}
	exceptsE.transform_e(function(e) {
		if(e.value != 'expired' && e.value != 'denied')
			window.alert("Server-Side Error: "+e.value);
	});
	return exceptsE;
}

function WidgetB(widgetTypeB /*, args */) {
	Widget.apply(this);
	var wargs = slice(arguments,0);
	var widgetB = lift_b.apply({},
		[function() {var w={}; arguments[0].apply(w,slice(arguments,1)); return w;}]
		.concat(wargs)
	);
	var wn = widgetB.valueNow();
	for (beh in wn.behaviors) {
		if (wn.behaviors[beh] instanceof Behaviour)
			this.behaviors[beh] = switch_b(lift_b(function(w,bn) {return w.behaviors[bn];},widgetB,beh));
	}
	for (evt in wn.events) {
		if (wn.events[evt] instanceof Event) {
			this.events[evt] = switch_b(lift_b(function(w,en) {return w.events[en].startsWith(undefined);},widgetB,evt)).changes()
				.filter_e(function(e) {return e !== undefined;});
		}
	}
	this.dom = switch_b(widgetB.transform_b(function(w) {return (w.dom instanceof Behaviour? w.dom : constant_b(w.dom));}));
}
inheritFrom(WidgetB,Widget);

function InputWidgetB(widgetTypeB /*, args */) {
	WidgetB.apply(this,slice(arguments,0));
}
inheritFrom(InputWidgetB,InputWidget);

