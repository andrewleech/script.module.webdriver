
## Javascript functions to be run in browser

class dotdict(dict):
    __getattr__ = lambda self,k: dict.__getitem__(self,k.lower())
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


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

start_watching_keys_js_complex = """
// Record any previous event handlers if assigned by jquery
// http://stackoverflow.com/a/447106
kodi_webdriver_window_keydown = []

try {
    var clickEvents = window.getStorage().get('prototype_event_registry').get('keydown');
    clickEvents.each(function(wrapper){
        kodi_webdriver_window_keydown.push(wrapper.handler);
    });
} catch(err) { }

try {
    var keydownEvents = $(window).data("events").keydown;
    jQuery.each(keydownEvents, function(key, handlerObj) {
        kodi_webdriver_window_keydown.push(handlerObj.handler);
        // also available: handlerObj.type, handlerObj.namespace
    });
    $(window).unbind("keydown");

} catch(err) { }

var orig = window.onclick;
if (orig) {
    kodi_webdriver_window_keydown.push(orig);
}

var target = document.createElement('div');
target.innerHtml = "<br>";
target.id = "kodi_webdriver_keypress_target";
target.contentEditable = true;
document.body.appendChild(target);

kodi_keys = [];
document.onkeydown = function(evt) {
    evt = evt || window.event;
    var target = document.getElementById("kodi_webdriver_keypress_target");
    if (evt.target != target) {
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
        // Block any default behavior
        evt.stopPropagation();
        evt.stopImmediatePropagation();
        evt.preventDefault();
        return false;
    } else {
        for (var fn in kodi_webdriver_window_keydown) {
            alert(evt)
            fn(evt);
        }
    }
};
return kodi_keys;
"""

start_watching_target_keys_js = """

kodi_keys_target = document.%s('%s');
kodi_keys_target.contentEditable = true;
kodi_keys_target.focus();

kodi_keys = [];
kodi_keys_target.addEventListener("keydown", function(evt) {

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

    // Block any default behavior
    evt.stopPropagation();
    evt.stopImmediatePropagation();
    evt.preventDefault();

    try {
        var jq_evt = $.event.fix(evt);
        jq_evt.stopPropagation();
    } catch(err) { }

    return false;
}, false);

return {"target":kodi_keys_target,
        "parent":kodi_keys_target.parentElement};
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

def close():
    return "close();"

def keypress(key):
    # hexkey = hex(key)[2:]
    # hexkey = r"\\u" + "0" * (4 - len(hexkey)) + hexkey
    # return "keyPress('{key}');".format(key=hexkey)
    key = keyname[key] if isinstance(key, int) else key
    return "keyPress('{key}');".format(key=key)


# keycodeToKeyname = dotdict(**{8:"backspace",9:"tab",13:"enter",16:"shift",17:"ctrl",18:"alt",19:"pause",20:"caps lock",27:"esc",32:"space",33:"pageup",34:"pagedown",35:"end",36:"home",37:"left",38:"up",39:"right",40:"down",45:"insert",46:"delete",48:"zero",49:"one",50:"two",51:"three",52:"four",53:"five",54:"six",55:"seven",56:"eight",57:"none",65:"a",66:"b",67:"c",68:"d",69:"e",70:"f",71:"g",72:"h",73:"i",74:"j",75:"k",76:"l",77:"m",78:"n",79:"o",80:"p",81:"q",82:"r",83:"s",84:"t",85:"u",86:"v",87:"w",88:"x",89:"y",90:"z",91:"meta",93:"menu",96:"numpadzero",97:"numpadone",98:"numpadtwo",99:"numpadthree",100:"numpadfour",101:"numpadfive",102:"numpadsix",103:"numpadseven",104:"numpadeight",105:"numpadnine",106:"numpad *",107:"numpadplus",109:"numpadminus",110:"numpad .",111:"numpad /",112:"f1",113:"f2",114:"f3",115:"f4",116:"f5",117:"f6",118:"f7",119:"f8",120:"f9",121:"f10",122:"f11",123:"f12",144:"num lock",145:"scroll lock",182:"my computer",183:"my calculator",186:";",187:"equals",188:"comma",189:"minus",190:"period",191:"/",192:"`",219:"opensquarebracket",220:"backslash",221:"closesquarebracket",222:"'"})
# keynameToKeycode = dotdict((val,key) for key,val in keycodeToKeyname.iteritems())

class _keycode(object):
    __getitem__ = lambda *args:getattr(_keycode,args[1])
    get = lambda self, key, default=None: getattr(self, key, default)
    backspace                  = 8
    tab                        = 9
    enter                      = 13
    shift                      = 16
    ctrl                       = 17
    alt                        = 18
    pause                      = 19
    vars()["caps lock"]        = 20
    esc                        = 27
    escape                     = 27
    space                      = 32
    pageup                     = 33
    pagedown                   = 34
    end                        = 35
    home                       = 36
    left                       = 37
    up                         = 38
    right                      = 39
    down                       = 40
    insert                     = 45
    delete                     = 46
    zero                       = 48
    one                        = 49
    two                        = 50
    three                      = 51
    four                       = 52
    five                       = 53
    six                        = 54
    seven                      = 55
    eight                      = 56
    none                       = 57
    a                          = 65
    b                          = 66
    c                          = 67
    d                          = 68
    e                          = 69
    f                          = 70
    g                          = 71
    h                          = 72
    i                          = 73
    j                          = 74
    k                          = 75
    l                          = 76
    m                          = 77
    n                          = 78
    o                          = 79
    p                          = 80
    q                          = 81
    r                          = 82
    s                          = 83
    t                          = 84
    u                          = 85
    v                          = 86
    w                          = 87
    x                          = 88
    y                          = 89
    z                          = 90
    meta                       = 91
    menu                       = 93
    numpadzero                 = 96
    numpadone                  = 97
    numpadtwo                  = 98
    numpadthree                = 99
    numpadfour                 = 100
    numpadfive                 = 101
    numpadsix                  = 102
    numpadseven                = 103
    numpadeight                = 104
    numpadnine                 = 105
    numpadplus                 = 107
    numpadminus                = 109
    vars()["numpad *"]         = 106
    vars()["numpad ."]         = 110
    vars()["numpad /"]         = 111
    f1                         = 112
    f2                         = 113
    f3                         = 114
    f4                         = 115
    f5                         = 116
    f6                         = 117
    f7                         = 118
    f8                         = 119
    f9                         = 120
    f10                        = 121
    f11                        = 122
    f12                        = 123
    equals                     = 187
    comma                      = 188
    minus                      = 189
    period                     = 190
    vars()["num lock"]         = 144
    vars()["scroll lock"]      = 145
    vars()["my computer"]      = 182
    vars()["my calculator"]    = 183
    vars()[";"]                = 186
    vars()["/"]                = 191
    vars()["`"]                = 192
    opensquarebracket          = 219
    backslash                  = 220
    closesquarebracket         = 221
    vars()["'"]                = 222
keycode = _keycode()
keyname = dotdict((getattr(keycode,key),key) for key in dir(keycode) if not key.startswith('_') )
