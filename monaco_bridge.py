"""Puente Monaco <-> Python: servidor local + editor embebido (se muestra con flet-webview)."""
import atexit, io, json, os, shutil, subprocess, sys, tarfile, threading, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

VER = "0.52.2"
CDN = f"https://cdn.jsdelivr.net/npm/monaco-editor@{VER}/min/vs"
TGZ = f"https://registry.npmjs.org/monaco-editor/-/monaco-editor-{VER}.tgz"
CACHE = os.path.join(os.path.expanduser("~"), ".bloc_monaco")
MIME = {".js": "application/javascript", ".css": "text/css", ".ttf": "font/ttf", ".json": "application/json",
        ".html": "text/html; charset=utf-8", ".map": "application/json", ".svg": "image/svg+xml"}


def find_browser():
    for env, rel in (("ProgramFiles(x86)", r"Microsoft\Edge\Application\msedge.exe"), ("ProgramFiles", r"Microsoft\Edge\Application\msedge.exe"),
                     ("ProgramFiles", r"Google\Chrome\Application\chrome.exe"), ("ProgramFiles(x86)", r"Google\Chrome\Application\chrome.exe"),
                     ("LOCALAPPDATA", r"Google\Chrome\Application\chrome.exe")):
        p = os.path.join(os.environ.get(env, ""), rel)
        if os.path.isfile(p):
            return p
    return shutil.which("msedge") or shutil.which("chrome") or shutil.which("google-chrome")


def find_local():
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (getattr(sys, "_MEIPASS", here), here, CACHE):
        r = os.path.join(base, "monaco")
        if os.path.isfile(os.path.join(r, "vs", "loader.js")):
            return r
        if base == CACHE and os.path.isfile(os.path.join(base, "vs", "loader.js")):
            return base
    return None


