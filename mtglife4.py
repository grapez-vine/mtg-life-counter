import curses
import sys
from art import text2art  # Requires: pip install art

# Standard color mapping for curses with distinct Orange and Yellow
COLOR_MAP = {
    "Red": curses.COLOR_RED,
    "Green": curses.COLOR_GREEN,
    "Blue": curses.COLOR_BLUE,
    "Yellow": curses.COLOR_YELLOW,
    "Orange": 208,  # 256-color code for vibrant orange
    "Cyan": curses.COLOR_CYAN,
    "Magenta": curses.COLOR_MAGENTA,
    "White": curses.COLOR_WHITE,
}

COLOR_NAMES = list(COLOR_MAP.keys())

MTG_LOGO = [
    r"            _____     _____        ___  _.     __  ____  ____.          _      ",
    r"           `~-,  \   `~-,  \       ~-_~~ \    /  ~~   / (    /' ,-~~~~~~,'     ",
    r"             /    \    /'   \      /~>\   \  (  /~~~\/   )  | .'  /~~~)/       ",
    r"            /      \  /      \    / /  \   \ | | ~==~~|  |  | |  (    '        ",
    r"           /',/\    \/ '/\    \  / <_,'>\   \ \ \___) |  |  | |   \_  _____    ",
    r"          /  /  \      /  \    \/     /  \   \ \  __  |  )  ( _`-_  ~~ ____]=='",
    "         /  /    \\     |   \\    \\~~~~~    `~~~~ ~~  ~\\|(=~~~~~'   `~~~~___.   .",
    r"        /  /      \     \   \    \    ___         _                     | |\ /|",
    r"       /  /        |     |   \    \   `|''|      / '  _._|      .,_  _  | | V |",
    r"      /  /          \     \   \    \   |  |^ %) | __'T T |^ %)/^|| )/ \        ",
    r"     /  (            |     |   \    \ .|. | |\,  \_|(] | | |\,[ || |\_/        ",
    r"    /    \,           \     \   \    \             '                 \         ",
    r"   /___---'            | ,-'~   .)    `.                            (~)        ",
    r".=~~                   `~       `~~~~~~~'                            ~         "
]

def render_ascii_art(text, font_name='doom', max_width=60, max_lines=10):
    """Generates ASCII art using the 'art' library scaled safely to fit panes."""
    text = str(text).strip() or "0"
    try:
        art_str = text2art(text, font=font_name)
        lines = [line for line in art_str.split('\n') if line.strip()]
        if not lines:
            lines = [text]
        formatted = []
        for l in lines[:max_lines]:
            if len(l) > max_width:
                l = l[:max_width]
            formatted.append(l)
        while len(formatted) < max_lines:
            formatted.append("")
        return formatted
    except Exception:
        return [text[:max_width]] + [""] * (max_lines - 1)

class Player:
    def __init__(self, name, color_name, starting_life=40, custom_rgb=None, deck_name="Standard"):
        self.name = name
        self.color_name = color_name
        self.life = starting_life
        self.commander_damage = 0
        self.eliminated = False
        self.overkill = False
        self.custom_rgb = custom_rgb
        self.deck_name = deck_name
        self.click_zones = {}

class MTGCounterApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)

        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

        curses.start_color()
        curses.use_default_colors()

        try:
            curses.init_pair(99, curses.COLOR_CYAN, -1)
        except curses.error:
            pass

        self.players = []
        self.num_players = 2
        self.starting_life = 40
        self.track_commander_damage = True
        self.setup_boxes = {}
        self.start_button_box = None
        self.setup_game()

    def hex_to_rgb1000(self, hex_str):
        hex_str = hex_str.strip().lstrip('#')
        if len(hex_str) != 6:
            return None
        try:
            r = int(hex_str[0:2], 16) * 1000 // 255
            g = int(hex_str[2:4], 16) * 1000 // 255
            b = int(hex_str[4:6], 16) * 1000 // 255
            return (r, g, b)
        except ValueError:
            return None

    def prompt_user_input(self, prompt_text):
        curses.curs_set(1)
        h, w = self.stdscr.getmaxyx()
        input_win = curses.newwin(3, 60, h // 2 - 1, w // 2 - 30)
        input_win.box()
        input_win.addstr(1, 2, prompt_text)
        input_win.refresh()

        curses.echo()
        s = input_win.getstr(1, len(prompt_text) + 3, 30).decode('utf-8', errors='ignore')
        curses.noecho()
        curses.curs_set(0)
        return s.strip()

    def setup_game(self):
        default_colors = ["Red", "Blue", "Green", "White", "Orange"]
        if len(self.players) != self.num_players:
            self.players = [
                Player(f"Player {i+1}", default_colors[i % len(default_colors)], self.starting_life, deck_name=f"Player {i+1}")
                for i in range(self.num_players)
            ]

        # Initialize vibrant standard curses color pairs for rainbow gradients
        try:
            curses.init_pair(50, curses.COLOR_RED, -1)
            curses.init_pair(51, curses.COLOR_YELLOW, -1)
            curses.init_pair(52, curses.COLOR_GREEN, -1)
            curses.init_pair(53, curses.COLOR_CYAN, -1)
            curses.init_pair(54, curses.COLOR_BLUE, -1)
            curses.init_pair(55, curses.COLOR_MAGENTA, -1)
        except curses.error:
            pass

        rainbow_pairs = [50, 51, 52, 53, 54, 55]
        color_cycle_idx = 0

        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()

            if h < 36 or w < 90:
                self.stdscr.addstr(0, 0, "Terminal too small! Resize to at least 90x36.")
                self.stdscr.refresh()
                curses.napms(100)
                continue

            # 1. Render MTG Logo with vibrant curses rainbow gradient
            logo_start_x = max(2, (w - len(MTG_LOGO[0])) // 2)
            for idx, line in enumerate(MTG_LOGO):
                for char_idx, char in enumerate(line):
                    if char.strip():
                        pair_idx = rainbow_pairs[(color_cycle_idx + idx + char_idx) % len(rainbow_pairs)]
                        attr = curses.color_pair(pair_idx) | curses.A_BOLD
                        try:
                            self.stdscr.addch(1 + idx, logo_start_x + char_idx, char, attr)
                        except curses.error:
                            pass

            # 2. Control toggles (Players, Life, Cmdr Dmg) centered
            ctrl_y = 17
            p_text = f"[P] Players: < {self.num_players} >"
            l_text = f"[L] Life: < {self.starting_life} >"
            cmdr_status = "ON" if self.track_commander_damage else "OFF"
            c_text = f"[C] Cmdr Dmg: < {cmdr_status} >"

            ctrls_combined = f"{p_text}     {l_text}     {c_text}"
            ctrl_x = (w - len(ctrls_combined)) // 2

            self.stdscr.addstr(ctrl_y, ctrl_x, p_text, curses.A_BOLD | curses.A_REVERSE)
            self.stdscr.addstr(ctrl_y, ctrl_x + len(p_text) + 5, l_text, curses.A_BOLD | curses.A_REVERSE)
            self.stdscr.addstr(ctrl_y, ctrl_x + len(p_text) + len(l_text) + 10, c_text, curses.A_BOLD | curses.A_REVERSE)

            self.setup_boxes = {}
            self.setup_boxes["players"] = (ctrl_y, ctrl_x, ctrl_x + len(p_text))
            self.setup_boxes["life"] = (ctrl_y, ctrl_x + len(p_text) + 5, ctrl_x + len(p_text) + 5 + len(l_text))
            self.setup_boxes["cmdr"] = (ctrl_y, ctrl_x + len(p_text) + len(l_text) + 10, ctrl_x + len(p_text) + len(l_text) + 10 + len(c_text))

            # 3. Horizontal Player Config Boxes
            box_w = 32
            total_w = self.num_players * box_w + (self.num_players - 1) * 2
            start_px = (w - total_w) // 2
            p_start_y = 20

            self.setup_boxes["players_config"] = []
            for i, p in enumerate(self.players):
                bx = start_px + i * (box_w + 2)

                # Set up player color (Orange uses 208, Yellow uses COLOR_YELLOW)
                if p.custom_rgb and curses.can_change_color():
                    try:
                        curses.init_color(20 + i, p.custom_rgb[0], p.custom_rgb[1], p.custom_rgb[2])
                        curses.init_pair(10 + i, 20 + i, -1)
                    except curses.error:
                        curses.init_pair(10 + i, curses.COLOR_WHITE, -1)
                else:
                    c_code = COLOR_MAP.get(p.color_name, curses.COLOR_WHITE)
                    curses.init_pair(10 + i, c_code, -1)
                p_attr = curses.color_pair(10 + i) | curses.A_BOLD

                # Player # centered above matching player color
                p_label = f"Player {i+1}"
                self.stdscr.addstr(p_start_y, bx + (box_w - len(p_label)) // 2, p_label, p_attr | curses.A_UNDERLINE)

                # Name Box
                name_y = p_start_y + 2
                self.stdscr.addstr(name_y, bx, "┌" + "─" * (box_w - 2) + "┐", p_attr)
                self.stdscr.addstr(name_y + 1, bx, "│", p_attr)
                self.stdscr.addstr(name_y + 1, bx + box_w - 1, "│", p_attr)
                self.stdscr.addstr(name_y + 2, bx, "└" + "─" * (box_w - 2) + "┘", p_attr)

                name_str = f"Name(N): {p.deck_name}"
                if len(name_str) > box_w - 4:
                    name_str = name_str[:box_w - 5] + "…"
                self.stdscr.addstr(name_y + 1, bx + (box_w - len(name_str)) // 2, name_str, p_attr)

                # Color Box
                color_y = name_y + 4
                self.stdscr.addstr(color_y, bx, "┌" + "─" * (box_w - 2) + "┐", p_attr)
                self.stdscr.addstr(color_y + 1, bx, "│", p_attr)
                self.stdscr.addstr(color_y + 1, bx + box_w - 1, "│", p_attr)
                self.stdscr.addstr(color_y + 2, bx, "└" + "─" * (box_w - 2) + "┘", p_attr)

                color_str = f"Color(C): {p.color_name}"
                self.stdscr.addstr(color_y + 1, bx + (box_w - len(color_str)) // 2, color_str, p_attr)

                self.setup_boxes["players_config"].append({
                    "name_zone": (name_y, name_y + 2, bx, bx + box_w - 1, i),
                    "color_zone": (color_y, color_y + 2, bx, bx + box_w - 1, i)
                })

            # 4. Start Game Button with curses rainbow gradient on both text AND box border
            start_art = [
                r"  ____ ___ ____ ____ ___    ____ ____ _  _ ____  ",
                r"  [__   |  |__| |__/  |     | __ |__| |\/| |___  ",
                r"  ___]  |  |  | |  \  |     |__] |  | |  | |___  "
            ]
            btn_box_w = len(start_art[0]) + 4
            btn_box_h = len(start_art) + 2
            btn_y = 31
            btn_x = (w - btn_box_w) // 2

            def get_grad_attr(r_idx, c_idx):
                pair_idx = rainbow_pairs[(color_cycle_idx + r_idx + c_idx) % len(rainbow_pairs)]
                return curses.color_pair(pair_idx) | curses.A_BOLD

            box_lines = [
                "╔" + "═" * (btn_box_w - 2) + "╗",
                *[ "║" + " " * (btn_box_w - 2) + "║" for _ in range(btn_box_h - 2) ],
                "╚" + "═" * (btn_box_w - 2) + "╝"
            ]
            for r_idx, bline in enumerate(box_lines):
                for c_idx, char in enumerate(bline):
                    if char != " ":
                        try:
                            self.stdscr.addch(btn_y + r_idx, btn_x + c_idx, char, get_grad_attr(r_idx, c_idx))
                        except curses.error:
                            pass

            for r_idx, line in enumerate(start_art):
                for c_idx, char in enumerate(line):
                    if char.strip():
                        try:
                            self.stdscr.addch(btn_y + 1 + r_idx, btn_x + 2 + c_idx, char, get_grad_attr(r_idx + 1, c_idx + 2))
                        except curses.error:
                            pass

            self.start_button_box = (btn_y, btn_y + btn_box_h - 1, btn_x, btn_x + btn_box_w - 1)

            self.stdscr.refresh()

            self.stdscr.nodelay(True)
            event = self.stdscr.getch()
            self.stdscr.nodelay(False)

            if event == -1:
                color_cycle_idx += 1
                curses.napms(100)
                continue

            if event == ord('q') or event == ord('Q'):
                sys.exit(0)
            elif event == ord('p') or event == ord('P'):
                self.num_players = (self.num_players % 4) + 1
                self.players = [
                    Player(f"Player {i+1}", default_colors[i % len(default_colors)], self.starting_life, deck_name=f"Player {i+1}")
                    for i in range(self.num_players)
                ]
            elif event == ord('l') or event == ord('L'):
                self.starting_life = 20 if self.starting_life == 40 else 40
            elif event == ord('c') or event == ord('C'):
                self.track_commander_damage = not self.track_commander_damage
            elif event in [ord('1'), ord('2'), ord('3'), ord('4')]:
                idx = event - ord('1')
                if idx < len(self.players):
                    p = self.players[idx]
                    p.custom_rgb = None
                    curr_idx = COLOR_NAMES.index(p.color_name) if p.color_name in COLOR_NAMES else 0
                    p.color_name = COLOR_NAMES[(curr_idx + 1) % len(COLOR_NAMES)]
            elif event in [ord('n'), ord('N')]:
                choice = self.prompt_user_input("Enter player number (1-4) to set Deck Name:")
                if choice in ['1', '2', '3', '4']:
                    idx = int(choice) - 1
                    if idx < len(self.players):
                        new_deck = self.prompt_user_input(f"Enter Deck Name for Player {idx+1}:")
                        if new_deck:
                            self.players[idx].deck_name = new_deck
            elif event == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, _ = curses.getmouse()
                    by_s, by_e, bx_s, bx_e = self.start_button_box
                    if by_s <= my <= by_e and bx_s <= mx <= bx_e:
                        break
                    if my == self.setup_boxes["players"][0] and self.setup_boxes["players"][1] <= mx <= self.setup_boxes["players"][2]:
                        self.num_players = (self.num_players % 4) + 1
                        self.players = [
                            Player(f"Player {i+1}", default_colors[i % len(default_colors)], self.starting_life, deck_name=f"Player {i+1}")
                            for i in range(self.num_players)
                        ]
                    elif my == self.setup_boxes["life"][0] and self.setup_boxes["life"][1] <= mx <= self.setup_boxes["life"][2]:
                        self.starting_life = 20 if self.starting_life == 40 else 40
                    elif my == self.setup_boxes["cmdr"][0] and self.setup_boxes["cmdr"][1] <= mx <= self.setup_boxes["cmdr"][2]:
                        self.track_commander_damage = not self.track_commander_damage
                    else:
                        for zones in self.setup_boxes["players_config"]:
                            ny1, ny2, nx1, nx2, p_idx = zones["name_zone"]
                            cy1, cy2, cx1, cx2, _ = zones["color_zone"]
                            if ny1 <= my <= ny2 and nx1 <= mx <= nx2:
                                new_deck = self.prompt_user_input(f"Enter Deck Name for Player {p_idx+1}:")
                                if new_deck:
                                    self.players[p_idx].deck_name = new_deck
                            elif cy1 <= my <= cy2 and cx1 <= mx <= cx2:
                                p = self.players[p_idx]
                                p.custom_rgb = None
                                curr_idx = COLOR_NAMES.index(p.color_name) if p.color_name in COLOR_NAMES else 0
                                p.color_name = COLOR_NAMES[(curr_idx + 1) % len(COLOR_NAMES)]
                except curses.error:
                    pass
            elif event == ord('\n') or event == ord('\r'):
                break

    def run(self):
        while True:
            self.draw_game_board()

            active_players = [p for p in self.players if not p.eliminated]
            if len(self.players) > 1 and len(active_players) <= 1:
                winner = active_players[0] if active_players else None
                if self.show_game_over_screen(winner):
                    return
            elif len(self.players) == 1 and self.players[0].eliminated:
                if self.show_game_over_screen(None):
                    return

            event = self.stdscr.getch()

            if event == ord('q') or event == ord('Q'):
                sys.exit(0)
            elif event == ord('r') or event == ord('R'):
                for p in self.players:
                    p.life = self.starting_life
                    p.commander_damage = 0
                    p.eliminated = False
                    p.overkill = False
            elif event == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, _ = curses.getmouse()
                    self.handle_mouse_click(mx, my)
                except curses.error:
                    pass
            elif event in [ord('1'), ord('2'), ord('3'), ord('4')]:
                p_idx = event - ord('1')
                if p_idx < len(self.players):
                    self.handle_advanced_keyboard_adjustment(p_idx)

    def handle_advanced_keyboard_adjustment(self, p_idx):
        p = self.players[p_idx]
        if p.eliminated:
            return
        val_str = self.prompt_user_input(f"{p.deck_name} Life (+/-num):")
        try:
            val = int(val_str)
            p.life += val
            if p.life <= 0:
                self.check_elimination(p, reason="life")
        except ValueError:
            pass

    def check_elimination(self, p, reason="life"):
        h, w = self.stdscr.getmaxyx()
        win_h, win_w = 9, 64
        win_y, win_x = h // 2 - win_h // 2, w // 2 - win_w // 2

        conf_win = curses.newwin(win_h, win_w, win_y, win_x)
        conf_win.keypad(True)
        conf_win.box()

        if reason == "commander":
            msg = f"{p.deck_name} [{p.color_name}] has reached 21 commander damage!"
        else:
            msg = f"{p.deck_name} [{p.color_name}] has reached {p.life} life!"

        conf_win.addstr(1, 4, msg)
        conf_win.addstr(2, 4, "Confirm elimination?")

        y_btn = " [ YES ] "
        n_btn = " [ NO ] "
        btn_y = 5
        y_x = 14
        n_x = 38

        for r in range(2):
            conf_win.addstr(btn_y + r, y_x, ' ' * len(y_btn), curses.A_REVERSE)
            conf_win.addstr(btn_y + r, n_x, ' ' * len(n_btn), curses.A_REVERSE)

        conf_win.addstr(btn_y, y_x + (len(y_btn) - len("[ YES ]")) // 2, "[ YES ]", curses.A_REVERSE | curses.A_BOLD)
        conf_win.addstr(btn_y, n_x + (len(n_btn) - len("[ NO ]")) // 2, "[ NO ]", curses.A_REVERSE | curses.A_BOLD)
        conf_win.refresh()

        y_zone = (win_y + btn_y, win_y + btn_y + 1, win_x + y_x, win_x + y_x + len(y_btn) - 1)
        n_zone = (win_y + btn_y, win_y + btn_y + 1, win_x + n_x, win_x + n_x + len(n_btn) - 1)

        while True:
            ev = conf_win.getch()
            if ev in [ord('y'), ord('Y')]:
                p.eliminated = True
                if p.life <= -25:
                    p.overkill = True
                break
            elif ev in [ord('n'), ord('N')]:
                break
            elif ev == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, _ = curses.getmouse()
                    if y_zone[0] <= my <= y_zone[1] and y_zone[2] <= mx <= y_zone[3]:
                        p.eliminated = True
                        if p.life <= -25:
                            p.overkill = True
                        break
                    elif n_zone[0] <= my <= n_zone[1] and n_zone[2] <= mx <= n_zone[3]:
                        break
                except curses.error:
                    pass

    def draw_game_board(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        for idx, p in enumerate(self.players):
            color_pair_id = idx + 1
            if p.custom_rgb and curses.can_change_color():
                try:
                    curses.init_color(10 + idx, p.custom_rgb[0], p.custom_rgb[1], p.custom_rgb[2])
                    curses.init_pair(color_pair_id, 10 + idx, -1)
                except curses.error:
                    curses.init_pair(color_pair_id, curses.COLOR_WHITE, -1)
            else:
                c_code = COLOR_MAP.get(p.color_name, curses.COLOR_WHITE)
                curses.init_pair(color_pair_id, c_code, -1)

        self.stdscr.addstr(0, 2, " MTG LIFE COUNTER ", curses.A_REVERSE)
        self.stdscr.addstr(0, w - 25, " [R]eset  [Q]uit ", curses.A_DIM)

        active_pane_players = [p for p in self.players if not p.eliminated]
        num_active = len(active_pane_players)

        if num_active == 0:
            boxes = []
        elif num_active == 1:
            boxes = [(2, 2, h - 4, w - 4, active_pane_players[0])]
        elif num_active == 2:
            half_h = h // 2
            boxes = [
                (2, 2, half_h - 1, w - 4, active_pane_players[0]),
                (half_h + 1, 2, h - half_h - 2, w - 4, active_pane_players[1])
            ]
        elif num_active == 3:
            half_h = h // 2
            half_w = w // 2
            boxes = [
                (2, 2, half_h - 1, half_w - 2, active_pane_players[0]),
                (2, half_w + 1, half_h - 1, w - half_w - 2, active_pane_players[1]),
                (half_h + 1, 2, h - half_h - 2, w - 4, active_pane_players[2])
            ]
        else:
            half_h = h // 2
            half_w = w // 2
            boxes = [
                (2, 2, half_h - 1, half_w - 2, active_pane_players[0]),
                (2, half_w + 1, half_h - 1, w - half_w - 2, active_pane_players[1]),
                (half_h + 1, 2, h - half_h - 2, half_w - 2, active_pane_players[2]),
                (half_h + 1, half_w + 1, h - half_h - 2, w - half_w - 2, active_pane_players[3])
            ]

        for by, bx, bh, bw, p in boxes:
            p_idx = self.players.index(p)
            attr = curses.color_pair(p_idx + 1) | curses.A_BOLD

            for row in range(by, by + bh):
                for col in range(bx, bx + bw):
                    if (row == by or row == by + bh - 1 or col == bx or col == bx + bw - 1):
                        if row < h - 1 and col < w - 1:
                            try:
                                self.stdscr.addch(row, col, '█', attr)
                            except curses.error:
                                pass

            if bh > 12 and bw > 30:
                deck_art = render_ascii_art(p.deck_name, font_name='doom', max_width=bw - 6, max_lines=9)
                for line_idx, ascii_line in enumerate(deck_art):
                    art_x = bx + (bw - len(ascii_line)) // 2
                    if by + 1 + line_idx < h - 1:
                        try:
                            self.stdscr.addstr(by + 1 + line_idx, art_x, ascii_line, attr | curses.A_DIM)
                        except curses.error:
                            pass

                life_art = render_ascii_art(str(p.life), font_name='epic', max_width=bw - 6, max_lines=9)
                life_y = by + 11

                p.click_zones = getattr(p, 'click_zones', {})
                p.click_zones["life_box"] = (life_y, life_y + len(life_art) - 1, bx + 2, bx + bw - 3)

                for line_idx, life_line in enumerate(life_art):
                    life_x = bx + (bw - len(life_line)) // 2
                    if life_y + line_idx < h - 1:
                        try:
                            self.stdscr.addstr(life_y + line_idx, life_x, life_line, attr | curses.A_STANDOUT)
                        except curses.error:
                            pass

                if self.track_commander_damage:
                    cmd_str = f"Cmdr Dmg: {p.commander_damage}/21"
                    if by + bh - 4 < h - 1:
                        try:
                            self.stdscr.addstr(by + bh - 4, bx + (bw - len(cmd_str)) // 2, cmd_str, attr)
                        except curses.error:
                            pass

                btn_y = by + bh - 3
                if btn_y < h - 1 and btn_y < by + bh - 1:
                    buttons = [
                        (" -10 ", "minus_10", 7),
                        (" -1 ", "minus_1", 6),
                        (" +1 ", "plus_1", 6),
                        (" +10 ", "plus_10", 7)
                    ]
                    if self.track_commander_damage:
                        buttons.append((" C- ", "cmdr_minus", 5))
                        buttons.append((" C+ ", "cmdr_plus", 5))

                    total_btns_w = sum(b[2] for b in buttons) + (len(buttons) - 1)
                    start_bx = bx + (bw - total_btns_w) // 2

                    cur_bx = start_bx
                    for label, action, b_w in buttons:
                        for r_offset in range(2):
                            if btn_y + r_offset < h - 1:
                                try:
                                    self.stdscr.addstr(btn_y + r_offset, cur_bx, ' ' * b_w, attr | curses.A_REVERSE)
                                except curses.error:
                                    pass
                        if btn_y < h - 1:
                            try:
                                self.stdscr.addstr(btn_y, cur_bx + (b_w - len(label)) // 2, label, attr | curses.A_REVERSE | curses.A_BOLD)
                            except curses.error:
                                pass

                        p.click_zones[action] = (btn_y, btn_y + 1, cur_bx, cur_bx + b_w - 1)
                        cur_bx += b_w + 1
            else:
                fallback_str = f"{p.deck_name}: {p.life}L"
                if by + 1 < h - 1:
                    try:
                        self.stdscr.addstr(by + 1, bx + (bw - len(fallback_str)) // 2, fallback_str, attr)
                    except curses.error:
                        pass

        self.stdscr.refresh()

    def handle_mouse_click(self, mx, my):
        for p_idx, p in enumerate(self.players):
            if p.eliminated:
                continue
            if hasattr(p, 'click_zones'):
                for action, zone_coords in p.click_zones.items():
                    if len(zone_coords) == 4:
                        zy_start, zy_end, zx_start, zx_end = zone_coords
                        if zy_start <= my <= zy_end and zx_start <= mx <= zx_end:
                            if action == "life_box":
                                self.handle_advanced_keyboard_adjustment(p_idx)
                            elif action == "minus_10":
                                p.life -= 10
                            elif action == "minus_1":
                                p.life -= 1
                            elif action == "plus_1":
                                p.life += 1
                            elif action == "plus_10":
                                p.life += 10
                            elif action == "cmdr_minus":
                                p.commander_damage = max(0, p.commander_damage - 1)
                            elif action == "cmdr_plus":
                                p.commander_damage += 1

                            if p.life <= 0:
                                self.check_elimination(p, reason="life")
                            elif self.track_commander_damage and p.commander_damage >= 21:
                                self.check_elimination(p, reason="commander")

    def show_game_over_screen(self, winner):
        try:
            curses.init_pair(50, curses.COLOR_RED, -1)
            curses.init_pair(51, curses.COLOR_YELLOW, -1)
            curses.init_pair(52, curses.COLOR_GREEN, -1)
            curses.init_pair(53, curses.COLOR_CYAN, -1)
            curses.init_pair(54, curses.COLOR_BLUE, -1)
            curses.init_pair(55, curses.COLOR_MAGENTA, -1)

            curses.init_pair(60, curses.COLOR_RED, -1)
            curses.init_pair(61, 208, -1)  # Vivid Orange
            curses.init_pair(62, curses.COLOR_YELLOW, -1)
        except curses.error:
            pass

        game_over_pairs = [50, 51, 52, 53, 54, 55]
        overkill_pairs = [60, 60, 61, 61, 62, 62]

        color_cycle_idx = 0

        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()

            win_attr = curses.A_BOLD
            if winner:
                c_code = COLOR_MAP.get(winner.color_name, curses.COLOR_WHITE)
                try:
                    curses.init_pair(70, c_code, -1)
                    win_attr = curses.color_pair(70) | curses.A_BOLD
                except curses.error:
                    pass

            box_h, box_w = h - 4, w - 4
            by, bx = 2, 2
            for row in range(by, by + box_h):
                for col in range(bx, bx + box_w):
                    if row == by or row == by + box_h - 1 or col == bx or col == bx + box_w - 1:
                        if row < h - 1 and col < w - 1:
                            try:
                                self.stdscr.addch(row, col, '█', win_attr)
                            except curses.error:
                                pass

            is_overkill = any(p.overkill for p in self.players) or any(p.life <= -25 for p in self.players)

            if is_overkill:
                top_art = render_ascii_art("OVERKILL", font_name='fire_font-s', max_width=box_w - 6, max_lines=10)
            else:
                top_art = render_ascii_art("GAME OVER", font_name='epic', max_width=box_w - 6, max_lines=10)

            if winner:
                winner_text = f"{winner.deck_name}        WINS"
            else:
                winner_text = "DRAW        NO SURVIVORS"

            status_art = render_ascii_art(winner_text, font_name='doom', max_width=box_w - 6, max_lines=10)

            total_art_height = len(top_art) + 1 + len(status_art)
            start_y = max(by + 2, (h - total_art_height) // 2 + 2)

            for idx, line in enumerate(top_art):
                lx = bx + (box_w - len(line)) // 2
                current_y = start_y + idx
                if current_y < h - 2:
                    for char_idx, char in enumerate(line):
                        if char.strip():
                            if is_overkill:
                                pair_idx = overkill_pairs[(color_cycle_idx + idx + char_idx) % len(overkill_pairs)]
                            else:
                                pair_idx = game_over_pairs[(color_cycle_idx + idx + char_idx) % len(game_over_pairs)]

                            attr = curses.color_pair(pair_idx) | curses.A_BOLD
                            try:
                                self.stdscr.addch(current_y, lx + char_idx, char, attr)
                            except curses.error:
                                pass

            next_y = start_y + len(top_art) + 1
            for idx, line in enumerate(status_art):
                lx = bx + (box_w - len(line)) // 2
                current_y = next_y + idx
                if current_y < h - 2:
                    try:
                        self.stdscr.addstr(current_y, lx, line, win_attr)
                    except curses.error:
                        pass

            footer_msg = "Press [R] to Return to Start or [Q] to Quit"
            footer_y = by + box_h - 2
            if footer_y < h - 1:
                try:
                    self.stdscr.addstr(footer_y, bx + (box_w - len(footer_msg)) // 2, footer_msg, curses.A_DIM)
                except curses.error:
                    pass

            self.stdscr.refresh()

            self.stdscr.nodelay(True)
            key = self.stdscr.getch()
            self.stdscr.nodelay(False)

            if key == ord('q') or key == ord('Q'):
                sys.exit(0)
            elif key == ord('r') or key == ord('R'):
                self.setup_game()
                return True

            color_cycle_idx += 1
            curses.napms(160)

def main(stdscr):
    try:
        app = MTGCounterApp(stdscr)
        app.run()
    except Exception as e:
        curses.endwin()
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    curses.wrapper(main)
