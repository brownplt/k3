from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import time
import httplib, urllib


# Constants, to be updated as the UI changes
BELAY_DOMAIN = "localhost:8080"
BELAY_URL = "http://localhost:8080/belay-frame.html"
GOOGLE_LOGIN_LINKTEXT = "Log in with Google"
GOOGLE_LOGIN_BUTTONID = "submit-login"

CREATE_PLT_LINKTEXT = "Log in with Brown Apps"
CREATE_PLT_USERFIELDID = "username"
CREATE_PLT_PW1FIELDID = "password1"
CREATE_PLT_PW2FIELDID = "password2"
CREATE_PLT_BUTTONID = "submit"


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


# Log in as google user, and check for the cookie
def google_login_test(driver):
  driver.get(BELAY_URL)

  link = driver.find_element_by_link_text(GOOGLE_LOGIN_LINKTEXT)
  if link == None:
    error(driver, "google_login_test error: couldnt find login link with text: " + GOOGLE_LOGIN_LINKTEXT)
  link.click()

  login_button = driver.find_element_by_id(GOOGLE_LOGIN_BUTTONID)
  if login_button == None:
    error(driver, "google_login_test error: couldnt find login button with id: " + GOOGLE_LOGIN_BUTTONID)

  login_button.click()
  if not session_cookie_exists(driver):
    error(driver, "google_login_test fail: couldn't find session cookie")

  driver.delete_all_cookies()
  print "google_login_test passed"


def create_pltaccount_test(driver):
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

    clearall([username_field, pw1_field, pw2_field])

  def shortpw_test():
    username_field.send_keys("joe")
    pw1_field.send_keys("bla")
    pw2_field.send_keys("bla")
    submit.click()

    alert = driver.switch_to_alert()
    alert.accept()

    if session_cookie_exists(driver):
      error(driver, "create_plt_test fail: short pw")
    clearall([username_field, pw1_field, pw2_field])

  def goodpw_test():
    username_field.send_keys("joe")
    pw1_field.send_keys("password123")
    pw2_field.send_keys("password123")
    submit.click()

    if not account_exists(driver, "joe"):
      error(driver, "create_plt_test fail: good pw")
    clearall([username_field, pw1_field, pw2_field])

  driver.get(BELAY_URL)

  link = driver.find_element_by_link_text(CREATE_PLT_LINKTEXT)
  if link == None:
    error(driver, "create_plt_test error: couldn't find login link with text " + CREATE_PLT_LINKTEXT)
  link.click()

  username_field = driver.find_element_by_id(CREATE_PLT_USERFIELDID)
  if username_field == None:
    error(driver, "create_plt_test error: couldn't find username field")

  pw1_field = driver.find_element_by_id(CREATE_PLT_PW1FIELDID)
  if pw1_field == None:
    error(driver, "create_plt_test error: couldn't find password1 field")

  pw2_field = driver.find_element_by_id(CREATE_PLT_PW2FIELDID)
  if pw2_field == None:
    error(driver, "create_plt_test error: couldn't find password2 field")

  submit = driver.find_element_by_id(CREATE_PLT_BUTTONID)
  if submit == None:
    error(driver, "create_plt_test error: couldn't find submit button")

  mismatch_test()
  shortpw_test()
  goodpw_test()

  print "create_pltaccount_test passed"


def main():
  driver = webdriver.Firefox()
  google_login_test(driver)
  create_pltaccount_test(driver)
  driver.quit()
  

if __name__ == "__main__":
    main()
