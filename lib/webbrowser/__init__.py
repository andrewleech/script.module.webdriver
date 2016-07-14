__author__ = 'corona'

import os
import re
import imp
import json
import xbmc
import websocket
import threading
import send_keys
import xbmcgui
from concurrent.futures import ThreadPoolExecutor
from utils import *

import js_fn

## Settings
import xbmcaddon
addon = xbmcaddon.Addon(id='script.module.webbrowser')
debug           = addon.getSetting('debug')
useKiosk        = addon.getSetting('useKiosk')
useCustomPath   = addon.getSetting('useCustomPath')
customPath      = addon.getSetting('customPath') if useCustomPath == 'true' else None

resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','resources'))

rcBrowser_address = 'ws://localhost:39682'

basepath = xbmc.translatePath(addon.getAddonInfo('profile'))

rcBrowser_path = {
    Win     : os.path.join(basepath,'rcBrowser-win32-x64', 'rcBrowser.exe'),
    OSX     : os.path.join(basepath,'rcBrowser-darwin-x64', 'rcBrowser.app','Contents','MacOS','rcBrowser'),
    Linux32 : os.path.join(basepath,'rcBrowser-linux-x32', 'rcBrowser'),
    Linux64 : os.path.join(basepath,'rcBrowser-linux-x64', 'rcBrowser'),
}[OS]

baseurl = "https://github.com/andrewleech/rcBrowser/releases/download/v1.0-alpha/"
rcBrowser_url = {
    Win     : baseurl + "rcBrowser-win32-ia32.tgz",
    OSX     : baseurl + "rcBrowser-darwin-x64.tgz",
    Linux32 : baseurl + "rcBrowser-linux-ia32.tgz",
    Linux64 : baseurl + "rcBrowser-linux-x64.tgz",
}[OS]



def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')

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
        self._controlWindow = None

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
                    if not os.path.exists(rcBrowser_path):
                        download_rcbrowser()
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
                        arg = msg.get('arg')

                        if fn == 'keyDown':
                            sender.send_key({'keyDown':arg})
                        elif fn == 'close':
                            if self._controlWindow:
                                self._controlWindow.close()
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
            self._controlWindow = control_window.window(self, keymap)
            self._controlWindow.doModal()
        except ImportError:
            pass
        finally:
            self._controlWindow = None

    def bring_browser_to_front(self):
        # self._command('setFullScreen', True)
        self._command('showFullScreen')

    def send_browser_to_back(self):
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

    def executeJavaScript(self, js_script):
        with self.browser_lock:
            result = self._command('executeJavaScript', js_script)
            # result = self._command('webContentsJavaScript', 'echo "test";')
        return result

    def executeJavaScriptOnReady(self, js_script):
        with self.browser_lock:
            result = self._command('webContentsJavaScript', js_fn.on_webview_ready_js % js_script)
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

    def getCookies(self):
        with self.browser_lock:
            result = self._command('getCookies')
        return result

    def setCookies(self, cookies):
        with self.browser_lock:
            result = self._command('setCookies', cookies)
        return result

    def set_keymap(self, keymap):
        result = self._command('setKeymap', json.dumps(keymap))

    def send_keys(self, key, by = None, target = None):
        result = self._command('keyDown', key)
        return result

    def downloadImages(self, url_filepaths):
        """
        :param url_filepaths: list of tuple(url, filepath)
        :return: True on success
        """
        start = time.time()

        with self.browser_lock:
            result = self._command('downloadImages', url_filepaths)

        return result

def download_rcbrowser():
    pDialog = xbmcgui.DialogProgress()
    try:
        pDialog.create('Downloading rcBrowser', translation(31000) + "...")
        pDialog.update(0, translation(31000) + "...")

        def progress(percent):
            pDialog.update(int(percent), translation(31000) + "...")

        archive = download_file(rcBrowser_url, basepath, progress)
        if archive:
            pDialog.update(100, translation(31000) + "...")
        folder, _ = extract(archive)
    except Exception as ex:
        utils.log("Error downloading rcBrowser: %s" % ex)
    finally:
        pDialog.close()


def openSettings():
    addon.openSettings()

if __name__ == '__main__':
    # Used for testing outside of kodi
    sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
    #server = ChromeDriverClient()
    #print server.getNoJs(BASE_MENU_URL)
    pass


