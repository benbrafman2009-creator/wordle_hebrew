
import customtkinter as tkcu
import socket
import threading
import tkinter as tk
import const
NUM_ROWS  = 6     # number of guess rows
NUM_COLS  = 5     # letters per row (between 5 and 8)
TILE_SIZE = 64
IP = "127.0.0.1" #TODO: create a udp proxy that sends the ip of the server.
PORT = 8080
# ── Palette ───────────────────────────────────────────
BG          = "#121213"
HEADER_BG   = "#1a1a1b"
DIVIDER     = "#3a3a3c"
TEXT_COLOR  = "#ffffff"
BORDER_IDLE = "#565758"
BORDER_CUR  = "#ffffff"
HINT_COLOR  = "#818384"

COLOR_MAP = {
    "green":  "#538d4e",
    "yellow": "#b59f3b",
    "gray":   "#3a3a3c",
    "empty":  "#121213",
}

# Auto-scale tile size for wide boards
_TS  = max(36, min(TILE_SIZE, 500 // NUM_COLS))
_FS  = max(13, _TS // 3)

class HandelCommunication(socket.socket):
    def __init__(self):
        super().__init__()
        self.connect((IP, PORT))
class HebrewWordle(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wordle – עברית")
        self.configure(bg=BG)
        self.resizable(False, False)

        # Board state
        self.tiles       = []
        self.tile_letter = [[" "] * NUM_COLS for _ in range(NUM_ROWS)]
        self.tile_color  = [["empty"] * NUM_COLS for _ in range(NUM_ROWS)]

        # Typing cursor
        self.cur_row   = 0   # active row
        self.cur_typed = 0   # letters typed so far in current row

        self._build_ui()
        self.focus_force()
        self.bind("<Key>", self._on_key)
        self._center_window()
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=HEADER_BG, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="W O R D L E  –  עברית",
                 bg=HEADER_BG, fg=TEXT_COLOR,
                 font=("Helvetica", 20, "bold")).pack()
        tk.Frame(self, bg=DIVIDER, height=1).pack(fill="x")

        # Tile grid
        gf = tk.Frame(self, bg=BG, padx=20, pady=18)
        gf.pack()
        for r in range(NUM_ROWS):
            row = []
            for c in range(NUM_COLS):
                cv = tk.Canvas(gf, width=_TS, height=_TS,
                               bg=BG, highlightthickness=0, cursor="arrow")
                cv.grid(row=r, column=c, padx=3, pady=3)
                cv.bind("<Button-1>", lambda e, rr=r, cc=c: self._click_tile(rr, cc))
                row.append(cv)
            self.tiles.append(row)

        # Initial draw
        for r in range(NUM_ROWS):
            for c in range(NUM_COLS):
                self._draw_tile(r, c)

        # Status / hint bar
        tk.Frame(self, bg=DIVIDER, height=1).pack(fill="x")
        self.hint = tk.Label(self, text="התחל להקליד…",
                             bg=BG, fg=HINT_COLOR,
                             font=("Helvetica", 11), pady=10)
        self.hint.pack()

    def _draw_tile(self, r, c):
        cv = self.tiles[r][c]
        cv.delete("all")
        s = _TS

        fill   = COLOR_MAP[self.tile_color[r][c]]
        letter = self.tile_letter[r][c].strip()
        is_cur = (r == self.cur_row and c == self._next_col())
        border = BORDER_CUR if is_cur else BORDER_IDLE
        bw     = 3 if is_cur else 2

        # Rounded rectangle tile
        self._rrect(cv, 1, 1, s-1, s-1, 5, fill=fill, outline=border, width=bw)

        # Letter
        if letter:
            cv.create_text(s // 2, s // 2,
                           text=letter, fill=TEXT_COLOR,
                           font=("David", _FS, "bold"))

    def _rrect(self, cv, x1, y1, x2, y2, radius, **kw):
        r = radius
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        cv.create_polygon(pts, smooth=True, **kw)

    def _next_col(self):
        """Column index (0-based from left) of the NEXT letter to be typed."""
        return NUM_COLS - 1 - self.cur_typed

    def _refresh_row(self, r):
        for c in range(NUM_COLS):
            self._draw_tile(r, c)

    # ─────────────────────────────────────────────────
    #  KEYBOARD INPUT
    # ─────────────────────────────────────────────────
    def _on_key(self, event):
        sym  = event.keysym
        char = event.char

        if sym == "BackSpace":
            self._backspace()
        elif sym in ("Return", "KP_Enter"):
            self._next_row()
        elif char and char.isprintable() and len(char) == 1:
            self._type(char)

    def _type(self, ch):
        if self.cur_row >= NUM_ROWS or self.cur_typed >= NUM_COLS:
            return
        c = NUM_COLS - 1 - self.cur_typed
        self.tile_letter[self.cur_row][c] = ch
        self.cur_typed += 1
        self._refresh_row(self.cur_row)
        self._update_hint()

    def _backspace(self):
        if self.cur_typed == 0:
            return
        self.cur_typed -= 1
        c = NUM_COLS - 1 - self.cur_typed
        self.tile_letter[self.cur_row][c] = " "
        self._refresh_row(self.cur_row)
        self._update_hint()

    def _next_row(self):
        if self.cur_row < NUM_ROWS - 1:
            self.cur_row  += 1
            self.cur_typed = 0
            self._refresh_row(self.cur_row - 1)
            self._refresh_row(self.cur_row)
            self._update_hint()

    def _click_tile(self, r, c):
        """Click any row to jump there and re-edit it."""
        self._refresh_row(self.cur_row)
        self.cur_row   = r
        self.cur_typed = 0
        # Count existing letters in that row (right → left fills, so scan from right)
        for col in range(NUM_COLS - 1, -1, -1):
            if self.tile_letter[r][col].strip():
                self.cur_typed = NUM_COLS - col
                break
        self._refresh_row(self.cur_row)
        self._update_hint()

    def _update_hint(self):
        if self.cur_row >= NUM_ROWS:
            self.hint.config(text="הלוח מלא")
            return
        left = NUM_COLS - self.cur_typed
        if left == 0:
            self.hint.config(text="לחץ Enter לשורה הבאה ↵")
        else:
            self.hint.config(text=f"שורה {self.cur_row + 1}  •  נותרו {left} אותיות")

    def set_tile_color(self, row: int, col: int, color: str):
        if color not in COLOR_MAP:
            raise ValueError(f"Unknown color '{color}'. Use: {list(COLOR_MAP)}")
        self.tile_color[row][col] = color
        self._draw_tile(row, col)

    def set_row_colors(self, row: int, colors: list):
        """
        Color all tiles in a row.
        colors : list of NUM_COLS color strings  (index 0 = leftmost tile)
        """
        for col, color in enumerate(colors):
            self.set_tile_color(row, col, color)

    def set_all_colors(self, grid: list):
        """
        Color the entire board.
        grid : list of rows, each a list of NUM_COLS color strings
        """
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                self.set_tile_color(r, c, color)

    # ─────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────
    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")


# ══════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    app = HebrewWordle()

    # ── Quick demo: color row 0 from the "backend" after 3 s ────
    def _demo():
        app.set_row_colors(0, ["green", "yellow", "gray", "gray", "green"])

    app.after(3000, _demo)   # remove this block when integrating your own backend

    app.mainloop()