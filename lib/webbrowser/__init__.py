__author__ = 'corona'

import os
import re
import imp
import json
import base64
import requests
import websocket
import threading
import send_keys
from collections import namedtuple
from Queue import Queue

from concurrent.futures import ThreadPoolExecutor
from utils import *

import js_fn

## Settings
import xbmcaddon
addon = xbmcaddon.Addon(id='script.module.webdriver')
debug           = addon.getSetting('debug')
useKiosk        = addon.getSetting('useKiosk')
useCustomPath   = addon.getSetting('useCustomPath')
customPath      = addon.getSetting('customPath') if useCustomPath == 'true' else None

resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','resources'))

rcBrowser_address = 'ws://localhost:39682'

basepath = os.path.join(os.path.dirname(__file__),'bin')
if osWin:
    rcBrowser_path= os.path.join(basepath,'rcBrowser-win32-x64', 'rcBrowser.exe')
elif osOSX:
    rcBrowser_path= os.path.join(basepath,'rcBrowser-darwin-x64', 'rcBrowser.app','Contents','MacOS','rcBrowser')
elif osLinux32:
    rcBrowser_path= os.path.join(basepath,'rcBrowser-linux-x32', 'rcBrowser.app')
elif osLinux64:
    rcBrowser_path= os.path.join(basepath,'rcBrowser-linux-x64', 'rcBrowser.app')
else:
    raise NotImplementedError("Dont' know platform: " % str(sys.platform))

# for fname in os.listdir(chrome_driver_path):
#     # Add execute permissions
#     try:
#         fname = os.path.join(chrome_driver_path, fname)
#         mode = os.stat(fname).st_mode
#         mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
#         os.chmod(fname, mode)
#     except OSError:
#         pass

# def get_ps():
#     ps = subprocess.check_output(["ps", "-xf"])
#     pid = None
#     pslines = ps.splitlines()
#     ps_entry = namedtuple('ps_entry', pslines[0].strip().split())
#     ps_entries = [ ]
#     for line in pslines[1:]:
#         spline = line.strip().split()
#         spline = spline[:7] + [" ".join(spline[7:])]
#         ps_entries.append(ps_entry(*spline))
#     return ps_entries


