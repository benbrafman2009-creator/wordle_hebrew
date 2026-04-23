import time

import customtkinter as ctk

import socket
import tkinter as tk
import const

NUM_ROWS  = 6
NUM_COLS  = 5
TILE_SIZE = 64
IP = "127.0.0.1"

# ── Palette ───────────────────────────────────────────
BG          = "#121213"
HEADER_BG   = "#1a1a1b"
DIVIDER     = "#3a3a3c"
TEXT_COLOR  = "#ffffff"
BORDER_IDLE = "#565758"
BORDER_CUR  = "#ffffff"
HINT_COLOR  = "#818384"
ACCENT      = "#538d4e"
ACCENT_HOVER= "#6aaf60"
BTN_SECONDARY    = "#2a2a2b"
BTN_SECONDARY_HV = "#3a3a3c"

COLOR_MAP = {
    "green":  "#538d4e",
    "yellow": "#b59f3b",
    "black":   "#3a3a3c",
    "empty":  "#121213",
}

_TS = max(36, min(TILE_SIZE, 500 // NUM_COLS))
_FS = max(13, _TS // 3)


# ══════════════════════════════════════════════════════
#  COMMUNICATION
# ══════════════════════════════════════════════════════
class HandelCommunication(socket.socket):
    def __init__(self):
        super().__init__()
        self.connect((IP, const.PORT))

    def _raw_recv(self, buffersize=2048, flags=0):
        size_header = b''
        while len(size_header) < const.size_header_size:
            chunk = super().recv(const.size_header_size - len(size_header), flags)
            if not chunk:
                return ''
            size_header += chunk
        try:
            data_len = int(size_header[:const.size_header_size - 1])
        except ValueError:
            return ''
        data = b''
        while len(data) < data_len:
            chunk = super().recv(data_len - len(data), flags)
            if not chunk:
                return ''
            data += chunk
        if const.TCP_DEBUG:
            print(f"\nRecv({data_len})>>>{data[:const.LEN_TO_PRINT]}")
        return data.decode()

    def send(self, bdata, flags=0):
        if type(bdata) != bytes:
            bdata = bdata.encode()
        header_data = str(len(bdata)).zfill(const.size_header_size - 1).encode() + b"|"
        super().send(header_data + bdata)
        if const.TCP_DEBUG:
            print(f"\nSent {len(bdata)})>>>{bdata[:const.LEN_TO_PRINT]}")


# ══════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════
def make_btn(parent, text, command, primary=True, width=260):
    bg  = ACCENT          if primary else BTN_SECONDARY
    hov = ACCENT_HOVER    if primary else BTN_SECONDARY_HV
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=TEXT_COLOR, activebackground=hov, activeforeground=TEXT_COLOR,
        font=("David", 14, "bold"), relief="flat", cursor="hand2",
        width=0, padx=0, pady=12, bd=0
    )
    btn.pack(pady=6, ipadx=0)
    btn.config(width=width // 10)

    # Hover effect
    btn.bind("<Enter>", lambda e: btn.config(bg=hov))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn

def make_label(parent, text, size=13, color=HINT_COLOR, bold=False):
    weight = "bold" if bold else "normal"
    lbl = tk.Label(parent, text=text, bg=BG, fg=color,
                   font=("David", size, weight))
    lbl.pack(pady=(4, 0))
    return lbl

def make_entry(parent, placeholder="", width=28):
    entry = tk.Entry(
        parent, bg="#1e1e1f", fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
        font=("David", 13), relief="flat", bd=0,
        highlightthickness=2, highlightcolor=ACCENT, highlightbackground=DIVIDER,
        width=width, justify="right"
    )
    entry.pack(pady=6, ipady=8)
    if placeholder:
        entry.insert(0, placeholder)
        entry.config(fg=HINT_COLOR)
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg=TEXT_COLOR)
        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=HINT_COLOR)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    return entry

def make_type_selector(parent, var):
    """Radio buttons for word length selection (5–8)."""
    frame = tk.Frame(parent, bg=BG)
    frame.pack(pady=8)
    make_label(parent, "בחר אורך מילה:", size=12)
    row = tk.Frame(parent, bg=BG)
    row.pack(pady=4)
    for val in [5, 6, 7, 8]:
        rb = tk.Radiobutton(
            row, text=str(val), variable=var, value=val,
            bg=BG, fg=TEXT_COLOR, selectcolor="#2a2a2b",
            activebackground=BG, activeforeground=TEXT_COLOR,
            font=("David", 13, "bold"), cursor="hand2",
            indicatoron=0, relief="flat",
            padx=14, pady=8,
            highlightthickness=0, bd=0
        )
        rb.pack(side="left", padx=4)

        def on_enter(e, b=rb): b.config(bg=BTN_SECONDARY_HV)
        def on_leave(e, b=rb, v=val, sv=var):
            b.config(bg="#2a2a2b" if sv.get() == v else BG)
        rb.bind("<Enter>", on_enter)
        rb.bind("<Leave>", on_leave)


def clear_window(win):
    for widget in win.winfo_children():
        widget.destroy()

def draw_header(win, subtitle=""):
    hdr = tk.Frame(win, bg=HEADER_BG, pady=14)
    hdr.pack(fill="x")
    tk.Label(hdr, text="W O R D L E  –  עברית",
             bg=HEADER_BG, fg=TEXT_COLOR,
             font=("Helvetica", 20, "bold")).pack()
    if subtitle:
        tk.Label(hdr, text=subtitle,
                 bg=HEADER_BG, fg=HINT_COLOR,
                 font=("David", 11)).pack()
    tk.Frame(win, bg=DIVIDER, height=1).pack(fill="x")


# ══════════════════════════════════════════════════════
#  START PAGE
# ══════════════════════════════════════════════════════
def show_start_page(win, server):
    clear_window(win)
    win.title("Wordle – עברית")

    draw_header(win)

    body = tk.Frame(win, bg=BG, pady=30)
    body.pack(expand=True)

    make_label(body, "ברוך הבא! בחר מצב משחק:", size=15, color=TEXT_COLOR, bold=True)
    tk.Frame(body, bg=BG, height=16).pack()

    make_btn(body, "🏠  צור חדר", lambda: show_create_room(win, server), primary=True)
    make_btn(body, "🔍  הצטרף לחדר", lambda: show_join_room(win, server), primary=False)
    make_btn(body, "🎮  שחק לבד",   lambda: show_solo(win, server),      primary=False)


# ══════════════════════════════════════════════════════
#  CREATE ROOM PAGE
# ══════════════════════════════════════════════════════
def show_create_room(win, server):
    clear_window(win)
    draw_header(win, "צור חדר חדש")

    body = tk.Frame(win, bg=BG, pady=24)
    body.pack(expand=True)

    make_label(body, "שם החדר:", size=12)
    name_entry = make_entry(body, placeholder="הכנס שם לחדר…")

    word_len = tk.IntVar(value=5)
    make_type_selector(body, word_len)

    msg_lbl = make_label(body, "", size=11, color="#e05252")

    def on_create():
        name = name_entry.get().strip()
        if not name or name == "הכנס שם לחדר…":
            msg_lbl.config(text="⚠  יש להכניס שם לחדר")
            return
        payload = f"{const.create_room}{name};{word_len.get()}"
        server.send(payload)
        msg_lbl.config(text="ממתין לשחקנים…", fg=HINT_COLOR)

    tk.Frame(body, bg=BG, height=10).pack()
    make_btn(body, "✔  צור חדר", on_create, primary=True)
    make_btn(body, "← חזור",     lambda: show_start_page(win, server), primary=False)


# ══════════════════════════════════════════════════════
#  JOIN ROOM PAGE
# ══════════════════════════════════════════════════════
def show_join_room(win, server):
    clear_window(win)
    draw_header(win, "הצטרף לחדר")

    body = tk.Frame(win, bg=BG, pady=24)
    body.pack(expand=True, fill="both")

    status_lbl = make_label(body, "מחפש חדרים פתוחים…", size=12, color=HINT_COLOR)

    list_frame = tk.Frame(body, bg=BG)
    list_frame.pack(pady=10, fill="both", expand=True)

    # Send request for room list
    server.send(const.ask_for_rooms)
    raw = server._raw_recv()
    rooms = [r.strip() for r in raw.split(",") if r.strip()]

    if not rooms:
        status_lbl.config(text="לא נמצאו חדרים פתוחים")
    else:
        status_lbl.config(text=f"נמצאו {len(rooms)} חדרים:")
        for room in rooms:
            def on_join(r=room):
                server.send(f"{const.join};{r}")
                # After joining, transition to game (handled by server flow)
                show_game(win, server)

            rf = tk.Frame(list_frame, bg=BTN_SECONDARY, pady=10, padx=16, cursor="hand2")
            rf.pack(fill="x", padx=24, pady=3)
            tk.Label(rf, text=room, bg=BTN_SECONDARY, fg=TEXT_COLOR,
                     font=("David", 13), anchor="e", justify="right").pack(side="right")
            tk.Button(rf, text="הצטרף", command=on_join,
                      bg=ACCENT, fg=TEXT_COLOR, activebackground=ACCENT_HOVER,
                      font=("David", 11, "bold"), relief="flat",
                      cursor="hand2", padx=10, pady=4).pack(side="left")

    tk.Frame(body, bg=BG, height=10).pack()
    make_btn(body, "← חזור", lambda: show_start_page(win, server), primary=False)


# ══════════════════════════════════════════════════════
#  SOLO PAGE
# ══════════════════════════════════════════════════════
def show_solo(win, server):
    clear_window(win)
    draw_header(win, "שחק לבד")

    body = tk.Frame(win, bg=BG, pady=28)
    body.pack(expand=True)

    word_len = tk.IntVar(value=5)
    make_type_selector(body, word_len)

    msg_lbl = make_label(body, "", size=11, color=HINT_COLOR)

    def on_start():
        payload = f"{const.play_solo};{word_len.get()}"
        server.send(payload)
        msg_lbl.config(text="ממתין לאישור שרת…")
        win.after(100, wait_for_accept)

    def wait_for_accept():
        response = server._raw_recv()
        if response.strip() == const.start_solo_game:
            show_game(win, server, word_len.get())
        else:
            msg_lbl.config(text=f"שגיאה: {response}", fg="#e05252")

    tk.Frame(body, bg=BG, height=10).pack()
    make_btn(body, "▶  התחל משחק", on_start, primary=True)
    make_btn(body, "← חזור", lambda: show_start_page(win, server), primary=False)


# ══════════════════════════════════════════════════════
#  GAME PAGE  (your original HebrewWordle, embedded)
# ══════════════════════════════════════════════════════
def show_game(win, server, num_cols=5):
    clear_window(win)

    # Load dictionary
    with open("index.dic", encoding="utf-8") as f:
        dictionary = [line.split("/")[0] for line in f.read().splitlines()]

    def is_correct(word):
        return word in dictionary

    num_rows = 6
    tile_size = 64
    ts  = max(36, min(tile_size, 500 // num_cols))
    fs  = max(13, ts // 3)

    tiles       = []
    tile_letter = [[""] * num_cols for _ in range(num_rows)]
    tile_color  = [["empty"] * num_cols for _ in range(num_rows)]
    state       = {"cur_row": 0, "cur_typed": 0}

    def next_col():
        return num_cols - 1 - state["cur_typed"]

    def draw_tile(r, c):
        cv = tiles[r][c]
        cv.delete("all")
        s = ts
        fill   = COLOR_MAP[tile_color[r][c]]
        letter = tile_letter[r][c].strip()
        is_cur = (r == state["cur_row"] and c == next_col())
        border = BORDER_CUR if is_cur else BORDER_IDLE
        bw     = 3 if is_cur else 2
        pts = [1+5,1, s-1-5,1, s-1,1, s-1,1+5,
               s-1,s-1-5, s-1,s-1, s-1-5,s-1, 1+5,s-1,
               1,s-1, 1,s-1-5, 1,1+5, 1,1]
        cv.create_polygon(pts, smooth=True, fill=fill, outline=border, width=bw)
        if letter:
            cv.create_text(s//2, s//2, text=letter, fill=TEXT_COLOR,
                           font=("David", fs, "bold"))

    def refresh_row(r):
        for c in range(num_cols):
            draw_tile(r, c)

    def update_hint():
        if state["cur_row"] >= num_rows:
            hint.config(text="הלוח מלא")
            return
        left = num_cols - state["cur_typed"]
        word = "".join(list(reversed(tile_letter[state["cur_row"]])))
        if left == 0 and is_correct(word):
            hint.config(text="לחץ Enter לשורה הבאה ↵", fg=HINT_COLOR)
        elif left == 0 and not is_correct(word):
            hint.config(text="המילה לא קיימת בשפה העברית", fg="#e05252")
        else:
            hint.config(text=f"שורה {state['cur_row']+1}  •  נותרו {left} אותיות", fg=HINT_COLOR)

    def type_char(ch):
        if state["cur_row"] >= num_rows or state["cur_typed"] >= num_cols:
            return
        c = num_cols - 1 - state["cur_typed"]
        tile_letter[state["cur_row"]][c] = ch
        state["cur_typed"] += 1
        refresh_row(state["cur_row"])
        update_hint()

    def backspace():
        if state["cur_typed"] == 0:
            return
        state["cur_typed"] -= 1
        c = num_cols - 1 - state["cur_typed"]
        tile_letter[state["cur_row"]][c] = " "
        refresh_row(state["cur_row"])
        update_hint()

    def set_tile_color(row, col, color):
        tile_color[row][col] = color
        draw_tile(row, col)

    def set_row_colors(row, colors):
        for col, color in enumerate(list(reversed(colors))):
            set_tile_color(row, col, color)

    def submit_row():
        r = state["cur_row"]
        if r >= num_rows - 1:
            return
        if not all(tile_letter[r]):
            return
        word = "".join(list(reversed(tile_letter[r])))
        if not is_correct(word):
            update_hint()
            return
        state["cur_row"]  += 1
        state["cur_typed"] = 0
        server.send(const.word + word)
        color_str = server._raw_recv()
        if color_str[:5] == "color":
            color_list = []
            for ch in color_str[5:]:
                color_list.append(next((w for w in COLOR_MAP.keys() if w.startswith(ch)), None))
            set_row_colors(r, color_list)
            win_game = all(color == "green" for color in color_list)
            refresh_row(r)
            refresh_row(state["cur_row"])
            update_hint()
            if win_game:
                win.after(2000,lambda: show_start_page(win, server))

    def on_key(event):
        sym  = event.keysym
        char = event.char
        if sym == "BackSpace":
            backspace()
        elif sym in ("Return", "KP_Enter"):
            submit_row()
        elif char and char.isprintable() and len(char) == 1:
            type_char(char)

    # ── Build UI ──────────────────────────────────────
    draw_header(win)

    gf = tk.Frame(win, bg=BG, padx=20, pady=18)
    gf.pack()
    for r in range(num_rows):
        row = []
        for c in range(num_cols):
            cv = tk.Canvas(gf, width=ts, height=ts,
                           bg=BG, highlightthickness=0, cursor="arrow")
            cv.grid(row=r, column=c, padx=3, pady=3)
            row.append(cv)
        tiles.append(row)

    for r in range(num_rows):
        for c in range(num_cols):
            draw_tile(r, c)

    tk.Frame(win, bg=DIVIDER, height=1).pack(fill="x")
    hint = tk.Label(win, text="התחל להקליד…",
                    bg=BG, fg=HINT_COLOR,
                    font=("Helvetica", 11), pady=10)
    hint.pack()

    # Back to menu button
    tk.Button(win, text="← תפריט ראשי",
              command=lambda: show_start_page(win, server),
              bg=BG, fg=HINT_COLOR, activebackground=BTN_SECONDARY,
              activeforeground=TEXT_COLOR, font=("David", 10),
              relief="flat", cursor="hand2", pady=4).pack()

    win.bind("<Key>", on_key)
    win.focus_force()


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG)
    root.resizable(False, False)

    server = HandelCommunication()

    # Center window helper
    def center(w):
        w.update_idletasks()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        ww, wh = w.winfo_width(), w.winfo_height()
        w.geometry(f"+{(sw-ww)//2}+{(sh-wh)//2}")

    show_start_page(root, server)
    root.update()
    center(root)
    root.mainloop()