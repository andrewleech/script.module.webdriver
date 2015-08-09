
## Javascript functions to be run in browser

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