class _Win32:
    """Utilidades Win32 mínimas (solo Windows) para incrustar la ventana del editor."""
    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.c, self.wt = ctypes, wintypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        U, K = ctypes.windll.user32, ctypes.windll.kernel32
        self.U, self.K = U, K
        H = wintypes.HWND
        U.SetParent.argtypes, U.SetParent.restype = [H, H], H
        U.GetWindowLongPtrW.argtypes, U.GetWindowLongPtrW.restype = [H, ctypes.c_int], ctypes.c_ssize_t
        U.SetWindowLongPtrW.argtypes, U.SetWindowLongPtrW.restype = [H, ctypes.c_int, ctypes.c_ssize_t], ctypes.c_ssize_t
        U.MoveWindow.argtypes = [H, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.BOOL]
        U.ShowWindow.argtypes = [H, ctypes.c_int]
        U.SetWindowPos.argtypes = [H, H, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        U.IsWindowVisible.argtypes = U.IsWindow.argtypes = U.IsIconic.argtypes = [H]
        U.PostMessageW.argtypes = [H, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        U.GetWindowTextW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
        U.GetClientRect.argtypes = [H, ctypes.POINTER(wintypes.RECT)]
        U.ClientToScreen.argtypes = [H, ctypes.POINTER(wintypes.POINT)]
        U.GetClassNameW.argtypes = [H, wintypes.LPWSTR, ctypes.c_int]
        U.GetWindowThreadProcessId.argtypes = [H, ctypes.POINTER(wintypes.DWORD)]
        K.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        K.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        K.Process32FirstW.argtypes = K.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        K.CloseHandle.argtypes = [ctypes.c_void_p]
        self.ENUM = ctypes.WINFUNCTYPE(wintypes.BOOL, H, wintypes.LPARAM)

    def ShowWindow(self, h, n):
        self.U.ShowWindow(h, n)

    def windows(self):
        out, c = [], self.c

        @self.ENUM
        def cb(h, _):
            cls, pid = c.create_unicode_buffer(80), self.wt.DWORD()
            self.U.GetClassNameW(h, cls, 80)
            self.U.GetWindowThreadProcessId(h, c.byref(pid))
            out.append((h, cls.value, pid.value, bool(self.U.IsWindowVisible(h))))
            return True
        self.U.EnumWindows(cb, 0)
        return out

    def descendants(self, root):
        c, wt = self.c, self.wt

        class PE(c.Structure):
            _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("pid", wt.DWORD), ("heap", c.c_size_t),
                        ("mod", wt.DWORD), ("thr", wt.DWORD), ("ppid", wt.DWORD), ("pri", c.c_long),
                        ("flags", wt.DWORD), ("exe", c.c_wchar * 260)]
        snap, pe, pairs = self.K.CreateToolhelp32Snapshot(2, 0), PE(), []
        pe.dwSize = c.sizeof(pe)
        ok = self.K.Process32FirstW(snap, c.byref(pe))
        while ok:
            pairs.append((pe.pid, pe.ppid))
            ok = self.K.Process32NextW(snap, c.byref(pe))
        self.K.CloseHandle(snap)
        found, ch = {root}, True
        while ch:
            ch = False
            for pid, pp in pairs:
                if pp in found and pid not in found:
                    found.add(pid)
                    ch = True
        return found

    def title(self, h):
        b = self.c.create_unicode_buffer(300)
        self.U.GetWindowTextW(h, b, 300)
        return b.value

    def host(self, hint):
        ws = [w for w in self.windows() if w[1] == "FLUTTER_RUNNER_WIN32_WINDOW"]
        pids = self.descendants(os.getpid())
        for h, cls, pid, vis in ws:
            if pid in pids:
                return h
        for h, cls, pid, vis in ws:
            if hint.lower() in self.title(h).lower():
                return h
        return None

    def find_by_title(self, text):
        for h, cls, pid, vis in self.windows():
            if cls == "Chrome_WidgetWin_1" and vis and text.lower() in self.title(h).lower():
                return h
        return None

    def detach(self, h):
        self.U.ShowWindow(h, 0)
        self.U.SetParent(h, None)
        st = self.U.GetWindowLongPtrW(h, -16)
        self.U.SetWindowLongPtrW(h, -16, (st & ~0x40000000) | 0x80000000)

    def adopt(self, h, host):
        U = self.U
        U.ShowWindow(h, 0)
        st = U.GetWindowLongPtrW(h, -16)
        st &= ~(0x40000000 | 0x00C00000 | 0x00040000 | 0x00080000 | 0x00020000 | 0x00010000)
        U.SetWindowLongPtrW(h, -16, st | 0x80000000)                  # popup sin marco ni botones
        ex = U.GetWindowLongPtrW(h, -20)
        U.SetWindowLongPtrW(h, -20, (ex & ~0x00040000) | 0x00000080)  # fuera de la barra de tareas y de Alt+Tab
        U.SetWindowLongPtrW(h, -8, host)                              # dueño = ventana de Flet: la sigue, se oculta y restaura con ella
        U.SetWindowPos(h, None, 0, 0, 0, 0, 0x27)

    def origin(self, host):
        pt = self.wt.POINT(0, 0)
        self.U.ClientToScreen(host, self.c.byref(pt))
        return pt.x, pt.y

    def client(self, host, layout):
        r = self.wt.RECT()
        self.U.GetClientRect(host, self.c.byref(r))
        try:
            sc = self.U.GetDpiForWindow(host) / 96
        except Exception:
            sc = 1.0
        l, t, rr, b = (int(v * sc) for v in layout)
        return l, t, max(100, r.right - l - rr), max(100, r.bottom - t - b)


W32 = _Win32() if sys.platform == "win32" else None


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Editor de código [__PORT__]</title>
<style>html,body,#c{margin:0;height:100%;width:100%;overflow:hidden;background:#0b0d10}</style></head>
<body><div id="c"></div>
<script src="__VS__/loader.js"></script>
<script>
const VS="__VS__", ABS = VS.startsWith('http') ? VS : location.origin + VS;
self.MonacoEnvironment={getWorkerUrl:()=>'data:text/javascript;charset=utf-8,'+encodeURIComponent(
 "self.MonacoEnvironment={baseUrl:'"+ABS.replace(/vs$/,'')+"'};importScripts('"+ABS+"/base/worker/workerMain.js');")};
require.config({paths:{vs:ABS}});
require(['vs/editor/editor.main'],()=>{
 monaco.editor.defineTheme('bloc',{base:'vs-dark',inherit:true,rules:[],colors:{
  'editor.background':'#0b0d10','editor.foreground':'#d7dae0','editorLineNumber.foreground':'#4b5263',
  'editorLineNumber.activeForeground':'#9aa4b5','editor.lineHighlightBackground':'#12151a',
  'editor.selectionBackground':'#2a3a5c','editorCursor.foreground':'#7aa2f7','editorGutter.background':'#0b0d10',
  'minimap.background':'#0b0d10'}});
 let chain=Promise.resolve(), oth=[], timer=null, dirty=false, applying=false, gen=0, ed=null, busy=false;
 const post=evs=>{chain=chain.then(()=>fetch('/ev',{method:'POST',body:JSON.stringify({evs})})).catch(()=>{});};
 function flush(){clearTimeout(timer);timer=null;const evs=[];
  if(dirty){evs.push({t:'chg',text:ed.getValue()});dirty=false;}
  evs.push(...oth);oth=[];if(evs.length)post(evs);}
 const queue=()=>{if(!timer)timer=setTimeout(flush,120);};
 const rng=(m,a,b)=>{const p=m.getPositionAt(a),q=m.getPositionAt(b);return new monaco.Range(p.lineNumber,p.column,q.lineNumber,q.column);};
 function run(c){const m=ed.getModel();switch(c.c){
  case 'open':{applying=true;const n=monaco.editor.createModel(c.text,c.lang);ed.setModel(n);m&&m.dispose();applying=false;
   ed.updateOptions({fontSize:c.font});ed.setScrollTop(0);ed.setPosition({lineNumber:1,column:1});break;}
  case 'setall':ed.pushUndoStop();ed.executeEdits('py',[{range:m.getFullModelRange(),text:c.text}]);ed.pushUndoStop();
   if(c.a!=null){const p=m.getPositionAt(c.a);ed.setPosition(p);}break;
  case 'replace':ed.pushUndoStop();ed.executeEdits('py',[{range:rng(m,c.a,c.b),text:c.t,forceMoveMarkers:true}]);
   ed.pushUndoStop();ed.setPosition(m.getPositionAt(c.a+c.t.length));break;
  case 'select':{const r=rng(m,c.a,c.b);ed.setSelection(r);ed.revealRangeInCenterIfOutsideViewport(r);ed.focus();break;}
  case 'undo':case 'redo':ed.focus();ed.trigger('py',c.c,null);break;
  case 'trigger':ed.focus();ed.trigger('py',c.id,null);break;
  case 'font':ed.updateOptions({fontSize:c.size});break;
  case 'focus':ed.focus();break;}}
 fetch('/boot').then(r=>r.json()).then(d=>{gen=d.gen;
  ed=monaco.editor.create(document.getElementById('c'),{value:d.text,language:d.lang,theme:'bloc',automaticLayout:true,
   fontFamily:'Consolas, "Courier New", monospace',fontSize:d.font,minimap:{enabled:true},smoothScrolling:true,
   cursorSmoothCaretAnimation:'on',bracketPairColorization:{enabled:true},scrollBeyondLastLine:false,
   renderWhitespace:'selection',tabSize:4,padding:{top:8},fontLigatures:false});
  const m=ed.getModel();ed.setSelection(rng(m,d.a,d.b));ed.revealRangeInCenterIfOutsideViewport(rng(m,d.a,d.b));
  ed.onDidChangeModelContent(()=>{if(!applying){dirty=true;queue();}});
  ed.onDidChangeCursorSelection(e=>{const mm=ed.getModel(),s=e.selection,p=ed.getPosition();
   oth=oth.filter(x=>x.t!=='sel');
   oth.push({t:'sel',a:mm.getOffsetAt(s.getStartPosition()),b:mm.getOffsetAt(s.getEndPosition()),ln:p.lineNumber,col:p.column,len:mm.getValueLength()});queue();});
  window.addEventListener('keydown',e=>{
   const k=e.key,up=k.length===1?k.toUpperCase():k;let n=null;
   if(e.ctrlKey&&!e.altKey){if('SNOPBE'.includes(up)&&up.length===1)n=up;
    else if(k==='='||k==='+')n='Equal';else if(k==='-'||k==='_')n='Minus';else if(k==='0')n='0';}
   else if(k==='F5'||k==='F11')n=k;
   if(!n)return;e.preventDefault();e.stopPropagation();
   oth.push({t:'key',key:n,ctrl:e.ctrlKey,shift:e.shiftKey});flush();},true);
  setInterval(()=>{if(busy)return;busy=true;fetch('/poll?g='+gen).then(r=>r.json()).then(cs=>cs.forEach(run)).catch(()=>{}).finally(()=>busy=false);},80);
  ed.focus();});
});
</script></body></html>"""


class Bridge:
    def __init__(self, on_event, font=15, on_note=None, title_hint="Bloc de notas"):
        self.on_event, self.q, self.lock, self.gen = on_event, [], threading.Lock(), 0
        self.on_note, self.title_hint, self.busy, self._h, self._last, self.att = on_note, title_hint, False, None, None, False
        threading.Thread(target=self._watch, daemon=True).start()
        self.doc = dict(text="", lang="plaintext", font=font, a=0, b=0)
        self.root, self.proc, self.hwnd, self.layout, self.want = find_local(), None, None, (0, 0, 0, 0), False
        atexit.register(self.close)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.port = self.srv.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/editor.html"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        if not self.root:
            threading.Thread(target=self._download, daemon=True).start()

    # ---- Python -> editor ----
    def cmd(self, **c):
        with self.lock:
            self.q.append(c)

    def open(self, text, lang, font):
        self.doc.update(text=text, lang=lang, font=font, a=0, b=0)
        self.cmd(c="open", text=text, lang=lang, font=font)

    def setall(self, text, caret=None):
        self.doc["text"] = text
        self.cmd(c="setall", text=text, a=caret)

    def replace(self, a, b, t):
        v = self.doc["text"]
        self.doc["text"] = v[:a] + t + v[b:]
        self.cmd(c="replace", a=a, b=b, t=t)

    def select(self, a, b):
        self.doc.update(a=a, b=b)
        self.cmd(c="select", a=a, b=b)

    def set_font(self, size):
        self.doc["font"] = size
        self.cmd(c="font", size=size)

    # ---- ventana del editor: Edge/Chrome en modo aplicación, incrustado en la ventana de Flet (Windows) ----
    def _say(self, m):
        if self.on_note:
            try:
                self.on_note(m)
            except Exception:
                pass

    def alive(self):
        return bool(self.hwnd) and bool(W32.U.IsWindow(self.hwnd))

    def show(self, layout):
        """layout = (izq, arriba, der, abajo) en px lógicos ocupados por el resto de la interfaz."""
        self.layout, self.want = layout, True
        if self.alive():
            self._place()
            return
        if self.busy:
            return
        exe = find_browser()
        if not exe:
            raise RuntimeError("no se encontró Microsoft Edge ni Chrome")
        self.hwnd, self.busy = None, True
        self.proc = subprocess.Popen([exe, f"--app={self.url}", f"--user-data-dir={os.path.join(CACHE, 'profile')}",
                                      "--window-position=200,150", "--window-size=900,600", "--no-first-run",
                                      "--disable-features=Translate"])
        threading.Thread(target=self._embed, daemon=True).start()

    def hide(self):
        self.want = False
        if self.alive():
            W32.U.ShowWindow(self.hwnd, 0)

    def place(self, layout):
        self.layout = layout
        if self.want and self.alive():
            self._place()

    def _host(self):
        if not (self._h and W32.U.IsWindow(self._h)):
            self._h = W32.host(self.title_hint)
        return self._h

    def _place(self, force=True):
        host = self._host()
        if not host or W32.U.IsIconic(host):  # ventana principal minimizada: Windows oculta y restaura el editor solo
            return
        x, y, w, h = W32.client(host, self.layout)
        ox, oy = W32.origin(host)
        r = (ox + x, oy + y, w, h)
        if force or r != self._last:
            self._last = r
            W32.U.MoveWindow(self.hwnd, *r, True)
        if not W32.U.IsWindowVisible(self.hwnd):
            W32.U.ShowWindow(self.hwnd, 4)  # SW_SHOWNOACTIVATE

    def _watch(self):  # el editor sigue a la ventana principal (mover, redimensionar, maximizar, restaurar)
        import time
        while True:
            time.sleep(0.04)
            try:
                if self.want and self.alive():
                    self._place(force=False)
            except Exception:
                pass

    def _embed(self):
        import time
        try:
            h = host = None
            for _ in range(200):  # hasta 20 s
                time.sleep(0.1)
                h = h or W32.find_by_title(f"[{self.port}]")
                host = W32.host(self.title_hint)
                if h and host:
                    break
            if not h:
                return self._say("No se encontró la ventana del editor")
            self.hwnd = h
            if not host:
                return self._say("Editor abierto en ventana aparte (no se halló la ventana principal)")
            W32.adopt(h, host)
            if self.want:
                self._place()
            else:
                W32.U.ShowWindow(h, 0)
            self._say("")
        except Exception as e:
            self._say(f"Error al incrustar el editor: {e}")
        finally:
            self.busy = False

    def close(self):
        if self.alive():
            W32.U.PostMessageW(self.hwnd, 0x10, 0, 0)  # WM_CLOSE
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    # ---- descarga única de Monaco (si no está empaquetado) ----
    def _download(self):
        try:
            tmp = os.path.join(CACHE, "tmp")
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp, exist_ok=True)
            data = urllib.request.urlopen(TGZ, timeout=60).read()
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tg:
                for m in tg:
                    if m.isfile() and m.name.startswith("package/min/vs/"):
                        dst = os.path.join(tmp, m.name[len("package/min/"):])
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        with open(dst, "wb") as f:
                            f.write(tg.extractfile(m).read())
            final = os.path.join(CACHE, "monaco")
            shutil.rmtree(final, ignore_errors=True)
            os.replace(tmp, final)
            self.root = final
        except Exception:
            shutil.rmtree(os.path.join(CACHE, "tmp"), ignore_errors=True)

    def _handler(self):
        br = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, body, ctype="application/json", code=200):
                if isinstance(body, str):
                    body = body.encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                u = urlparse(self.path)
                if u.path == "/editor.html":
                    vs = "/vs" if br.root else CDN
                    self._send(PAGE.replace("__VS__", vs).replace("__PORT__", str(br.port)), MIME[".html"])
                elif u.path == "/boot":
                    with br.lock:
                        br.gen += 1
                        br.q.clear()
                    self._send(json.dumps(dict(br.doc, gen=br.gen)))
                elif u.path == "/poll":
                    g = int(parse_qs(u.query).get("g", ["0"])[0])
                    with br.lock:
                        out, br.q = (br.q, []) if g == br.gen else ([], br.q)
                    self._send(json.dumps(out))
                elif u.path.startswith("/vs/") and br.root:
                    p = os.path.normpath(os.path.join(br.root, u.path.lstrip("/")))
                    if p.startswith(os.path.normpath(br.root)) and os.path.isfile(p):
                        with open(p, "rb") as f:
                            self._send(f.read(), MIME.get(os.path.splitext(p)[1], "application/octet-stream"))
                    else:
                        self._send("", "text/plain", 404)
                else:
                    self._send("", "text/plain", 404)

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                try:
                    evs = json.loads(self.rfile.read(n) or b"{}").get("evs", [])
                except Exception:
                    evs = []
                for ev in evs:
                    if ev.get("t") == "chg":
                        br.doc["text"] = ev["text"]
                    elif ev.get("t") == "sel":
                        br.doc.update(a=ev["a"], b=ev["b"])
                    try:
                        br.on_event(ev)
                    except Exception:
                        pass
                self._send("{}")

        return H
