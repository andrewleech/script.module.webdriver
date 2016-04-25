# Generic compatibility & usage functions

# Use the appropriate versino of sleep depending on whether we're
# running in kodi or system python
import time
try:
    import xbmc
    sleep = lambda t: xbmc.sleep(int(t*1000))
    log = lambda text: xbmc.log(text, level=xbmc.LOGDEBUG)

except ImportError: # Not running in xbmc/kodi
    sleep = time.sleep
    log = sys.stdout

## Python 2.6 (Kodi on osx) doesn't support subprocess.check_output
import subprocess
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


import sys, platform
osOSX = sys.platform.startswith('darwin')
osLinux = sys.platform.startswith('linux')
osLinux32 = osLinux and platform.architecture()[0] == '32bit'
osLinux64 = osLinux and platform.architecture()[0] == '64bit'
osWin = 'win32' in sys.platform
