__author__ = 'corona'

import os
import re
import sys
import time
import subprocess
import _include as includes

try:
    import xbmc
    sleep = xbmc.sleep
except ImportError:
    sleep = time.sleep

BASE_MENU_URL = "http://m.hulu.com/menu/hd_main_menu?show_id=0&dp_id=huludesktop&package_id=2&page=1"

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if lib_path not in sys.path:
    sys.path.append(lib_path)
chromedriver_path = os.path.join(os.path.dirname(__file__))
if chromedriver_path not in sys.path:
    sys.path.append(chromedriver_path)

import jsonrpclib

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

osOSX = sys.platform.startswith('darwin')
osLinux = sys.platform.startswith('linux')
osWin = 'win' in sys.platform

class ChromeDriverClient(jsonrpclib.Server):
    def __init__(self, uri='http://127.0.0.1:%s'%includes.port, transport=None, encoding=None, verbose=0, version=None):
        jsonrpclib.Server.__init__(self, uri, transport, encoding, verbose, version)

    def show_control_window(self, jsTarget = None):
        # blocking
        self.jsTarget = jsTarget
        try:
            import control_window
            controlWindow = control_window.window(self, self.jsTarget)
            controlWindow.doModal()
        except ImportError: pass

    def bring_chrome_to_front(self):
        pid = self.pid()
        self.bring_proc_to_front(pid)

    @staticmethod
    def send_chrome_to_back():
        pid = os.getpid()
        ChromeDriverClient.bring_proc_to_front(pid)

    @staticmethod
    def bring_proc_to_front(pid):
        if osLinux:
                # Ensure chrome is active window
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
                while time.time() < timeout:# and "chrome" not in currentActiveWindowLinux().lower():
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
                    sleep(500)
            except (OSError, subprocess.CalledProcessError):
                pass

        elif osOSX:
            timeout = time.time() + 10
            while time.time() < timeout:
                sleep(500)
                applescript_switch_chrome = """tell application "System Events"
                        set frontmost of the first process whose unix id is %d to true
                    end tell""" % pid
                try:
                    subprocess.Popen(['osascript', '-e', applescript_switch_chrome])
                    break
                except subprocess.CalledProcessError:
                    pass
        elif osWin:
            # TODO: find out if this is needed, and if so how to implement
            pass

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
    server = ChromeDriverClient()
    print server.getNoJs(BASE_MENU_URL)
    pass


