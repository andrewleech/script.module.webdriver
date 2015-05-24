__author__ = 'corona'

## Note
# It appears that xbmx.service does not like imports happenning during jsonrpc callbacks or similar. Just include them all here.

import os
import sys
import types
import time
import base64
import platform
import threading
import subprocess
from concurrent import futures
import requests
import _include as includes

addonUserDataFolder = None
try:
    import xbmc, xbmcaddon

    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    addonDir = xbmc.translatePath(addon.getAddonInfo('path'))
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)

    log = lambda text: xbmc.log(text, level=xbmc.LOGDEBUG)
except ImportError:
    log = sys.stdout

try:
    resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))

    from chrome_driver.selenium import webdriver
    from chrome_driver.selenium.webdriver.chrome.options import Options as ChromeOptions

    import client
    import plugins

    from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

    if platform.system() == 'Windows':
        chrome_driver_path= os.path.join(os.path.dirname(__file__),'bin','win32')
    elif platform.system() == 'Darwin':
        chrome_driver_path= os.path.join(os.path.dirname(__file__),'bin','osx')
    else:
        chrome_driver_path= os.path.join(os.path.dirname(__file__),'bin','linux')

    os.environ["PATH"] += os.pathsep + chrome_driver_path

    try:
        check_output = subprocess.check_output
    except AttributeError:
        def check_output(*popenargs, **kwargs):
            r"""Run command with arguments and return its output as a byte string.

            Backported from Python 2.7 as it's implemented as pure python on stdlib.

            >>> check_output(['/usr/bin/python', '--version'])
            Python 2.6.2
            """
            process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
            output, unused_err = process.communicate()
            retcode = process.poll()
            if retcode:
                cmd = kwargs.get("args")
                if cmd is None:
                    cmd = popenargs[0]
                error = subprocess.CalledProcessError(retcode, cmd)
                error.output = output
                raise error
            return output

        subprocess.check_output = check_output

    ## Running a get/post through ajax avoids the browser parsing the returning code, meaning this is more like a python request
    get_js = """
      var oReq = new XMLHttpRequest();
      oReq.overrideMimeType('text/plain; charset=ascii')
      oReq.open("get", "{0}", false);
      oReq.send(null);
      return oReq.response;
    """

    post_js = """
      var oReq = new XMLHttpRequest();
      oReq.open("post", "{0}", false);
      oReq.send("{1}");
      return oReq.responseText;
    """

    get_multi_js = """
    args = arguments;
    done = arguments[0];
    urls = arguments[1]
    total = urls.length;
    data = {};
    for(var i = 0; i < total; i++) {
        var req = new XMLHttpRequest();
        req.open('GET', urls[i], true);
        req.onload = function() {
          data[req.responseURL] = req.responseText
          if (data.keys().length >= total) {
            done(images);
          };
        };
        req.send(null);
    }
    """

    getimg_js = """
    var done = arguments[0];
    req = new XMLHttpRequest();
    req.overrideMimeType('text/plain; charset=x-user-defined');
    req.open('GET', "{0}", true);
    req.responseType = 'arraybuffer';
    req.onload = function() {{
      done(btoa(String.fromCharCode.apply(null, new Uint8Array(this.response))));
    }};
    req.send(null);
    """

    start_watching_keys_js = """
    kodi_keys = [];
    document.onkeydown = function(evt) {
        evt = evt || window.event;
        var key = { keyIdentifier:evt.keyIdentifier,
                    keyCode:evt.keyCode,
                    timeStamp:evt.timeStamp,
                    layerX:evt.layerX,
                    layerY:evt.layerY,
                    ctrlKey:evt.ctrlKey,
                    altKey:evt.altKey,
                    metaKey:evt.metaKey,
                    shiftKey:evt.shiftKey
                  };
        kodi_keys.push(key);
    };
    return kodi_keys;
    """

    getimg_js = """
    var done = arguments[0];
    req = new XMLHttpRequest();
    req.overrideMimeType('text/plain; charset=x-user-defined');
    req.open('GET', "{0}", true);
    req.responseType = 'arraybuffer';
    req.onload = function() {{
      done(btoa(String.fromCharCode.apply(null, new Uint8Array(this.response))));
    }};
    req.send(null);
    """

    getimgs_js = """
    var done = arguments[1];
    urls = arguments[0];
    total = urls.length;
    images = {};
    for(var i = 0; i < total; i++) {
        var req = new XMLHttpRequest();
        req.overrideMimeType('text/plain; charset=x-user-defined');
        req.open('GET', urls[i], true);
        req.responseType = 'arraybuffer';
        req.onload = function() {
          images[req.responseURL] = btoa(String.fromCharCode.apply(null, new Uint8Array(this.response)));
          if (Object.keys(images).length >= total) {
            done(images);
          };
        };
        req.send(null);
    }
    """

    get_keys_js = "var kodi_retkeys = kodi_keys; kodi_keys = []; return kodi_retkeys;"
    keycodeToKeyname = {8:"Backspace",9:"Tab",13:"Enter",16:"Shift",17:"Ctrl",18:"Alt",19:"Pause/Break",20:"Caps Lock",27:"Esc",32:"Space",33:"Page Up",34:"Page Down",35:"End",36:"Home",37:"Left",38:"Up",39:"Right",40:"Down",45:"Insert",46:"Delete",48:"0",49:"1",50:"2",51:"3",52:"4",53:"5",54:"6",55:"7",56:"8",57:"9",65:"A",66:"B",67:"C",68:"D",69:"E",70:"F",71:"G",72:"H",73:"I",74:"J",75:"K",76:"L",77:"M",78:"N",79:"O",80:"P",81:"Q",82:"R",83:"S",84:"T",85:"U",86:"V",87:"W",88:"X",89:"Y",90:"Z",91:"Windows",93:"Right Click",96:"Numpad 0",97:"Numpad 1",98:"Numpad 2",99:"Numpad 3",100:"Numpad 4",101:"Numpad 5",102:"Numpad 6",103:"Numpad 7",104:"Numpad 8",105:"Numpad 9",106:"Numpad *",107:"Numpad +",109:"Numpad -",110:"Numpad .",111:"Numpad /",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"Num Lock",145:"Scroll Lock",182:"My Computer",183:"My Calculator",186:";",187:"=",188:",",189:"-",190:".",191:"/",192:"`",219:"[",220:"\\",221:"]",222:"'"}


    class ChromeFunctions:
        def __init__(self):

            #browser = webdriver.Chrome('/path/to/chromedriver')  # Optional argument, if not specified will search path.
            self._chrome_options = ChromeOptions()
            self._chrome_options.add_argument("disable-web-security") # We can't do the ajax get/post without this option, thanks to CORS
            #chrome_options.add_argument('--load-and-launch-app="%s"' % os.path.join(os.path.dirname(__file__), 'kodi-chrome-app'))
            self._chrome_options.add_argument('--kiosk')

            if addonUserDataFolder:
                self._chrome_options.add_argument('--user-data-dir=' + os.path.join(addonUserDataFolder, "chrome_userdata"))

            self.browser_lock = threading.Lock()
            self._browser = None
            self.plugins = {}
            self.background = futures.ThreadPoolExecutor(max_workers=1)

            self.register_plugins()

        @property
        def browser(self):
            """
            This will load chrome and webdriver the first time it's hit, then
            return the cached instance forever after.
            :return: webdriver.Chrome
            """
            if self._browser is None:
                self._browser = webdriver.Chrome(chrome_options=self._chrome_options, port=47238)
                self._browser.get("file://%s/black.htm" % resources_path.replace('\\','/'))
                client.ChromeDriverClient.send_chrome_to_back()
            return self._browser

        def register_plugins(self):
            self.plugins = {}
            for mod in plugins.__dict__.values():
                if isinstance(mod, types.ModuleType):
                    self.plugins[mod.PLUGIN_NAME] = mod.PLUGIN(self)

            for plugin in self.plugins.values():
                plugin.poll()

        def plugin(self, name, function, **kwargs):
            if name in self.plugins:
                fn = self.plugins[name].__getattribute__(function)
                if fn is not None:
                    return fn(**kwargs)

        # Used to test jsonrpc channel
        def ping(self, msg):
            return msg

        def pid(self):
            if platform.system() == 'Windows':
                raise NotImplementedError("Need to add new method to find parent pid on windows, psutil module perhaps?")
            ps = subprocess.check_output(["ps","-xf"])
            pid = None
            for line in ps.splitlines()[1:]:
                try:
                    splitline = line.strip().split()
                    with self.browser_lock:
                        if splitline[2] == str(self.browser.service.process.pid):
                            pid = int(splitline[1])
                            break
                except (IndexError, ValueError) as ex: pass
            return pid

        ## Functions for interacting with chrome

        def send_keys(self, key, target = None):
            target = '/html/body' if target is None else target
            with self.browser_lock:
                result = self.browser.find_elements_by_xpath(target)[0].send_keys(key)
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
                result = self.browser.execute_script(get_js.format(url))
            return result

        def getMultNoJs(self, urls):
            with self.browser_lock:
                self.browser.set_script_timeout(5)
                result =  self.browser.execute_script(get_multi_js, urls)
            return result

        def postNoJs(self, url, data):
            with self.browser_lock:
                self.browser.set_script_timeout(5)
                result =  self.browser.execute_script(post_js.format(url, data))
            return result

        def getCookies(self):
            with self.browser_lock:
                result =  self.browser.get_cookies()
            return result

        def setCookies(self, cookies):
            with self.browser_lock:
                result =  self.browser.add_cookie(cookies)
            return result

        def startMonitoringKeystrokes(self):
            with self.browser_lock:
                self.browser.set_script_timeout(5)
                result = self.browser.execute_script(start_watching_keys_js)
            return result

        def getKeystrokes(self):
            with self.browser_lock:
                self.browser.set_script_timeout(5)
                keys = self.browser.execute_script(get_keys_js)
            for key in keys:
                key['name'] = keycodeToKeyname.get(key['keyCode'], None)
            return keys

        def downloadImage(self, url_filepaths, background):
            if background:
                self.background.submit(self.downloadImage, url_filepaths, False)
            else:
                try:
                    for url, filepath in url_filepaths:
                        dirname = os.path.dirname(filepath)
                        if not os.path.exists(dirname):
                            os.makedirs(dirname)

                        use_chrome = False
                        if use_chrome:
                            with self.browser_lock:
                                self.browser.set_script_timeout(10)
                                link = self.browser.execute_async_script(getimg_js.format(url))
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
                images = self.browser.execute_async_script(getimgs_js, url_filepaths.keys())
            if images:
                for url, data in images.iteritems:
                    img = base64.b64decode(data)
                    filepath = url_filepaths[url]
                    with open(filepath, 'wb') as filehandle:
                        filehandle.write(img)

            end = time.time()
            print "downloadImage: %0.2f" % (end-start)

    class ChromeServer(object):
        def     __init__(self, port = includes.port):
            self._port = port
            self.server = SimpleJSONRPCServer(('127.0.0.1', self._port), logRequests=False)
            self.chromefunctions = ChromeFunctions()
            self.server.register_instance(self.chromefunctions)
            self.started = False
            print "ready"
            super(ChromeServer, self).__init__()

        def service(self, timeout):
            self.started = True
            self.server.timeout = timeout
            try:
                self.server.handle_request()
                pass

            except Exception as ex:
                try:
                    import xbmc, xbmcaddon
                    xbmc.log("Chromedriver error. Please copy this line dowm to the \"-->End of Python script error report<--\" line when asking for assistance fixing the issue.", xbmc.LOGERROR)
                    __version__ = xbmcaddon.Addon().getAddonInfo('version')
                    xbmc.log("Chromedriver version: " + str(__version__), xbmc.LOGERROR)
                except: pass
                exc_info = sys.exc_info()
                raise exc_info[1], None, exc_info[2]


        def run(self):
            self.started = True
            print "ChromeDriver starting."
            self.server.serve_forever()

        def shutdown(self):
            if self.started:
                print "ChromeDriver shutting down."
                self.chromefunctions.browser.close()
                self.chromefunctions.browser.quit()
                self.server.shutdown()

    def start():
        server = ChromeServer()
        server.run()
        # server.start()
        # server.join()

    if __name__ == '__main__':
        start()


except Exception as ex:
    try:
        import xbmc, xbmcaddon
        xbmc.log("Chromedriver error. Please copy this line dowm to the \"-->End of Python script error report<--\" line when asking for assistance fixing the issue.", xbmc.LOGERROR)
        __version__ = xbmcaddon.Addon().getAddonInfo('version')
        xbmc.log("Chromedriver version: " + str(__version__), xbmc.LOGERROR)
    except: pass
    exc_info = sys.exc_info()
    raise exc_info[1], None, exc_info[2]