class Browser(object):
    _browser = None
    def __init__(self):
        self.browser_lock = threading.Lock()
        self.recv_queue = {}

        self.plugins = {}
        self.background = ThreadPoolExecutor(max_workers=1)
        # self.thr = threading.Thread(target=self.recv_queue)
        # self.thr.daemon = True

        if useKiosk:
            print 'TODO: kiosk mode not implemented yet'
            # self._chrome_options.add_argument('--kiosk')

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
            for _ in range(2):
                try:
                    self._browser = websocket.create_connection(rcBrowser_address)
                    break
                except websocket.socket.error as ex:
                    # TODO check the kind of exception above
                    subprocess.Popen([rcBrowser_path], close_fds=True)
                    # TODO check stdout from rcBrowser for a startup/ready declaration before continuing
                    sleep(5)

            if not self._browser:
                raise Exception("Can't start webbrowser")
            else:
                self.background.submit(self.recv_thread)
                # self.thr.start()
        return self._browser

    def recv_thread(self):
        try:
            sender = send_keys.KeySender()
            while True:
                data = self._browser.recv_data()
                try:
                    msg = json.loads(data[1])
                except:
                    msg = data[1]

                if isinstance(msg, dict):
                    if msg.get('seq'):
                        self.recv_queue[msg.get('seq')] = msg

                    else:
                        fn = msg['fn']
                        arg = msg['arg']

                        if fn == 'keyDown':
                            sender.send_key({'keyDown':arg})
                else:
                    print msg


        except websocket.WebSocketConnectionClosedException:
            pass
        except Exception as ex:
            print __import__('traceback').format_exc()
            print str(ex)
            raise

    def _command(self, function, argument=None):
        seq = int(time.time())
        timeout = seq + 10
        self.browser.send(json.dumps({'fn': function,
                                      'arg': argument,
                                      'seq': seq}))
        while seq not in self.recv_queue and timeout > time.time():
            sleep(0.2)
        if seq in self.recv_queue:
            ret = self.recv_queue.pop(seq).get('arg')
        else:
            print "No Reponse to %s(%s)" % (function, str(argument))
        ret = None
        return ret

    def close(self):
        with self.browser_lock:
            self._command('close')

    def show_control_window(self, keymap = None):
        # blocking
        try:
            import control_window
            controlWindow = control_window.window(self, keymap)
            controlWindow.doModal()
        except ImportError: pass

    def bring_browser_to_front(self):
        # pid = self.pid()
        # self.bring_proc_to_front(pid)
        self._command('show')

    def send_browser_to_back(self):
        # pid = os.getpid()
        # Browser.bring_proc_to_front(pid)
        self._command('hide')

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

    # def pid(self):
    #     if platform.system() == 'Windows':
    #         raise NotImplementedError("Need to add new method to find parent pid on windows, psutil module perhaps?")
    #
    #     ps = get_ps()
    #     cd_pid = None
    #     chrome_pid = 0
    #     for line in ps:
    #         if chrome_driver_path in line.CMD:
    #             cd_pid = line.PID
    #             break
    #     for line in ps:
    #         if line.PPID == cd_pid:
    #             chrome_pid = line.PID
    #     return int(chrome_pid)


    ## Functions for interacting with browser

    def execute_script(self, js_script, timeout=5):
        with self.browser_lock:
            # self.browser.set_script_timeout(timeout)
            result = self._command('executeJavaScript', js_script)
        return result

    def navigateBack(self):
        with self.browser_lock:
            # result =  self.browser.back()
            result = self._command('back')
        return result

    def loadUrl(self, url):
        with self.browser_lock:
            result = self._command('loadURL', url)
        return result

    def get(self, url):
        with self.browser_lock:
            result =  self.browser.get(url)
        return result

    def post(self, url, data):
        with self.browser_lock:
            result =  self.browser.post(url, data)
        return result

    # def getNoJs(self, url):
    #     with self.browser_lock:
    #         self.browser.set_script_timeout(5)
    #         result = self.browser.execute_script(js_fn.get_js.format(url))
    #     return result
    #
    # def getMultNoJs(self, urls):
    #     with self.browser_lock:
    #         self.browser.set_script_timeout(5)
    #         result =  self.browser.execute_script(js_fn.get_multi_js, urls)
    #     return result
    #
    # def postNoJs(self, url, data):
    #     with self.browser_lock:
    #         self.browser.set_script_timeout(5)
    #         result =  self.browser.execute_script(js_fn.post_js.format(url, data))
    #     return result

    def getCookies(self):
        with self.browser_lock:
            result = self._command('getCookies')
        return result

    def setCookies(self, cookies):
        with self.browser_lock:
            result = self._command('setCookies', cookies)
        return result

    # def startMonitoringKeystrokes(self, by, target):
    #     with self.browser_lock:
    #         self.browser.set_script_timeout(5)
    #
    #         jstype = 'getElementById'     if by == By.ID else \
    #              'querySelectorAll'       if by == By.CSS_SELECTOR else \
    #              'getElementsByName'      if by == By.NAME else \
    #              'getElementsByClassName' if by == By.CLASS_NAME else \
    #              None
    #         if not jstype: raise NotImplementedError
    #         result = self.browser.execute_script(js_fn.start_watching_target_keys_js % (jstype, target))
    #         if result:
    #             self._monitoring_target = result['target']
    #             self._monitoring_parent = result['parent']
    #     return result

    # def getKeystrokes(self):
    #     with self.browser_lock:
    #         self.browser.set_script_timeout(5)
    #         keys = self.browser.execute_script(js_fn.get_keys_js)
    #     for key in keys:
    #         key['name'] = js_fn.keycodeToKeyname.get(key['keyCode'], None)
    #     return keys

    # def send_keys_to_monitored(self, key):
    #     # TODO incomplete
    #     with self.browser_lock:
    #         result = False
    #
    #         if self._monitoring_parent:
    #             # todo cache these during configuration
    #             jstype = 'getElementById' if by == By.ID else \
    #                  'querySelectorAll'   if by == By.CSS_SELECTOR else \
    #                  'getElementsByName'  if by == By.NAME else \
    #                  'getElementsByClassName' if by == By.CLASS_NAME else \
    #                  None
    #             if not jstype: raise NotImplementedError
    #
    #             #telement = self.browser.find_element(by, target)
    #             pelement = self.browser.execute_script("var pele = document.%s('%s').parentElement;pele.contentEditable = true;return pele"% (jstype, target))
    #             #pelement = telement.find_element_by_xpath('..')
    #
    #             # click_by = By.ID
    #             # click_target = "kodi_webdriver_keypress_target"
    #             # click_element = self.browser.find_element(click_by, click_target)
    #             if pelement:
    #                 # Send key to our target div
    #                 result = pelement.send_keys(key)
    #                 # then re-focus the desired target
    #                 self.browser.execute_script("document.%s('%s').focus();document.%s('%s').parentElement.contentEditable = false;"% (jstype, target))
    #     return result

    def set_keymap(self, keymap):
        result = self._command('setKeymap', json.dumps(keymap))

    def send_keys(self, key, by = None, target = None):
        result = self._command('keyDown', key)

        # target = 'body' if target is None else target
        # by = By.CSS_SELECTOR if by is None else by
        # with self.browser_lock:
        #     result = False
        #
        #     # todo cache these during configuration
        #     jstype = 'getElementById'    if by == By.ID else \
        #          'querySelectorAll'  if by == By.CSS_SELECTOR else \
        #          'getElementsByName' if by == By.NAME else \
        #          'getElementsByClassName' if by == By.CLASS_NAME else \
        #          None
        #     if not jstype: raise NotImplementedError
        #
        #     telement = self.browser.find_element(by, target)
        #
        #     if telement:
        #         # Send key to our target div
        #         result = telement.send_keys(key)
        #         # then re-focus the desired target
        #         # self.browser.execute_script("document.%s('%s').focus();"% (jstype, target))
        return result

    # def downloadImage(self, url_filepaths, background):
    #     if background:
    #         self.background.submit(self.downloadImage, url_filepaths, False)
    #     else:
    #         url = "<none>"
    #         try:
    #             for url, filepath in url_filepaths:
    #                 dirname = os.path.dirname(filepath)
    #                 if not os.path.exists(dirname):
    #                     os.makedirs(dirname)
    #
    #                 use_browser = False
    #                 if use_browser:
    #                     with self.browser_lock:
    #                         self.browser.set_script_timeout(10)
    #                         link = self.browser.execute_async_script(js_fn.getimg_js.format(url))
    #                     img = base64.b64decode(link)
    #                     with open(filepath, 'wb') as filehandle:
    #                         filehandle.write(img)
    #                 else:
    #                     response = requests.get(url, stream=True)
    #                     if response.status_code == requests.codes.ok:
    #                         with open(filepath, 'wb') as filehandle:
    #                             for chunk in response.iter_content(1024):
    #                                 filehandle.write(chunk)
    #         except Exception as ex:
    #             log("Thumbnail download error: %s" % url)
    #             log("%s" % ex.message)

    def downloadImages(self, url_filepaths):
        """
        :param url_filepaths: list of tuple(url, filepath)
        :return: True on success
        """
        start = time.time()

        with self.browser_lock:
            result = self._command('downloadImages', url_filepaths)

        #     self.browser.set_script_timeout(3*len(url_filepaths))
        #     images = self.browser.execute_async_script(js_fn.getimgs_js, url_filepaths.keys())
        # if images:
        #     for url, data in images.iteritems:
        #         img = base64.b64decode(data)
        #         filepath = url_filepaths[url]
        #         with open(filepath, 'wb') as filehandle:
        #             filehandle.write(img)
        #
        # end = time.time()
        # print "downloadImage: %0.2f" % (end-start)
        return result

def openSettings():
    addon.openSettings()

if __name__ == '__main__':
    # Used for testing outside of kodi
    sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
    #server = ChromeDriverClient()
    #print server.getNoJs(BASE_MENU_URL)
    pass


