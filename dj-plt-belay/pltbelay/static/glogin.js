/* This file runs from glogin.html, which is served upon a successful login
   via google.  It depends on globals provided by the server:

    STATION : Serialized cap to get the account's station
    MAKESTASH : Serialized cap to create stashes for this account
    CLIENTKEY : The secret shared with the opening iframe to prevent spoofing
*/

$(function() {
  // The belay-frame that opened the glogin window
  var target = window.opener;

  $.pm({
    target: target,
    type: 'login',
    data: {
      loginInfo: {
        station: STATION,
        makeStash: MAKESTASH,
      },
      clientkey: CLIENTKEY
    },
  });

  window.close();
});
