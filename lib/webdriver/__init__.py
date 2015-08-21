__author__ = 'corona'

import os
import re
import imp
# import sys
# import time
# import types
import base64
import requests
import platform
import threading
from collections import namedtuple

from concurrent.futures import ThreadPoolExecutor
import _include as includes
from _utils import *

import js_fn

# lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# if lib_path not in sys.path:
#     sys.path.append(lib_path)
# chromedriver_path = os.path.join(os.path.dirname(__file__))
# if chromedriver_path not in sys.path:
#     sys.path.append(chromedriver_path)

resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','resources'))

import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# TODO move to settings
BROWSER_CHROME = "chrome"
BROWSER_FIREFOX = "firefox"
BROWSER_IE = "internetexplorer"

_use_browser = BROWSER_CHROME


if _use_browser == BROWSER_CHROME:
    if osWin:
        chrome_driver_path= os.path.join(os.path.dirname(__file__),'bin','win32')
    elif osOSX:
        chrome_driver_path= os.path.join(os.path.dirname(__file__),'bin','osx')
    elif osLinux:
        chrome_driver_path= os.path.join(os.path.dirname(__file__),'bin','linux')
    else:
        raise NotImplementedError("Dont' know platform: " % str(sys.platform))

    if chrome_driver_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + chrome_driver_path

    from selenium.webdriver.chrome.options import Options as ChromeOptions

def get_ps():
    ps = subprocess.check_output(["ps","-xf"])
    pid = None
    pslines = ps.splitlines()
    ps_entry = namedtuple('ps_entry', pslines[0].strip().split())
    ps_entries = [ ]
    for line in pslines[1:]:
        spline = line.strip().split()
        spline = spline[:7] + [" ".join(spline[7:])]
        ps_entries.append(ps_entry(*spline))
    return ps_entries


