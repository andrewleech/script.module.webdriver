__author__ = 'corona'

import os
import js_fn

import xbmcgui
import xbmcaddon

import send_keys
import subprocess
from utils import *

DEFAULT_KEYMAP = {
    xbmcgui.ACTION_SELECT_ITEM   : js_fn.keypress(js_fn.keycode.space),
    xbmcgui.ACTION_MOVE_LEFT     : js_fn.keypress(js_fn.keycode.left),
    xbmcgui.ACTION_MOVE_RIGHT    : js_fn.keypress(js_fn.keycode.right),
    xbmcgui.ACTION_MOVE_UP       : js_fn.keypress(js_fn.keycode.up),
    xbmcgui.ACTION_MOVE_DOWN     : js_fn.keypress(js_fn.keycode.down),
    xbmcgui.ACTION_PLAY          : js_fn.keypress(js_fn.keycode.space),
    xbmcgui.ACTION_NAV_BACK      : js_fn.close(),
    xbmcgui.ACTION_PARENT_DIR    : js_fn.close(),
    xbmcgui.ACTION_PREVIOUS_MENU : js_fn.close(),
    xbmcgui.ACTION_STOP          : js_fn.close(),
    xbmcgui.ACTION_SHOW_INFO     : js_fn.close(),
    xbmcgui.ACTION_SHOW_GUI      : js_fn.close(),
}


class WindowXMLDialogActions(xbmcgui.WindowXMLDialog):
    # def __init__(self, strXMLname, strFallbackPath, strDefaultName, forceFallback=0, parent = None):
    #     self.parent = parent
    #     xbmcgui.WindowXMLDialog.__init__( self )
    TEXTBOX_ID = 7509
    OK_BUTTON_ID = 7510

    def setParent(self, parent):
        self.parent = parent

    def onAction(self, *args):
        if self.parent:
            self.parent.onAction(*args)

    def onClick(self, controlId):
        if controlId == self.OK_BUTTON_ID:
            self.close()

    def onInit(self):
        # window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        addon = xbmcaddon.Addon('script.module.webbrowser')
        textbox = self.getControl(self.TEXTBOX_ID)
        ok_button = self.getControl(self.OK_BUTTON_ID)
        textbox.setText(addon.getLocalizedString(32001))
        textbox.setVisible(True)
        ok_button.setLabel(addon.getLocalizedString(32002))


class window(object):
    def __init__(self, browser, keymap = None):
        addon_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..',))
        self.window = WindowXMLDialogActions('control_window.xml', addon_folder, 'default')
        # self.window = WindowXMLDialogActions('DialogBusy.xml', addon_folder)
        self.window.setParent(self)
        self.browser = browser
        self.keymap = DEFAULT_KEYMAP if keymap is None else keymap

    def __del__(self):
        self.close()

    def close(self):
        self.window.close()

    def _backgroundJsHandler(self, stopEvt):
        """
        Runs in thread while control window is open
        """
        # self.browser.startMonitoringKeystrokes()
        sender = send_keys.KeySender()
        while not stopEvt.is_set():
            try:
                keys = self.browser.getKeystrokes()
    #            for key in keys:
                if keys:
                    sender.send_key(keys)
     #               action = KEY_ACTION_MAP.get(key.get('name', None), None)
      #              if action:
       #                 self.onAction(action)
                    sleep(0.025)
                else:
                    sleep(0.250)
            except Exception as ex:
                log(__import__('traceback').format_exc())
                log(str(ex))
        sender.close()

    def doModal(self):
        import threading
        stopEvt = threading.Event()
        try:
            # thread = threading.Thread(target = self._backgroundJsHandler, args=(stopEvt,))
            # thread.daemon = True
            # thread.start()
            self.window.doModal()
        finally:
            stopEvt.set()

    def setKeymapCallback(self, keymap):
        self.keymap = keymap if keymap is not None else DEFAULT_KEYMAP

    def onAction(self, action):
        action = action.getId() if isinstance(action, xbmcgui.Action) else action
        action_js= self.keymap.get(action, None)
        if action_js:
            try:
                self.browser.executeJavaScript(action_js)
            except:
                pass
            if action_js == js_fn.close():
                self.close()


    def action_exit(self, *args):
        self.close()

    def action_sendkey(self, *args):
        self.browser.send_keys(*args)
