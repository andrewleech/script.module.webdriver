
try:
    import xbmc
    log = lambda text: xbmc.log(text, level=xbmc.LOGDEBUG)
except ImportError:
    log = sys.stdout

trace_on = False
try:
    try:
        __import__("pydevd").settrace('192.168.0.16', port=51384, stdoutToServer=True, stderrToServer=True)
        trace_on = True
    except BaseException as ex: pass

    import os
    import sys
    import threading

    lib_path = os.path.join(os.path.dirname(__file__), 'lib')
    if lib_path not in sys.path:
        sys.path.append(lib_path)
    chromedriver_path = os.path.join(os.path.dirname(__file__), 'lib', 'chrome_driver')
    if chromedriver_path not in sys.path:
        sys.path.append(chromedriver_path)

    from lib.webdriver import server

    # def monitor_thread():
    #     monitor = xbmc.Monitor()


    log("ChromeDriver service starting up")
    driver = server.ChromeServer()
    #driver = None

    #monthread = threading.Thread(target=service_monitor, args=(driver,))
    #monthread.daemon = True
    #monthread.start()

    shutdown_thread = threading.Thread(target=driver.shutdown)
    shutdown_thread.daemon = True

    # We need to service the shutdown check and exit the script when asked within 5 seconds or risk getting killed
    while not xbmc.abortRequested:
        # Service jsonrpc requests
        driver.service(1)

    log("ChromeDriver service shutting down")
    shutdown_thread.start()

finally:
    if trace_on:
        __import__("pydevd").stoptrace()