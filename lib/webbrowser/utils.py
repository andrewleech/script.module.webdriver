# Generic compatibility & usage functions

# Use the appropriate versino of sleep depending on whether we're
# running in kodi or system python
import time
try:
    import xbmc
    sleep = lambda t: xbmc.sleep(int(t*1000))
    log = lambda text: xbmc.log(text)
    logdebug = lambda text: xbmc.log(text, level=xbmc.LOGDEBUG)

except ImportError: # Not running in xbmc/kodi
    import sys
    sleep = time.sleep
    log = sys.stdout
    logdebug = sys.stdout

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

import os
import stat
from fnmatch import fnmatch

def download_file(url, dest, progress_callback):
    import requests
    if not os.path.exists(dest):
        os.makedirs(dest)
    file_name = os.path.join(dest,url.split('/')[-1])
    response = requests.get(url, stream=True, verify=False)
    response.raise_for_status()
    meta = response.headers
    file_size = int(meta.get("Content-Length", -1))
    if os.path.exists(file_name) and os.path.getsize(file_name) == file_size:
        print("Using previously downloaded: %s" % (file_name))
    else:
        with open(file_name, 'wb') as fp:
            file_size_dl = 0
            block_sz = 1024*1024
            for block in response.iter_content(block_sz):
                if not block:
                    break
                file_size_dl += len(block)
                fp.write(block)
                if progress_callback:
                    percent = min(int(file_size_dl * 100. / file_size)+1, 100)
                    progress_callback(percent)
            print(": Done.")
    return file_name


def rmdir(path):
    try:
        print("Removing: %s" % path)
        if sys.platform == "win32":
            os.system("RMDIR /s /q %s" % os.path.normpath(path))
        else:
            os.system("chmod -R +w %s" % path)
            os.system("rm -rf %s" % path)
    except:
        pass
    if os.path.exists(path):
        import shutil
        shutil.rmtree(path, ignore_errors=True)


def extract(filename, filtermatch = None):
    if isinstance(filtermatch, basestring):
        filtermatch = [filtermatch]
    file_list = []
    folder, extension = os.path.splitext(filename)
    if extension.endswith('zip'):
        import zipfile
        if os.path.exists(folder):
            rmdir(folder)
        if not os.path.exists(folder):
            os.makedirs(folder)
        zipFile = zipfile.ZipFile(filename, 'r')
        if not filtermatch:
            zipFile.extractall(folder)
            file_list = zipFile.namelist()
        else:
            for item in zipFile.infolist():
                if item is None:
                    break
                if True in [fnmatch(item.filename, match) for match in filtermatch]:
                    zipFile.extract(item, folder)
                    file_list.append(item.filename)
    else:
        import tarfile
        if os.path.exists(folder):
            rmdir(folder)
        if not os.path.exists(folder):
            os.makedirs(folder)
        tarFile = tarfile.open(filename, "r")
        if not filtermatch:
            tarFile.extractall(folder)
            file_list = tarFile.getnames()
        else:
            for item in tarFile.getmembers():
                if item is None:
                    break
                if True in [fnmatch(item.name, match) for match in filtermatch]:
                    tarFile.extract(item, folder)
                    file_list.append(item.name)

                    fname = os.path.abspath(os.path.join(folder, item.name))
                    if not os.path.islink(fname):
                        # Remove readonly flag as it often causes problems later on
                        os.chmod( fname, stat.S_IWRITE | os.stat(fname).st_mode )
                    else: # is symlink
                        # Check if symlink is absolute, and convert to relative if it is
                        linkpath = os.readlink(fname)
                        if os.path.isabs(linkpath):
                            newpath = folder + os.path.sep + linkpath
                            newpath = os.path.relpath(newpath,os.path.dirname(fname))
                            print ("rewriting symlink %s from %s to %s" % (fname, linkpath, newpath))
                            os.unlink(fname)
                            os.symlink(newpath, fname)


    contents = [e for e in os.listdir(folder) if not e.startswith('.')]
    if len(contents) == 1 and contents[0] == os.path.basename(folder):
        os.rename(folder, folder+"_tmp")
        os.rename(os.path.join(folder+"_tmp", contents[0]), folder)
        rmdir(folder+"_tmp")
    file_list = [os.path.abspath(os.path.join(folder, fname)) for fname in file_list]
    return folder, file_list

import sys, platform
osOSX = sys.platform.startswith('darwin')
osLinux = sys.platform.startswith('linux')
osLinux32 = osLinux and platform.architecture()[0] == '32bit'
osLinux64 = osLinux and platform.architecture()[0] == '64bit'
osWin = 'win32' in sys.platform

OSX = "OSX"
Linux = "Linux"
Linux32 = "Linux32"
Linux64 = "Linux64"
Win = "Win"

OS = Win if osWin else \
    Linux64 if osLinux64 else \
    Linux32 if osLinux32 else \
    Linux if osLinux else \
    OSX if osOSX else None
