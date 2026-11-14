"""Bloc de notas oscuro en Flet (compatible con Flet 0.28 y 0.80+)."""
import os, re, sys, shutil, inspect, subprocess, datetime, webbrowser
MOBILE = ("ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ
          or os.environ.get("FLET_PLATFORM", "").lower() in ("android", "ios"))
try:  # no existe en Android
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = filedialog = None
import flet as ft
from types import SimpleNamespace
try:
    import monaco_bridge
    MONACO, MONACO_ERR = os.environ.get("BLOC_MONACO") != "0" and not MOBILE, ""  # BLOC_MONACO=0 lo desactiva
except Exception as _e:
    MONACO, MONACO_ERR = False, repr(_e)
try:  # incrustado solo si el cliente de Flet lo soporta: BLOC_MONACO=embed
    import flet_webview as fwv
    EMBED = os.environ.get("BLOC_MONACO") == "embed"
except Exception:
    EMBED = False
try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name
    from pygments.token import Token
except ImportError:
    lex = None

CODE = {".py": "python", ".js": "javascript", ".ts": "typescript", ".json": "json", ".html": "html",
        ".css": "css", ".java": "java", ".c": "c", ".cpp": "cpp", ".h": "cpp", ".cs": "csharp", ".go": "go",
        ".rs": "rust", ".sh": "bash", ".sql": "sql", ".yml": "yaml", ".yaml": "yaml", ".xml": "xml",
        ".php": "php", ".rb": "ruby", ".kt": "kotlin", ".toml": "ini", ".ini": "ini", ".bat": "dos",
        ".ps1": "powershell", ".lua": "lua", ".swift": "swift", ".dart": "dart"}
MD = {".md", ".markdown"}
TYPES = [("Texto y código", " ".join("*" + e for e in [".txt", ".log", ".csv"] + sorted(MD) + sorted(CODE))),
         ("Todos los archivos", "*.*")]
LANG = {"bash": "shell", "dos": "bat", "dart": "plaintext"}  # nombres distintos en Monaco
LIVE_COLORS = False  # False = código como texto plano + botón de vista con colores
BG, BAR, FG, ACC, MUTED, MONO = "#0b0d10", "#12151a", "#d7dae0", "#7aa2f7", "#6b7280", "Consolas"

TC = {Token.Keyword: "#c586c0", Token.Keyword.Constant: "#569cd6", Token.Keyword.Type: "#4ec9b0",
      Token.Name.Function: "#dcdcaa", Token.Name.Class: "#4ec9b0", Token.Name.Builtin: "#4ec9b0",
      Token.Name.Decorator: "#dcdcaa", Token.Name.Tag: "#569cd6", Token.Name.Attribute: "#9cdcfe",
      Token.Name.Constant: "#4fc1ff", Token.String: "#ce9178", Token.Number: "#b5cea8",
      Token.Comment: "#6a9955", Token.Operator.Word: "#c586c0"} if lex else {}


def tcolor(t):
    while t is not None:
        if t in TC:
            return TC[t]
        t = t.parent
    return FG


def hl_spans(text, lang):
    try:
        lexer = get_lexer_by_name({"dos": "bat"}.get(lang, lang), stripnl=False, ensurenl=False)
    except Exception:
        return None
    out, last, buf = [], None, ""
    for t, v in lex(text, lexer):
        c = tcolor(t)
        if c == last:
            buf += v
        else:
            if buf:
                out.append(ft.TextSpan(text=buf, style=ft.TextStyle(color=last)))
            last, buf = c, v
    if buf:
        out.append(ft.TextSpan(text=buf, style=ft.TextStyle(color=last)))
    return out


def W(cls, *a, **kw):
    """Crea un control ignorando argumentos que la versión instalada de Flet no soporte."""
    while True:
        try:
            return cls(*a, **kw)
        except TypeError as e:
            m = re.search(r"argument '(\w+)'", str(e))
            if m and m.group(1) in kw:
                kw.pop(m.group(1))
            else:
                raise


def pad(h, v=None):
    v = h if v is None else v
    P = getattr(ft, "Padding", None)
    if P is not None and hasattr(P, "symmetric"):
        return P.symmetric(horizontal=h, vertical=v)
    return ft.padding.symmetric(horizontal=h, vertical=v)


_CLIP = [""]


def ask(fn, **kw):
    if tk is None:
        return None
    r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
    try:
        return fn(parent=r, **kw)
    finally:
        r.destroy()


