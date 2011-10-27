/* demo.js : Functionality for "Demo-ing" Javascript applications.

 * Say you have an application that you want to show off to potential
 * users.  Rather than passive screenshots, you'd like them to sample
 * the actual, running application.  But you'd like to do it while
 * watching over the shoulders, saying, "Click here" and "Did you see
 * that there?"

 * That's what this, the Flapjax Demo Tool, lets you do.  You can run
 * your application in a managed setting, allowing the user to
 * interact and experiment with your interface while you guide them.

 * In what follows, we'll need separate names for three programs.  The
 * first is the program being demo'ed; we'll call this the
 * Application.  The second is this support library that enables
 * demos; we'll call it the Manager.  Finally there is the actual demo
 * program that you write to show off the Application; we'll call
 * that, obviously, the Demo.

 * You will have to modify your Application slightly, but we've worked
 * hard to make sure you need to modify it *very* slightly.  All the
 * Application needs to do is expose the interesting events to the
 * Manager through the interface described below.  The Manager
 * consists of a state machine that changes states based on these
 * events. Each state has accompanying text that guides the user
 * through the application.

 * To expose events to the Manager, every page of the Application that
 * you care to include in the demo must add a "startDemo" function to
 * its document object at load time. This function takes a callback,
 * which the underlying application must call whenever an action
 * occurs. The callback takes one argument: an object that includes an
 * "action" attribute, which contains the name of the action that just
 * occured.  This object is passed by the Manager to its state
 * machine.

 */

/* State :: String x String -> State

 * Models a state in a "demo" state machine.  States have transitions
 * to other states, which occur on certain actions.  Each state has a
 * name, as well as a blurb that can be displayed alongside the
 * appropriate state in the Application.

 * States also have "highlight actions".  If the Demo invokes
 * setHighlight, then when the state's blurb is displayed, a special
 * link will be displayed alongside.  This link, when clicked, will
 * run a designated function (hlOn) that is meant to be used for
 * highlighting parts of the page to which the user's attention should
 * be drawn.  The accompanying hlOff function, which should reverse
 * whatever changes have been made, is called when leaving the state.

 */
function State(name,text) {
	var state = this;
	this.name = name;
	this.text = text;
	this.transitions = [];
	this.hlLink = A({href:'javascript:undefined'},'[show me what to click]');
	this.hlLink.onclick = function() {if(state.hlOn) state.hlOn();};

	/* State Methods */

	/* addTransition :: State x (Action -> Boolean) -> undefined

	 * Add a new state transition to this state.  When the Demo invokes
	 * getNextState, all the transitions for this state are evaluated.
	 * The state that is returned is the one associated with the first
	 * transition to return "true".
	 */
	this.addTransition = function(toState,predicate) {
		this.transitions.push({pred:predicate,to:toState});
	}

	/* setHighlight :: Function x Function -> undefined

	 * setHighlight takes two zero-arity functions, one to turn
	 * highlighting on and the other to turn it off.  The first one is
	 * called when the user presses the "[show me what to click]" link;
	 * the second is called by getNextState() when transitioning to a new
	 * state.  (Why?  Because the next "state" may continue to use the
	 * same screen, and you don't usually want the highlighting from one
	 * state of the demo to persist into the next.  If you do want to
	 * leave the highlighting on, the second function argument simply
	 * needs to do nothing.)
	 */
	this.setHighlight = function(on,off) {
		this.hlOn = on;
		this.hlOff = off;
	}

	/* getNextState :: Action -> State

	 * getNextState performs a state transition by finding out which
	 * predicate (of the ones added by addTransition) matches the given
	 * action.  If a predicate matches, getNextState will call the current
	 * state's hlOff function (if one exists) and return the new state.
	 * If no predicates match, getNextState will return the current state
	 * and not call the hlOff function.
	 */
	this.getNextState = function(newAct) {
		var newState = state;
		map(function(st) {
			if(st.pred(newAct)) {
				newState = st.to;
				if(state.hlOff) state.hlOff();
			}
		},state.transitions);
		return newState;
	}

	/* getDisplayDom :: (no arguments) -> DOM 
	 *
	 * getDisplayDom returns the DOM representation of this state, which
	 * consists of the state's blurb and (if this state does any highlighting)
	 * the "[show me what to click]" link. You can then insert this DOM
	 * representation into an appropriate place using code like:
	 *
	 * insertDomB(currentStateB.transform_b(function(curState) {
	 *         return curState.getDisplayDom();
	 *     }), some_dom);
	 */
	this.getDisplayDom = function() {
		return this.hlOn ? SPAN(this.text,BR(),BR(),this.hlLink) : SPAN(this.text);
	};
}

/* StateMachine :: [State] x String x Event Action -> StateMachine
 * Create a state machine: a group of states connected by transitions.
 */
function StateMachine() {
	this.states = {};
	this.initState = null;
	
	/* StateMachine Methods */

	/* createState :: String x String -> State 
	 *
	 * createState creates a new state by invoking the State constructor with
	 * its arguments, and then adds the new state to the state machine.
	 * */
	this.createState = function(name, blurb) {
		this.states[name] = new State(name,blurb);
		return this.states[name];
	};

	/* setInitState :: String -> State
	 *
	 * setInitState sets the inital state of the state machine to the state
	 * with a given name. It then returns that state. You must call
	 * setInitState before calling runMachine.
	 */
	this.setInitState = function(isname) {
		this.initState = this.states[isname];
		return this.initState;
	};

	/* runMachine :: Event Action -> Behavior State
	 *
	 * runMachine "executes" the state machine by taking a series of actions
	 * (as an event stream) and returning a time-varying value representing
	 * the current state at a given time.
	 */
	this.runMachine = function(eventsE) {
		return eventsE.collect_e(this.initState,function(evt,state) {
			return state.getNextState(evt);
		}).startsWith(this.initState);
	};
}

/* chAct :: String -> (Action -> Boolean)
 *
 * Much of the time, you will want your state transitions to happen whenever
 * an action happens whose "action" attribute matches a given value; for
 * instance, you might have a transition triggered by any "newpage" actions.
 * 
 * chAct is a convenience function that creates a predicate matching all
 * actions with a given name. That way, instead of writing
 *
 * someState.addTransition(otherState,
 *     function(a) {return a.action == 'newpage';});
 *
 * you can just write
 *
 * someState.addTransition(otherState,chAct('newpage'));
 */
function chAct(name) {
	return function(act) {return act.action == name;};};

/* runDemo :: HTMLIFrameElement x StateMachine -> Behavior State
 *
 * runDemo binds a state machine to an iframe on the page. Whenever
 * a new page loads in the iframe, its startDemo function will be called
 * (as per the "demo protocol" above). runDemo sends that page's actions 
 * (along with a special "newpage" action that occurs immediately
 * on page loads) to the state machine, and returns a behaviour
 * representing the current state.
 */
function runDemo(iframe,statemach) {
	var pageChangeE = extractEvent_e(iframe,'load');
	var pageEventsE = consumer_e();
	pageChangeE.transform_e(function(pc) {
		if(window.frames[iframe.name].document.startDemo)
			window.frames[iframe.name].document.startDemo (
				function(evt) {pageEventsE.sendEvent(evt);}
			);
	});
	var eventsE = merge_e(pageEventsE,pageChangeE.constant_e({action:'newpage',src:iframe.src}));
	return statemach.runMachine(eventsE);
}
