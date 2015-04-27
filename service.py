
try:
    import xbmc
    log = lambda text: xbmc.log(text, level=xbmc.LOGDEBUG)
except ImportError:
    log = sys.stdout

trace_on = False
try:
    # try:
    #     __import__("pydevd").settrace('192.168.0.16', port=51384, stdoutToServer=True, stderrToServer=True)
    #     trace_on = True
    # except BaseException as ex: pass

    import os
    import sys
    import threading

    libpath = os.path.join(os.path.dirname(__file__), 'lib')
    if libpath not in sys.path:
        sys.path.append(libpath)

    from lib.chrome_driver import server

    def service_monitor(driver):
        monitor = xbmc.Monitor()
        while True:
            # We need to service the shutdown check and exit the script when asked within 5 seconds or risk getting killed

            # Sleep/wait for abort for 0.1 seconds
            if monitor.waitForAbort(0.05):
                # Abort was requested while waiting. We should exit
                break

            # Service jsonrpc requests
            driver.service(1)

        log("ChromeDriver service shutting down")
        driver.shutdown()

    log("ChromeDriver service starting up")
    driver = server.ChromeServer()
    #driver = None

    #monthread = threading.Thread(target=service_monitor, args=(driver,))
    #monthread.daemon = True
    #monthread.start()

    #driver.run()
    service_monitor(driver)

finally:
    if trace_on:
        __import__("pydevd").stoptrace()