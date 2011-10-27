Array.prototype.foldl = function(init,f) {
  var arr = this;
  var result = init;
  for (var i = 0; i < arr.length; i++) {
    result = f(result,arr[i])
  }
  return result;
};

Array.prototype.map = function(f) { 
  var src = this;
  var dest = [ ];
  for (var i = 0; i < src.length; i++) { dest.push(f(src[i]));  }
  return dest;
}


Array.prototype.each = function(f) {
  var arr = this;
  for (var i = 0; i < arr.length; i++) {
    f(arr[i]);
  }
};

Array.prototype.eachWithIndex = function(f) {
  var arr = this;
  for (var i = 0; i < arr.length; i++) {
    f(i,arr[i]);
  }
};

Array.prototype.ormap = function(f) {
  var arr = this;
  for (var i = 0; i < arr.length; i++) { 
    var r = f(arr[i]);
    if (r !== false) { return r; }
  }
  return false;
};

function clicks_e(elt) { 
  return extractEvent_e(elt,'click');
};

function orFilter(f,g) {
  return function(x) {
    return f(x) || g(x);
  };
};

// composeFilters :: (a -> Bool) * (a -> Bool) -> a -> Bool
function composeFilters(f,g) {
  return function(x) {
    return f(x) && g(x);
  }
}

function compose(f,g) { 
  return function(x) { return f(g(x)); };
};

function hasLettersBy(writerPatterns) {
  return function(applicant) {
    return applicant.info.refletters.ormap(function(letter) {
      return writerPatterns.ormap(function(pattern) {
        return (letter.name.toLowerCase().indexOf(pattern.toLowerCase()) >= 0 ||
                letter.email.toLowerCase().indexOf(pattern.toLowerCase()) >= 0);
      });
    });
  }
}

function hasInstitutionWithName(namePatterns) {
  return function(applicant) {
    return applicant.info.institutions.ormap(function(inst) {
      return namePatterns.ormap(function(pattern) {
	return inst.name.toLowerCase().indexOf(pattern.toLowerCase()) >= 0;
      });
    });
  }
}


// Removes some silly linear arrays and replaces them with maps from DB ids
// to values.
function parseBasic(basicInfo) {
  var positionMap = { };
  for (var ix = 0; ix < basicInfo.positions.length; ix++) {
    positionMap[basicInfo.positions[ix].id] = basicInfo.positions[ix];
  }
  basicInfo.positions = positionMap;
  return basicInfo;
}

function getBasicInfoSE(infoE) {
	return infoE.transform_e(function(bi) {
		bi.svcs = {};
		bi.svnum = {};
		map(function(sc) {
		    map(function(sv) {
			bi.svcs[sv.id] = sc;
			bi.svnum[sv.id] = sv.number;},sc.values);},bi.scores);
		return bi;
	});
}
function getAuthE(onLoadTimeE,cookie) {
	return getFilteredWSO_e(onLoadTimeE.constant_e(genRequest(
		{url:'Auth/currentUser',fields:{cookie:cookie}})));
}
function setHeadAndTitle(bi,pageName,buttons) {
	insertDom(H1({id:'ptitle'},
		buttons ? DIV({className:'buttons'},buttons) : '',
		IMG({src:'image-header',alt:bi.info.name,id:'header'}),
		IMG({src:'image-logo',alt:'',id:'logo'}),
		IMG({src:'image-resume',alt:'resume',id:'resume'})
	),'ptitle');
	document.title = pageName + ' - ' + bi.info.name;
}
function showWebsite(wsstr) {
	if(wsstr.indexOf('http://') != 0)
		if(wsstr.indexOf('http') == 0)
			return wsstr.replace(/http[^\/]*\//,'http://');
		else
			return 'http://'+wsstr;
	else
		return wsstr;
}

function precision(num,decimals) {
	var ret = '' + (num - (num % 1)) + '.';
	num = (num % 1)*10;
	var rfactor = 1;
	for(var i=0; i<decimals; i++) rfactor /= 10;
	if (((num / rfactor) % 1) >= .5) num += rfactor;
	for(;decimals;decimals--) {
		var nd = (num - (num % 1));
		num = (num % 1) * 10;
		ret += nd;
	}
	return ret;
}

function errorLog(str) {
	if(window.console) {
	  console.log(str);
	}
}
