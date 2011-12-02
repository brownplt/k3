/* This file runs from glogin.html, which is served upon a successful login
   via google.  It depends on globals provided by the server:

    STATION : Serialized cap to get the account's station
    MAKESTASH : Serialized cap to create stashes for this account
    EMAIL : The email from the openID provider
    CLIENTKEY : The secret shared with the opening iframe to prevent spoofing
*/

$(function() {
  window.opener.login(JSON.stringify(loginInfo));
  window.close();
});
