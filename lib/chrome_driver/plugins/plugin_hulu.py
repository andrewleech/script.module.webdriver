__author__ = 'corona'
import os
import json
from selenium.webdriver.common.keys import Keys

PLUGIN_NAME="hulu"

class PLUGIN(object):
    BASE_MENU_URL = "https://m.hulu.com/menu/hd_main_menu?show_id=0&dp_id=huludesktop&package_id=2&page=1"
    POLL_RATE = 5 * 60

    def __init__(self, server):
        self.menus = {}
        self.server = server
        self.browser = self.server.browser

    def poll(self):
        pass
        # menus = self.getMenus()
        # self.menus = menus


    def login(self, login, password, cookiefile = None):
        login_url = "https://www.hulu.com/about"

        if 'hulu.com' not in self.browser.current_url:
            self.browser.get(login_url)

        def _is_logged_in():
            return len(self.browser.find_elements_by_class_name('logout')) > 0

        status = _is_logged_in()
        if not status:
            try:
                if cookiefile and os.path.exists(cookiefile):
                    with open(cookiefile, 'r') as fp:
                        cookies = json.load(fp)
                        for cookie in cookies:
                            self.browser.add_cookie(cookie)
                        self.browser.get(login_url)
                        status = _is_logged_in()

                if not status:
                    log_in_btn = self.browser.find_element_by_link_text("LOG IN")
                    log_in_btn.click()
                    try:
                        dummy_login_input = self.browser.find_elements_by_name('dummy_login').pop(0)
                        dummy_login_input.click()
                    except IndexError as ex: pass
                    login_input = self.browser.find_elements_by_id('login').pop(0)
                    password_input = self.browser.find_elements_by_id('password').pop(0)
                    login_input.click()
                    login_input.send_keys(login)
                    password_input.send_keys(password)
                    password_input.send_keys(Keys.ENTER)

                    self.browser.get(login_url)
                    status = _is_logged_in()

                if status and cookiefile:
                    try:
                        os.makedirs(os.path.dirname(cookiefile))
                    except OSError: pass
                    with open(cookiefile, 'w') as fp:
                        json.dump(self.browser.get_cookies(), fp)
            except IndexError as ex:
                status = ex
            except Exception as ex:
                status = ex
        return status

    def getMenus(self):
        browser = self.server.browser
        res = self.server.getNoJs(self.BASE_MENU_URL)