class Browser(object):
    _browser = None
    def __init__(self):
        # Check if webdriver instance running

        self.browser_lock = threading.Lock()

        self.plugins = {}
        self.background = ThreadPoolExecutor(max_workers=1)

        if _use_browser == BROWSER_CHROME:
            self._chrome_options = ChromeOptions()
            self._chrome_options.add_argument("disable-web-security") # We can't do the ajax get/post without this option, thanks to CORS
            #self._chrome_options.add_argument("--disable-bundled-ppapi-flash") # Everyone who's anyone hates flash... especially because selenium can't control it!
            #self._chrome_options.add_argument('--kiosk')
        else:
            raise NotImplementedError("Currently only supports chrome")

        self._monitoring_target = None
        self._monitoring_parent = None

    @property
    def browser(self):
        """
        This will load chrome and webdriver the first time it's hit, then
        return the cached instance forever after.
        :return: webdriver.Chrome
        """
        if self._browser is None:
            port = 47238
            if _use_browser == BROWSER_CHROME:
                # self._browser = webdriver.Chrome(chrome_options=self._chrome_options, port=47238)
                for _ in range(2):
                    try:
                        self._browser = selenium.webdriver.Remote("http://127.0.0.1:%d"%port, desired_capabilities=self._chrome_options.to_capabilities())
                        break
                    except Exception as ex:
                        # TODO check the kind of exception above
                        # TODO add args to keep it running in background
                        subprocess.Popen([os.path.join(chrome_driver_path, 'chromedriver'), '--port=%d'%port], close_fds=True)
                        sleep(1)
                if not self._browser:
                    raise Exception("Can't start webdriver")
                # self._browser.get("file://%s/black.htm" % resources_path.replace('\\','/'))
                # self.send_browser_to_back()
        return self._browser

    def close(self):
        with self.browser_lock:
            self.browser.close()

    def show_control_window(self, jsTargetBy = None, jsTarget = None, keymap = None):
        # blocking
        self.jsTargetBy = jsTargetBy
        self.jsTarget = jsTarget
        try:
            import control_window
            controlWindow = control_window.window(self, self.jsTargetBy, self.jsTarget, keymap)
            controlWindow.doModal()
        except ImportError: pass

    def bring_browser_to_front(self):
        pid = self.pid()
        self.bring_proc_to_front(pid)

    @staticmethod
    def send_browser_to_back():
        pid = os.getpid()
        Browser.bring_proc_to_front(pid)

    @staticmethod
    def bring_proc_to_front(pid):
        if osLinux:
                # Ensure browser is active window
            def currentActiveWindowLinux():
                name = ""
                try:
                    # xprop -id $(xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2) _NET_WM_NAME
                    current_window_id = check_output(['xprop', '-root', '32x', '\'\t$0\'', '_NET_ACTIVE_WINDOW'])
                    current_window_id = current_window_id.strip("'").split()[1]
                    current_window_name = check_output(['xprop', '-id', current_window_id, "WM_NAME"])
                    if "not found" not in current_window_name and "failed request" not in current_window_name:
                        current_window_name = current_window_name.strip().split(" = ")[1].strip('"')
                        name = current_window_name
                except OSError:
                    pass
                return name

            def findWid():
                wid = None
                match = re.compile("(0x[0-9A-Fa-f]+)").findall(check_output(['xprop','-root','_NET_CLIENT_LIST']))
                if match:
                    for id in match:
                        try:
                            wpid = check_output(['xprop','-id',id,'_NET_WM_PID'])
                            wname = check_output(['xprop','-id',id,'WM_NAME'])
                            if str(pid) in wpid:
                                wid = id
                        except (OSError, subprocess.CalledProcessError): pass
                return wid

            try:
                timeout = time.time() + 10
                while time.time() < timeout:# and "browser" not in currentActiveWindowLinux().lower():
                    #windows = check_output(['wmctrl', '-l'])
                    #if "Google Chrome" in windows:
                    wid = findWid()
                    if wid:
                        try:
                            subprocess.Popen(['wmctrl', '-i', '-a', wid])
                        except (OSError, subprocess.CalledProcessError):
                            try:
                                subprocess.Popen(['xdotool', 'windowactivate', wid])
                            except (OSError, subprocess.CalledProcessError):
                                xbmc.log("Please install wmctrl or xdotool")
                        break
                    sleep(0.5)
            except (OSError, subprocess.CalledProcessError):
                pass

        elif osOSX:
            timeout = time.time() + 10
            while time.time() < timeout:
                sleep(0.5)
                applescript_switch_browser = """tell application "System Events"
                        set frontmost of the first process whose unix id is %d to true
                    end tell""" % pid
                try:
                    subprocess.Popen(['osascript', '-e', applescript_switch_browser])
                    break
                except subprocess.CalledProcessError:
                    pass
        elif osWin:
            # TODO: find out if this is needed, and if so how to implement
            pass

    def register_plugin(self, modname, pypath):
        if modname not in self.plugins:
            plugin = None
            try:
                if pypath.endswith(".pyo"):
                    pypath = os.path.splitext(pypath)[0] + ".py"
                plugin = imp.load_source(modname, pypath)
            except SyntaxError:
                try:
                    os.unlink(pypath+"o") # sometimes an incompatible over pyo breaks the import
                    plugin = imp.load_source(modname, pypath)
                except: pass
            if plugin:
                self.plugins[modname] = plugin.PLUGIN(self)

            # TODO implement background polling of plugins?
            return plugin is not None

    def __getattr__(self, name):
        for plugin in self.plugins.values():
            try:
                fn = plugin.__getattribute__(name)
                if fn is not None:
                    return fn
            except AttributeError:
                pass
        # will fail with an appropriate AttributeError
        return self.__getattribute__(name)

    def plugin(self, name, function, **kwargs):
        if name in self.plugins:
            fn = self.plugins[name].__getattribute__(function)
            if fn is not None:
                return fn(**kwargs)

    def pid(self):
        if platform.system() == 'Windows':
            raise NotImplementedError("Need to add new method to find parent pid on windows, psutil module perhaps?")

        if _use_browser == BROWSER_CHROME:
            ps = get_ps()
            cd_pid = None
            chrome_pid = 0
            for line in ps:
                if chrome_driver_path in line.CMD:
                    cd_pid = line.PID
                    break
            for line in ps:
                if line.PPID == cd_pid:
                    chrome_pid = line.PID
            return int(chrome_pid)

    ## Functions for interacting with browser

    def execute_script(self, js_script, timeout=5):
        with self.browser_lock:
            self.browser.set_script_timeout(timeout)
            result = self.browser.execute_script(js_script)
        return result

    def navigateBack(self):
        with self.browser_lock:
            result =  self.browser.back()
        return result

    def get(self, url):
        with self.browser_lock:
            result =  self.browser.get(url)
        return result

    def post(self, url, data):
        with self.browser_lock:
            result =  self.browser.post(url, data)
        return result

    def getNoJs(self, url):
        with self.browser_lock:
            self.browser.set_script_timeout(5)
            result = self.browser.execute_script(js_fn.get_js.format(url))
        return result

    def getMultNoJs(self, urls):
        with self.browser_lock:
            self.browser.set_script_timeout(5)
            result =  self.browser.execute_script(js_fn.get_multi_js, urls)
        return result

    def postNoJs(self, url, data):
        with self.browser_lock:
            self.browser.set_script_timeout(5)
            result =  self.browser.execute_script(js_fn.post_js.format(url, data))
        return result

    def getCookies(self):
        with self.browser_lock:
            result =  self.browser.get_cookies()
        return result

    def setCookies(self, cookies):
        with self.browser_lock:
            result =  self.browser.add_cookie(cookies)
        return result

    def startMonitoringKeystrokes(self, by, target):
        with self.browser_lock:
            self.browser.set_script_timeout(5)

            jstype = 'getElementById'     if by == By.ID else \
                 'querySelectorAll'       if by == By.CSS_SELECTOR else \
                 'getElementsByName'      if by == By.NAME else \
                 'getElementsByClassName' if by == By.CLASS_NAME else \
                 None
            if not jstype: raise NotImplementedError
            result = self.browser.execute_script(js_fn.start_watching_target_keys_js % (jstype, target))
            if result:
                self._monitoring_target = result['target']
                self._monitoring_parent = result['parent']
        return result

    def getKeystrokes(self):
        with self.browser_lock:
            self.browser.set_script_timeout(5)
            keys = self.browser.execute_script(js_fn.get_keys_js)
        for key in keys:
            key['name'] = js_fn.keycodeToKeyname.get(key['keyCode'], None)
        return keys

    def send_keys_to_monitored(self, key):
        # TODO incomplete
        with self.browser_lock:
            result = False

            if self._monitoring_parent:
                # todo cache these during configuration
                jstype = 'getElementById' if by == By.ID else \
                     'querySelectorAll'   if by == By.CSS_SELECTOR else \
                     'getElementsByName'  if by == By.NAME else \
                     'getElementsByClassName' if by == By.CLASS_NAME else \
                     None
                if not jstype: raise NotImplementedError

                #telement = self.browser.find_element(by, target)
                pelement = self.browser.execute_script("var pele = document.%s('%s').parentElement;pele.contentEditable = true;return pele"% (jstype, target))
                #pelement = telement.find_element_by_xpath('..')

                # click_by = By.ID
                # click_target = "kodi_webdriver_keypress_target"
                # click_element = self.browser.find_element(click_by, click_target)
                if pelement:
                    # Send key to our target div
                    result = pelement.send_keys(key)
                    # then re-focus the desired target
                    self.browser.execute_script("document.%s('%s').focus();document.%s('%s').parentElement.contentEditable = false;"% (jstype, target))
        return result


    def send_keys(self, key, by = None, target = None):
        target = 'body' if target is None else target
        by = By.CSS_SELECTOR if by is None else by
        with self.browser_lock:
            result = False

            # todo cache these during configuration
            jstype = 'getElementById'    if by == By.ID else \
                 'querySelectorAll'  if by == By.CSS_SELECTOR else \
                 'getElementsByName' if by == By.NAME else \
                 'getElementsByClassName' if by == By.CLASS_NAME else \
                 None
            if not jstype: raise NotImplementedError

            telement = self.browser.find_element(by, target)

            if telement:
                # Send key to our target div
                result = telement.send_keys(key)
                # then re-focus the desired target
                # self.browser.execute_script("document.%s('%s').focus();"% (jstype, target))
        return result

    def downloadImage(self, url_filepaths, background):
        if background:
            self.background.submit(self.downloadImage, url_filepaths, False)
        else:
            url = "<none>"
            try:
                for url, filepath in url_filepaths:
                    dirname = os.path.dirname(filepath)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)

                    use_browser = False
                    if use_browser:
                        with self.browser_lock:
                            self.browser.set_script_timeout(10)
                            link = self.browser.execute_async_script(js_fn.getimg_js.format(url))
                        img = base64.b64decode(link)
                        with open(filepath, 'wb') as filehandle:
                            filehandle.write(img)
                    else:
                        response = requests.get(url, stream=True)
                        if response.status_code == requests.codes.ok:
                            with open(filepath, 'wb') as filehandle:
                                for chunk in response.iter_content(1024):
                                    filehandle.write(chunk)
            except Exception as ex:
                log("Thumbnail download error: %s" % url)
                log("%s" % ex.message)


    def downloadImages(self, url_filepaths):
        start = time.time()

        with self.browser_lock:
            self.browser.set_script_timeout(3*len(url_filepaths))
            images = self.browser.execute_async_script(js_fn.getimgs_js, url_filepaths.keys())
        if images:
            for url, data in images.iteritems:
                img = base64.b64decode(data)
                filepath = url_filepaths[url]
                with open(filepath, 'wb') as filehandle:
                    filehandle.write(img)

        end = time.time()
        print "downloadImage: %0.2f" % (end-start)

if __name__ == '__main__':
    # Used for testing outside of kodi
    sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
    #server = ChromeDriverClient()
    #print server.getNoJs(BASE_MENU_URL)
    pass


