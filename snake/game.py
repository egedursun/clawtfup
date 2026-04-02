"""Terminal snake game using curses."""

import curses
import random
import sys
import time

DIRECTIONS = {
    curses.KEY_UP:    (-1,  0),
    curses.KEY_DOWN:  ( 1,  0),
    curses.KEY_LEFT:  ( 0, -1),
    curses.KEY_RIGHT: ( 0,  1),
    ord("w"):         (-1,  0),
    ord("s"):         ( 1,  0),
    ord("a"):         ( 0, -1),
    ord("d"):         ( 0,  1),
}

OPPOSITES = {
    (-1,  0): ( 1,  0),
    ( 1,  0): (-1,  0),
    ( 0, -1): ( 0,  1),
    ( 0,  1): ( 0, -1),
}


def place_food(snake_set, height, width):
    while True:
        r = random.randint(1, height - 2)
        c = random.randint(1, width - 2)
        if (r, c) not in snake_set:
            return (r, c)


def draw_score(win, score):
    win.addstr(0, 2, f" Score: {score} ", curses.A_BOLD)


def game_loop(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # color setup
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN,  -1)  # snake
    curses.init_pair(2, curses.COLOR_RED,    -1)  # food
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # score / message

    height, width = stdscr.getmaxyx()
    if height < 10 or width < 20:
        stdscr.addstr(0, 0, "Terminal too small.")
        stdscr.refresh()
        time.sleep(2)
        return

    # initial snake: 3 cells in the middle, moving right
    mid_r, mid_c = height // 2, width // 2
    snake = [(mid_r, mid_c - i) for i in range(3)]
    snake_set = set(snake)
    direction = (0, 1)

    food = place_food(snake_set, height, width)
    score = 0
    speed = 0.15  # seconds per tick

    while True:
        # --- input ---
        key = stdscr.getch()
        if key in (ord("q"), 27):  # q or ESC
            break
        if key in DIRECTIONS:
            new_dir = DIRECTIONS[key]
            if new_dir != OPPOSITES.get(direction):
                direction = new_dir

        # --- move ---
        head_r, head_c = snake[0]
        dr, dc = direction
        new_head = (head_r + dr, head_c + dc)

        # wall collision
        if not (0 < new_head[0] < height - 1 and 0 < new_head[1] < width - 1):
            break

        # self collision
        if new_head in snake_set:
            break

        snake.insert(0, new_head)
        snake_set.add(new_head)

        if new_head == food:
            score += 10
            speed = max(0.05, speed - 0.002)
            food = place_food(snake_set, height, width)
        else:
            tail = snake.pop()
            snake_set.discard(tail)

        # --- draw ---
        stdscr.erase()
        stdscr.border()
        draw_score(stdscr, score)

        # food
        try:
            stdscr.addch(food[0], food[1], "@", curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        # snake
        for i, (r, c) in enumerate(snake):
            ch = "O" if i == 0 else "o"
            try:
                stdscr.addch(r, c, ch, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

        stdscr.refresh()
        time.sleep(speed)

    # --- game over ---
    msg = f"  Game over! Score: {score}  Press any key…  "
    r = height // 2
    c = max(0, (width - len(msg)) // 2)
    try:
        stdscr.addstr(r, c, msg, curses.color_pair(3) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def main():
    try:
        curses.wrapper(game_loop)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