def clip_set(t):
    _CLIP[0] = t
    if tk is not None:
        r = tk.Tk(); r.withdraw(); r.clipboard_clear(); r.clipboard_append(t); r.update(); r.destroy()


def clip_get():
    if tk is None:
        return _CLIP[0]
    r = tk.Tk(); r.withdraw()
    try:
        return r.clipboard_get()
    except tk.TclError:
        return ""
    finally:
        r.destroy()


def main(page: ft.Page):
    S = dict(path=None, dirty=False, mode="edit", size=15, sel=(0, 0), hist=[""], idx=0, root=None, sbw=240, sb=not MOBILE, exp=set(), cur=None, pv=None, hv=None)
    page.theme_mode = ft.ThemeMode.DARK
    try:
        page.theme = page.dark_theme = W(ft.Theme, font_family="Segoe UI", color_scheme=W(
            ft.ColorScheme, primary=ACC, surface=BG, on_surface=FG, background=BG, on_background=FG,
            surface_tint=BG, surface_container=BAR, surface_container_high=BAR, surface_container_highest=BAR))
    except Exception:
        pass
    page.bgcolor = BG
    page.padding = 0
    if not MOBILE:
        page.window.width, page.window.height = 1000, 700

    mono = lambda: ft.TextStyle(font_family=MONO, size=S["size"], height=1.4, letter_spacing=0, word_spacing=0)

    def focus(c):
        try:
            r = c.focus()
        except Exception:
            return
        if inspect.iscoroutine(r):
            async def _f():
                await r
            page.run_task(_f)

    tf = W(ft.TextField, multiline=True, min_lines=30, border=ft.InputBorder.NONE, bgcolor=ft.Colors.TRANSPARENT, filled=True, fill_color=ft.Colors.TRANSPARENT, focused_bgcolor=ft.Colors.TRANSPARENT, hover_color=ft.Colors.TRANSPARENT,
           text_vertical_align=ft.VerticalAlignment.START,
           selection_color="#2a3a5c", color=FG,
           cursor_color=ACC, content_padding=pad(18), text_size=S["size"], autofocus=True,
           text_style=mono(), hint_text="Escribe o pega aquí…",
           hint_style=ft.TextStyle(color=MUTED))
    theme = getattr(ft.MarkdownCodeTheme, "ATOM_ONE_DARK", "atom-one-dark")
    md = W(ft.Markdown, "", selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, code_theme=theme,
           on_tap_link=lambda e: webbrowser.open(e.data))
    md_col = ft.Column([md], scroll=ft.ScrollMode.AUTO, expand=True)
    md_view = W(ft.Container, md_col, padding=pad(28, 14),
                expand=True, bgcolor=BG)
    hl_t = ft.Text(spans=[], style=mono())
    hl = W(ft.Container, hl_t, padding=pad(18), visible=False)
    tf_box = W(ft.Container, ft.Column([ft.Stack([hl, tf])], scroll=ft.ScrollMode.AUTO, expand=True,
                                           horizontal_alignment=ft.CrossAxisAlignment.STRETCH), expand=True, bgcolor=BG)
    vdiv = ft.VerticalDivider(width=1, color="#232830", visible=False)
    md_view.visible = False
    mb = code_box = None
    if MONACO:
        try:
            mb = monaco_bridge.Bridge(lambda ev: on_monaco(ev), S["size"], lambda m: note(m))
            if EMBED:
                code_box = W(ft.Container, W(fwv.WebView, url=mb.url, expand=True, bgcolor=BG), expand=True, bgcolor=BG, visible=False)
            else:
                code_box = W(ft.Container, expand=True, bgcolor=BG, visible=False)
        except Exception as _e:
            mb = code_box = None
            globals()["MONACO_ERR"] = repr(_e)
    body = ft.Row([c for c in (tf_box, code_box, vdiv, md_view) if c is not None], spacing=0, expand=True)

    def note(m):
        S["note"] = m
        status.value = stat()
        status.update()

    def layout():  # px lógicos que ocupa el resto de la interfaz alrededor del editor
        return (40 + ((S["sbw"] + 5) if S["sb"] else 0), 48, 0, 28 if status_bar.visible else 0)

    def show_win():
        if not mb or EMBED:
            return
        try:
            mb.show(layout())
        except Exception as ex:
            status.value = f"No se pudo abrir el editor: {ex}"
            status.update()

    def hide_win():
        if mb and not EMBED:
            mb.hide()

    def back_win():
        if codeon() and not EMBED:
            show_win()

    def codeon():
        return bool(mb) and S.get("mon") is True and S["mode"] == "edit"

    def on_monaco(ev):
        t = ev.get("t")
        if t == "chg":
            tf.value = ev["text"]
            if not S["dirty"]:
                S["dirty"] = True
                page.title = f"*{name()} - Bloc de notas"
                page.update()
        elif t == "sel":
            S["sel"], S["cp"] = (ev["a"], ev["b"]), (ev["ln"], ev["col"], ev["len"])
            status.value = stat()
            status.update()
        elif t == "key":
            on_key(SimpleNamespace(key=ev["key"], ctrl=ev["ctrl"], shift=ev["shift"]))
    vbtn = W(ft.IconButton, icon=ft.Icons.VISIBILITY_OUTLINED, icon_size=18, icon_color=ACC, visible=False,
             on_click=lambda e: set_mode())

    def mdstyle():
        z, B = S["size"], ft.FontWeight.BOLD
        t = lambda k=1, **kw: ft.TextStyle(size=z * k, color=kw.pop("color", FG), **kw)
        return W(ft.MarkdownStyleSheet, p_text_style=t(), h1_text_style=t(2, weight=B), h2_text_style=t(1.6, weight=B),
                 h3_text_style=t(1.3, weight=B), h4_text_style=t(1.1, weight=B), list_bullet_text_style=t(),
                 a_text_style=t(color=ACC), code_text_style=ft.TextStyle(font_family=MONO, size=z - 1, bgcolor="#12161d"),
                 codeblock_decoration=W(ft.BoxDecoration, bgcolor="#12161d", border_radius=6),
                 blockquote_decoration=W(ft.BoxDecoration, bgcolor=BAR, border_radius=4),
                 table_body_text_style=t(), table_head_text_style=t(weight=B))

    def mk_md():
        return W(ft.Markdown, md_text(), extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, code_theme=theme,
                 md_style_sheet=mdstyle(), on_tap_link=lambda e: webbrowser.open(e.data))
    status = ft.Text("", size=12, color=MUTED)
    status_bar = W(ft.Container, status, bgcolor=BAR, padding=pad(14, 0), height=28, alignment=ft.Alignment(-1, 0))

    # ---------- utilidades ----------
    def name():
        return os.path.basename(S["path"]) if S["path"] else "Sin título"

    def refresh():
        ext = os.path.splitext(S["path"] or "")[1].lower()
        vbtn.visible = ext not in CODE or not LIVE_COLORS
        mon = bool(mb) and ext in CODE
        vbtn.visible = not mon and (ext not in CODE or not LIVE_COLORS)
        if mon and S.get("mon") is not True:
            mb.open(tf.value or "", LANG.get(CODE[ext], CODE[ext]), S["size"])
        S["mon"] = mon
        if mb and not EMBED:
            show_win() if mon and S["mode"] == "edit" else hide_win()
        if code_box is not None:
            tf_box.visible = S["mode"] == "edit" and not mon
            code_box.visible = S["mode"] == "edit" and mon
        fit_w()
        hl_on = LIVE_COLORS and bool(lex) and ext in CODE and len(tf.value or "") < 80000
        if hl_on and tf.value != S["hv"]:
            sp = hl_spans(tf.value or "", CODE[ext])
            if sp is None:
                hl_on = False
            else:
                S["hv"] = tf.value
                hl_t.spans = sp
        hl.visible = hl_on
        tf.color = ft.Colors.TRANSPARENT if hl_on else FG
        tf.selection_color = ft.Colors.with_opacity(0.3, ACC) if hl_on else "#2a3a5c"
        vbtn.icon = ft.Icons.EDIT_OUTLINED if S["mode"] == "view" else ft.Icons.VISIBILITY_OUTLINED
        vbtn.tooltip = "Editar (Ctrl+E)" if S["mode"] == "view" else "Ver con formato (Ctrl+E)"
        if S["mode"] == "view" and tf.value != S["pv"]:
            S["pv"] = tf.value
            md_col.controls = [mk_md()]
        page.title = f"{'*' if S['dirty'] else ''}{name()} - Bloc de notas"
        status.value = stat()
        if ext in CODE and not mb:
            status.value += f"   |   Monaco no disponible: {MONACO_ERR}"
        page.update()

    def md_text():
        ext = os.path.splitext(S["path"] or "")[1].lower()
        return f"````{CODE[ext]}\n{tf.value}\n````" if ext in CODE else (tf.value or "")

    def render():
        m = S["mode"]
        tf_box.visible, md_view.visible = m == "edit", m == "view"
        S["pv"] = None
        refresh()
        if m == "view":
            page.update()
        elif S.get("mon"):
            mb.cmd(c="focus")
        else:
            focus(tf)

    def set_mode(m=None):
        if S.get("mon") and not isinstance(m, str):
            return
        S["mode"] = m if isinstance(m, str) else "view" if S["mode"] == "edit" else "edit"
        render()

    def push(v):
        h = S["hist"]
        if v != h[S["idx"]]:
            del h[S["idx"] + 1:]
            h.append(v)
            S["idx"] += 1
            if len(h) > 300:
                h.pop(0); S["idx"] -= 1

    def on_change(e):
        S["dirty"] = True
        push(tf.value)
        refresh()

    def stat():
        v = tf.value or ""
        b = min(S["sel"][1], len(v))
        ln, col, n = v.count(chr(10), 0, b) + 1, b - (v.rfind(chr(10), 0, b) + 1) + 1, len(v)
        if codeon() and S.get("cp"):
            ln, col, n = S["cp"]
        mode = dict(edit="Edición", split="Dividida", view="Vista")[S["mode"]]
        return (f"Ln {ln}, Col {col}   |   {n} caracteres"
                f"   |   {int(S['size'] / 15 * 100)}%   |   UTF-8   |   {mode}" + (f"   |   {S['note']}" if S.get("note") else ""))

    def on_sel(e):
        s = e.selection
        try:
            a, b = s.start, s.end
        except Exception:
            a, b = s.base_offset, s.extent_offset
        S["sel"] = tuple(sorted((max(0, a), max(0, b))))
        status.value = stat()
        status.update()

    tf.on_change, tf.on_selection_change = on_change, on_sel
    try:
        tf.text_vertical_align = ft.VerticalAlignment.START
    except Exception:
        pass

    def select(a, b):
        if codeon():
            S["sel"] = (a, b)
            mb.select(a, b)
            return
        try:
            tf.selection = ft.TextSelection(start=a, end=b)
        except TypeError:
            tf.selection = ft.TextSelection(base_offset=a, extent_offset=b)
        S["sel"] = (a, b)
        tf.update()
        focus(tf)

    def set_text(t, caret=None):
        tf.value = t
        if codeon():
            S["dirty"] = True
            if caret is not None:
                S["sel"] = (caret, caret)
            mb.setall(t, caret)
            refresh()
            return
        push(t)
        S["dirty"] = True
        if caret is not None:
            select(caret, caret)
        refresh()

    def insert(t):
        a, b = S["sel"]
        v = tf.value or ""
        if codeon():
            mb.replace(a, b, t)
            tf.value, S["sel"], S["dirty"] = v[:a] + t + v[b:], (a + len(t),) * 2, True
            refresh()
            return
        set_text(v[:a] + t + v[b:], a + len(t))

    # ---------- diálogos ----------
    def show(d):
        hide_win()
        page.show_dialog(d) if hasattr(page, "show_dialog") else page.open(d)

    def close(d):
        back_win()
        page.pop_dialog() if hasattr(page, "pop_dialog") else page.close(d)

    def dlg(title, content=None, actions=(), modal=True):
        d = W(ft.AlertDialog, modal=modal, title=ft.Text(title, size=16), content=content, bgcolor=BAR,
              actions=list(actions))
        show(d)
        return d

    def btn(text, fn):
        return W(ft.TextButton, content=ft.Text(text), on_click=lambda e: fn())

    def confirm_then(action):
        if not S["dirty"]:
            return action()

        def yes():
            close(d)
            if save():
                action()

        def no():
            close(d); action()

        d = dlg("¿Guardar cambios?", ft.Text(f"Hay cambios sin guardar en {name()}."),
                [btn("Guardar", yes), btn("No guardar", no), btn("Cancelar", lambda: close(d))])

    # ---------- archivo ----------
    def load(p):
        raw = open(p, "rb").read()
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            t = raw.decode("utf-16", errors="replace")
        elif b"\0" in raw[:8192]:
            d = dlg("No se puede abrir", ft.Text(f"{os.path.basename(p)} es un archivo binario."),
                    [btn("Cerrar", lambda: close(d))])
            return
        else:
            try:
                t = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                t = raw.decode("cp1252", errors="replace")
        ext = os.path.splitext(p)[1].lower()
        tf.value = t
        S.update(mon=None, cp=None, path=p, dirty=False, hist=[t], idx=0, sel=(0, 0), mode="view" if ext in MD else "edit")
        render()

    def new():
        def go():
            tf.value = ""
            S.update(mon=None, cp=None, path=None, dirty=False, hist=[""], idx=0, sel=(0, 0), mode="edit")
            render()
        confirm_then(go)

    def new_window():
        if MOBILE:
            return
        args = [sys.executable] + ([] if getattr(sys, "frozen", False) else [os.path.abspath(__file__)])
        subprocess.Popen(args)

    fp = None
    if tk is None:  # Android / sin tkinter: selector de archivos de Flet
        fp = ft.FilePicker()
        try:
            page.services.append(fp)
        except Exception:
            page.overlay.append(fp)

    async def pick_file():
        try:
            r = await fp.pick_files(allow_multiple=False)
            if r and r[0].path:
                load(r[0].path)
        except Exception as ex:
            note(f"No se pudo abrir el archivo: {ex}")

    async def pick_dir():
        try:
            d = await fp.get_directory_path()
            if d:
                S.update(root=d, cur=d, exp={d})
                if not S["sb"]:
                    toggle_sb()
                build_tree()
        except Exception as ex:
            note(f"No se pudo abrir la carpeta: {ex}")

    def open_file():
        def go():
            if fp is not None:
                page.run_task(pick_file)
                return
            p = ask(filedialog.askopenfilename, filetypes=TYPES)
            if p:
                load(p)
        confirm_then(go)

    def save(as_=False):
        p = S["path"]
        if (as_ or not p) and fp is not None:  # sin diálogo de guardar: carpeta de datos de la app
            base = os.environ.get("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
            os.makedirs(base, exist_ok=True)
            p, n = os.path.join(base, "nota.txt"), 1
            while os.path.exists(p) and not (S["path"] and os.path.samefile(p, S["path"])):
                n += 1
                p = os.path.join(base, f"nota{n}.txt")
            note(f"Guardado en {p}")
        elif as_ or not p:
            p = ask(filedialog.asksaveasfilename, defaultextension=".txt", initialfile=name(), filetypes=TYPES)
            if not p:
                return False
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(tf.value or "")
        S.update(path=p, dirty=False)
        refresh()
        return True

    def print_file():
        if save() and hasattr(os, "startfile"):
            os.startfile(S["path"], "print")

    def destroy():
        if mb:
            mb.close()
        async def _d():
            r = page.window.destroy()
            if inspect.isawaitable(r):
                await r
        page.run_task(_d)

    def exit_app():
        confirm_then(destroy)

    def on_win(e):
        t = str(getattr(e, "type", "") or getattr(e, "data", "")).lower()
        if "close" in t:
            exit_app()

    try:
        page.window.prevent_close = True
        page.window.on_event = on_win
    except Exception:
        pass

    # ---------- edición ----------
    def undo():
        if codeon():
            mb.cmd(c="undo")
            return
        if S["idx"] > 0:
            S["idx"] -= 1; tf.value = S["hist"][S["idx"]]; S["dirty"] = True; refresh()

    def redo():
        if codeon():
            mb.cmd(c="redo")
            return
        if S["idx"] < len(S["hist"]) - 1:
            S["idx"] += 1; tf.value = S["hist"][S["idx"]]; S["dirty"] = True; refresh()

    def copy():
        a, b = S["sel"]
        if a != b:
            clip_set((tf.value or "")[a:b])

    def cut():
        copy(); insert("")

    def paste():
        t = clip_get()
        if t:
            insert(t)

    def delete():
        a, b = S["sel"]
        if a == b:
            S["sel"] = (a, min(b + 1, len(tf.value or "")))
        insert("")

    def select_all():
        select(0, len(tf.value or ""))

    def now():
        insert(datetime.datetime.now().strftime("%H:%M %d/%m/%Y"))

    fq = W(ft.TextField, label="Buscar", dense=True, autofocus=True, on_submit=lambda e: find_next())
    rq = W(ft.TextField, label="Reemplazar con", dense=True)

    def find_next():
        if codeon():
            mb.cmd(c="trigger", id="editor.action.nextMatchFindAction")
            return
        q, v = fq.value or "", (tf.value or "")
        if not q:
            return
        if S["mode"] == "view":
            set_mode("edit")
        i = v.lower().find(q.lower(), S["sel"][1])
        if i < 0:
            i = v.lower().find(q.lower())
        if i >= 0:
            select(i, i + len(q))
        else:
            status.value = "No se encontró el texto"; page.update()

    def replace_one():
        a, b = S["sel"]
        if a != b and (tf.value or "")[a:b].lower() == (fq.value or "").lower():
            insert(rq.value or "")
        find_next()

    def replace_all():
        if fq.value:
            n = re.sub(re.escape(fq.value), lambda m: rq.value or "", tf.value or "", flags=re.I)
            set_text(n, 0)

    def find_dialog(replace=False):
        if codeon():
            mb.cmd(c="trigger", id="editor.action.startFindReplace" if replace else "actions.find")
            return
        rq.visible = replace
        col = ft.Column([fq, rq], tight=True, width=340)
        acts = [btn("Siguiente", find_next)]
        if replace:
            acts += [btn("Reemplazar", replace_one), btn("Todo", replace_all)]
        d = dlg("Reemplazar" if replace else "Buscar", col, acts + [btn("Cerrar", lambda: close(d))], modal=False)

    def goto():
        if codeon():
            mb.cmd(c="trigger", id="editor.action.gotoLine")
            return
        n = W(ft.TextField, label="Número de línea", dense=True, autofocus=True)

        def go():
            try:
                ln = max(1, int(n.value))
            except (TypeError, ValueError):
                return
            lines = (tf.value or "").split("\n")
            pos = sum(len(x) + 1 for x in lines[:min(ln, len(lines)) - 1])
            close(d); set_mode("edit") if S["mode"] == "view" else None; select(pos, pos)
        n.on_submit = lambda e: go()
        d = dlg("Ir a la línea", n, [btn("Ir", go), btn("Cancelar", lambda: close(d))])

    # ---------- ver ----------
    def zoom(delta=0):
        S["size"] = 15 if delta == 0 else max(8, min(60, S["size"] + delta))
        if mb:
            mb.set_font(S["size"])
        tf.text_size = S["size"]
        tf.text_style = hl_t.style = mono()
        S["hv"] = None
        S["pv"] = None
        fit()
        refresh()

    def toggle_status():
        status_bar.visible = not status_bar.visible; page.update()
        if mb and S.get("mon"):
            mb.place(layout())

    def fullscreen():
        page.window.full_screen = not page.window.full_screen; page.update()

    def about():
        d = dlg("Bloc de notas", ft.Text("Editor ligero en Flet.\nTexto, Markdown y código con colores.\n"
                                         "Pega respuestas de una IA y pulsa Ctrl+E para verlas renderizadas."),
                [btn("Cerrar", lambda: close(d))])

    def fit_w():
        w = (page.width or page.window.width or 1000) - 45 - ((S["sbw"] + 5) if S["sb"] else 0) - 14
        tf.width = hl.width = max(200, w)
        if mb and S.get("mon") and not EMBED:
            mb.place(layout())

    def fit(e=None):
        fit_w()
        h = page.height or page.window.height or 700
        tf.min_lines = max(5, int((h - 120) / (S["size"] * 1.25)))
        try:
            tf.update()
        except Exception:
            pass
    try:
        page.on_resize = page.on_resized = fit
    except Exception:
        pass

    # ---------- explorador ----------
    SKIP = {".git", "__pycache__", "node_modules", ".venv", ".idea", ".vscode"}
    tree = ft.ListView(expand=True, spacing=0)
    title_txt = ft.Text("EXPLORADOR", size=11, color=MUTED, weight=ft.FontWeight.BOLD, expand=True)

    def prompt(title, default, cb):
        t = W(ft.TextField, value=default, dense=True, autofocus=True)

        def ok():
            v = (t.value or "").strip()
            if v:
                close(d)
                try:
                    cb(v)
                except OSError as ex:
                    status.value = str(ex); page.update()
        t.on_submit = lambda e: ok()
        d = dlg(title, t, [btn("Aceptar", ok), btn("Cancelar", lambda: close(d))])

    def mk(base, is_dir):
        b = base if isinstance(base, str) else (S["cur"] or S["root"])
        if not b:
            return open_folder()

        def go(n):
            p = os.path.join(b, n)
            if is_dir:
                os.makedirs(p, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "a").close()
            S["exp"].add(b)
            build_tree()
            if not is_dir:
                confirm_then(lambda: load(p))
        prompt("Nueva carpeta" if is_dir else "Nuevo archivo", "", go)

    def rename(p):
        def go(n):
            q = os.path.join(os.path.dirname(p), n)
            os.rename(p, q)
            cp = S["path"]
            if cp and (cp == p or cp.startswith(p + os.sep)):
                S["path"] = q + cp[len(p):]
            build_tree(); refresh()
        prompt("Renombrar", os.path.basename(p), go)

    def delete(p):
        def yes():
            close(d)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
            cp = S["path"]
            if cp and (cp == p or cp.startswith(p + os.sep)):
                S.update(path=None, dirty=True)
            build_tree(); refresh()
        d = dlg("Eliminar", ft.Text(f"¿Eliminar {os.path.basename(p)}? No se puede deshacer."),
                [btn("Eliminar", yes), btn("Cancelar", lambda: close(d))])

    def click(p, isd):
        if isd:
            S["exp"].symmetric_difference_update({p})
            S["cur"] = p
            build_tree()
        else:
            S["cur"] = os.path.dirname(p)
            confirm_then(lambda: (load(p), build_tree()))

    def row_menu(p, isd):
        it = lambda t, f: W(ft.PopupMenuItem, content=ft.Text(t, size=13), on_click=lambda e: f())
        items = ([it("Nuevo archivo", lambda: mk(p, False)), it("Nueva carpeta", lambda: mk(p, True))] if isd else [])
        items += [it("Renombrar", lambda: rename(p)), it("Eliminar", lambda: delete(p))]
        return W(ft.PopupMenuButton, icon=ft.Icons.MORE_VERT, icon_size=14, icon_color=MUTED, items=items)

    def walk(d, depth):
        try:
            items = sorted(os.scandir(d), key=lambda x: (not x.is_dir(), x.name.lower()))
        except OSError:
            return
        for x in items:
            if x.name in SKIP:
                continue
            isd, op = x.is_dir(), x.path in S["exp"]
            icon = (ft.Icons.FOLDER_OPEN if op else ft.Icons.FOLDER) if isd else ft.Icons.INSERT_DRIVE_FILE_OUTLINED
            row = ft.Row([ft.Icon(icon, size=16, color=ACC if isd else MUTED),
                          ft.Text(x.name, size=13, color=FG, expand=True, no_wrap=True), row_menu(x.path, isd)],
                         spacing=6)
            tree.controls.append(W(ft.Container, row, padding=ft.Padding(left=8 + depth * 14, top=1, right=2, bottom=1),
                                   bgcolor="#1c2230" if x.path == S["path"] else None, ink=True,
                                   on_click=lambda e, p=x.path, i=isd: click(p, i)))
            if isd and op:
                walk(x.path, depth + 1)

    def build_tree():
        tree.controls.clear()
        r = S["root"]
        title_txt.value = (os.path.basename(r) or r).upper() if r else "EXPLORADOR"
        if r:
            walk(r, 0)
        else:
            tree.controls.append(W(ft.Container, ft.Column([ft.Text("No hay carpeta abierta", size=12, color=MUTED),
                                                            btn("Abrir carpeta", open_folder)]), padding=pad(12, 10)))
        page.update()

    def open_folder():
        if fp is not None:
            page.run_task(pick_dir)
            return
        p = ask(filedialog.askdirectory)
        if p:
            S.update(root=p, cur=p, exp={p})
            if not S["sb"]:
                toggle_sb()
            build_tree()

    def toggle_sb():
        S["sb"] = not S["sb"]
        sidebar.visible = grip.visible = S["sb"]
        fit_w()
        page.update()

    def drag(e):
        dx = getattr(e, "delta_x", None)
        if dx is None:
            dx = e.local_delta.x
        S["sbw"] = max(140, min(600, S["sbw"] + dx))
        sidebar.width = S["sbw"]
        fit_w()
        page.update()

    ib = lambda ic, tip, f: W(ft.IconButton, icon=ic, icon_size=16, icon_color=MUTED, tooltip=tip,
                              on_click=lambda e: f())
    head = ft.Row([ib(ft.Icons.NOTE_ADD_OUTLINED, "Nuevo archivo", lambda: mk(None, False)),
                   ib(ft.Icons.CREATE_NEW_FOLDER_OUTLINED, "Nueva carpeta", lambda: mk(None, True)),
                   ib(ft.Icons.REFRESH, "Actualizar", build_tree),
                   ib(ft.Icons.CHEVRON_LEFT, "Ocultar (Ctrl+B)", toggle_sb)], spacing=0,
                   alignment=ft.MainAxisAlignment.END)
    sidebar = W(ft.Container, ft.Column([W(ft.Container, head, padding=pad(10, 2)), tree], spacing=0),
                width=S["sbw"], bgcolor=BAR, visible=S["sb"])
    grip = W(ft.GestureDetector, visible=S["sb"], content=ft.Container(width=5, bgcolor="#232830"),
             mouse_cursor=getattr(ft.MouseCursor, "RESIZE_COLUMN", None), on_horizontal_drag_update=drag)
    strip = W(ft.Container, ib(ft.Icons.FOLDER_OUTLINED, "Explorador (Ctrl+B)", toggle_sb), width=40, bgcolor=BAR,
              padding=pad(0, 6))

    # ---------- menú ----------
    def mi(label, fn, key=""):
        return W(ft.MenuItemButton,
                 content=ft.Row([ft.Text(label, size=13), ft.Text(key, size=12, color=MUTED)],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=270),
                 on_click=lambda e: fn())

    def sm(title, items):
        return W(ft.SubmenuButton, content=ft.Text(title, size=13), controls=items, on_open=lambda e: hide_win(),
                 on_close=lambda e: back_win(), menu_style=ft.MenuStyle(bgcolor=BAR))

    div = lambda: ft.Divider(height=1, color="#232830")
    menubar = W(ft.MenuBar, style=ft.MenuStyle(bgcolor=BAR, elevation=0), controls=[
        sm("Archivo", [mi("Nuevo", new, "Ctrl+N"), mi("Nueva ventana", new_window, "Ctrl+Shift+N"),
                       mi("Abrir…", open_file, "Ctrl+O"), mi("Abrir carpeta…", open_folder, "Ctrl+Shift+O"), mi("Guardar", save, "Ctrl+S"),
                       mi("Guardar como…", lambda: save(True), "Ctrl+Shift+S"), div(),
                       mi("Imprimir", print_file, "Ctrl+P"), div(), mi("Salir", exit_app)]),
        sm("Edición", [mi("Deshacer", undo, "Ctrl+Z"), mi("Rehacer", redo, "Ctrl+Y"), div(),
                       mi("Cortar", cut, "Ctrl+X"), mi("Copiar", copy, "Ctrl+C"),
                       mi("Pegar", paste, "Ctrl+V"), mi("Eliminar", delete, "Supr"), div(),
                       mi("Buscar…", find_dialog, "Ctrl+F"), mi("Buscar siguiente", find_next, "F3"),
                       mi("Reemplazar…", lambda: find_dialog(True), "Ctrl+H"),
                       mi("Ir a…", goto, "Ctrl+G"), div(),
                       mi("Seleccionar todo", select_all, "Ctrl+A"), mi("Hora y fecha", now, "F5")]),
        sm("Formato", [mi("Aumentar fuente", lambda: zoom(2), "Ctrl++"),
                       mi("Reducir fuente", lambda: zoom(-2), "Ctrl+-"),
                       mi("Fuente predeterminada", lambda: zoom(0), "Ctrl+0")]),
        sm("Ver", [mi("Alternar edición / vista", set_mode, "Ctrl+E"),
                   mi("Explorador de archivos", toggle_sb, "Ctrl+B"),
                   mi("Barra de estado", toggle_status), mi("Pantalla completa", fullscreen, "F11")]),
        sm("Ayuda", [mi("Acerca de", about)]),
    ])

    # ---------- atajos ----------
    def on_key(e):
        k = e.key
        if e.ctrl:
            acts = {"N": new_window if e.shift else new, "O": open_folder if e.shift else open_file, "S": lambda: save(e.shift),
                    "P": print_file, "F": find_dialog, "H": lambda: find_dialog(True), "G": goto,
                    "E": set_mode, "B": toggle_sb, "Y": redo, "0": lambda: zoom(0), "Equal": lambda: zoom(2),
                    "=": lambda: zoom(2), "+": lambda: zoom(2), "Minus": lambda: zoom(-2),
                    "-": lambda: zoom(-2)}
            f = acts.get(k.upper() if len(k) == 1 else k)
            if f:
                f()
        elif k == "F5":
            now()
        elif k == "F3":
            find_next()
        elif k == "F11":
            fullscreen()

    page.on_keyboard_event = on_key
    page.add(ft.Column([W(ft.Container, ft.Row([menubar, ft.Container(expand=True), vbtn], vertical_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=BAR, height=48),
                       ft.Row([strip, sidebar, grip, body], spacing=0, expand=True,
                              vertical_alignment=ft.CrossAxisAlignment.STRETCH), status_bar],
                       spacing=0, expand=True))
    a1 = sys.argv[1] if len(sys.argv) > 1 else ""
    if os.path.isdir(a1):
        S.update(root=a1, cur=a1, exp={a1})
    fit()
    build_tree()
    if os.path.isfile(a1):
        load(a1)
    else:
        refresh()


if __name__ == "__main__":
    (ft.run if hasattr(ft, "run") else ft.app)(main)
