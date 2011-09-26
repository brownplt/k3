from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import time
import httplib, urllib


# Constants, to be updated as the UI changes
BELAY_DOMAIN = "localhost:8080"
BELAY_URL = "http://localhost:8080/belay-frame.html"
GOOGLE_LOGIN_ID = "glogin"
GOOGLE_LOGIN_BUTTONID = "submit-login"

CREATE_PLT_ID = "createplt"
CREATE_PLT_USERFIELDID = "username"
CREATE_PLT_PW1FIELDID = "password1"
CREATE_PLT_PW2FIELDID = "password2"
CREATE_PLT_BUTTONID = "submit"

LOGIN_PLT_UFIELD = "username"
LOGIN_PLT_PFIELD = "password"
LOGIN_PLT_SUBMIT = "submit"


def error(driver, msg):
  print msg
  driver.quit()
  exit(1)


def clearall(elts):
  for e in elts:
    e.clear()


def session_cookie_exists(driver):
  cookies = driver.get_cookies()
  if len(cookies) == 0:
    return False
  for c in cookies:
    if c.has_key("name") and c["name"] == "session":
      return True
  return False


def account_exists(driver, username):
  params = urllib.urlencode({"username" : username})
  conn = httplib.HTTPConnection(BELAY_DOMAIN)
  conn.request("POST", "/check_uname", params)
  response = conn.getresponse()
  r = response.read()
  return r == "Taken"


def get_elt(driver, ident):
  try:
    link = driver.find_element_by_id(ident)
    return link
  except:
    error(driver, "couldn't find element: " + ident)
    return None


# Log in as google user, and check for the cookie
def google_login_test(driver):
  driver.get(BELAY_URL)
  
  link = get_elt(driver, "glogin")
  link.click()

  login_button = get_elt(driver, GOOGLE_LOGIN_BUTTONID)
  login_button.click()

  if not session_cookie_exists(driver):
    error(driver, "google_login_test fail: couldn't find session cookie")

  driver.delete_all_cookies()
  print "google_login_test passed"


def create_pltaccount_test(driver):
  def clearall():
    username_field.clear()
    pw1_field.clear()
    pw2_field.clear()

  def create_account(username, pw1, pw2):
    username_field.send_keys(username)
    pw1_field.send_keys(pw1)
    pw2_field.send_keys(pw2)
    submit.click()
  
  def mismatch_test():
    username_field.send_keys("joe")
    pw1_field.send_keys("blablablabla1")
    pw2_field.send_keys("blablablabla2")
    submit.click()

    alert = driver.switch_to_alert()
    alert.accept()

    if session_cookie_exists(driver):
      error(driver, "create_plt_test fail: mismatched pws")
    clearall()

  def shortpw_test():
    username_field.send_keys("joe")
    pw1_field.send_keys("bla")
    pw2_field.send_keys("bla")
    submit.click()

    alert = driver.switch_to_alert()
    alert.accept()

    if session_cookie_exists(driver):
      error(driver, "create_plt_test fail: short pw")
    clearall()

  def goodpw_test():
    username_field.send_keys("joe")
    pw1_field.send_keys("password123")
    pw2_field.send_keys("password123")
    submit.click()

    if not account_exists(driver, "joe"):
      error(driver, "create_plt_test fail: good pw")

  driver.get(BELAY_URL)

  #link = get_link(driver, CREATE_PLT_LINKTEXT)
  link = get_elt(driver, CREATE_PLT_ID)
  link.click()

  username_field = get_elt(driver, CREATE_PLT_USERFIELDID)
  pw1_field = get_elt(driver, CREATE_PLT_PW1FIELDID)
  pw2_field = get_elt(driver, CREATE_PLT_PW2FIELDID)
  submit = get_elt(driver, CREATE_PLT_BUTTONID)

  mismatch_test()
  shortpw_test()
  goodpw_test()

  print "create_pltaccount_test passed"


def login_pltaccount_test(driver):
  driver.delete_all_cookies()
  driver.get(BELAY_URL)

  link = get_elt(driver, "loginplt")
  link.click()

  ufield = get_elt(driver, LOGIN_PLT_UFIELD)
  pfield = get_elt(driver, LOGIN_PLT_PFIELD)
  submit = get_elt(driver, LOGIN_PLT_SUBMIT)

  ufield.send_keys("joee")
  pfield.send_keys("password123");
  submit.click()
  if session_cookie_exists(driver):
    error(driver, "login_pltaccount_test fail: logged in with bad uname")
  ufield.clear()
  pfield.clear()

  ufield.send_keys("joe")
  pfield.send_keys("password1233")
  submit.click()
  if session_cookie_exists(driver):
    error(driver, "login_pltaccount_test fail: logged in with bad pw")
  ufield.clear()
  pfield.clear()

  ufield.send_keys("joe")
  pfield.send_keys("password123")
  submit.click()
  if not session_cookie_exists(driver):
    error(driver, "login_pltaccount_test fail: couldn't log in")

  print "login_pltaccount_test passed"


def main():
  driver = webdriver.Firefox()
  driver.delete_all_cookies()
  google_login_test(driver)
  create_pltaccount_test(driver)
  login_pltaccount_test(driver)
  driver.quit()
  

if __name__ == "__main__":
    main()
