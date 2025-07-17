import tkinter as tk
import random
import time

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 500
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 12
BALL_RADIUS = 8
BRICK_ROWS = 5
BRICK_COLUMNS = 12
BRICK_WIDTH = (WINDOW_WIDTH - 50) // BRICK_COLUMNS
BRICK_HEIGHT = 22
MIN_BRICKS = 25

PASTEL_COLORS = ["#FFB6C1", "#A0E7E5", "#B4F8C8", "#FBE7C6", "#FFD6A5", "#FF9CEE", "#C3F584"]
CHAOS_EVENTS = [
    "reverse", "multiball", "bigpaddle", "ghostball", "shrinkpad",
    "invisiblepad", "drunkpad", "partybricks", "confusion",
    "darkness", "splitpad", "slippery", "gunpad", "shuffler", "flipview"
]

CHAOS_COLORS = {
    "reverse": "#f72585",
    "multiball": "#4361ee",
    "bigpaddle": "#80ed99",
    "ghostball": "#adb5bd",
    "shrinkpad": "#ff6b6b",
    "invisiblepad": "#222222",
    "drunkpad": "#e29578",
    "partybricks": "#ffbe0b",
    "confusion": "#9d4edd",
    "darkness": "#000000",
    "splitpad": "#e0aaff",
    "slippery": "#72efdd",
    "gunpad": "#d00000",
    "shuffler": "#ffb703",
    "flipview": "#9ae3d3"
}


class ChaosBreakout:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#1e1e1e", highlightthickness=0)
        self.canvas.grid(row=0, column=1, rowspan=3)

        self.reverse_controls = False
        self.extra_balls = []
        self.effect_end_time = None
        self.active_effect = None
        self.ghostball = False
        self.shrunk = False
        self.invisiblepad = False
        self.drunk_direction = None
        self.partybricks_active = False
        self.confusion = False
        self.dark_overlay = None
        self.split_paddles = []
        self.split_direction = 0
        self.slippery_velocity = 0
        self.gun_bullets = []
        self.bullets_to_remove = set()
        self.flip_applied = False
        self.paddle_speed = 8
        self.ball_speed = 5
        self.chaos_chance = 1.0
        self.score = 0
        self.highscore = 0
        self.lives = 3
        self.running = True
        self.paused = False

        self.left_pressed = False
        self.right_pressed = False

        self.build_sidebar()
        self.init_game()
        self.bind_keys()
        self.loop_movement()
        self.game_loop()

    def build_sidebar(self):
        self.sidebar = tk.Frame(self.root, width=260, height=WINDOW_HEIGHT, bg="#f3ede5")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        title = tk.Label(self.sidebar, text="ChaosBreakout", font=("Segoe UI", 17, "bold"), bg="#f3ede5", fg="#3a0ca3")
        title.pack(pady=(10, 4))

        self.score_label = tk.Label(self.sidebar, text="Score: 0", font=("Segoe UI", 11, "bold"), bg="#f3ede5",
                                    fg="#222")
        self.score_label.pack()

        self.highscore_label = tk.Label(self.sidebar, text="High Score: 0", font=("Segoe UI", 10), bg="#f3ede5",
                                        fg="#777")
        self.highscore_label.pack()

        self.lives_label = tk.Label(self.sidebar, text="❤ x3", font=("Segoe UI", 11), bg="#f3ede5", fg="#e63946")
        self.lives_label.pack(pady=(0, 10))

        tk.Label(self.sidebar, text="Chaos Event", font=("Segoe UI", 11, "underline"), bg="#f3ede5", fg="#444").pack()

        self.chaos_label = tk.Label(
            self.sidebar, text="None", font=("Segoe UI", 10, "bold"),
            fg="#d00000", bg="#fffdf5", width=25, height=2, relief="ridge", bd=2
        )
        self.chaos_label.pack(pady=(2, 12), padx=10)

        tk.Label(self.sidebar, text="Settings", font=("Segoe UI", 11, "underline"), bg="#f3ede5", fg="#444").pack()

        for text, varname, from_, to, update_fn in [
            ("Paddle Speed", "speed_slider", 3, 15, self.update_speed),
            ("Ball Speed", "ball_slider", 2, 10, self.update_ball_speed),
            ("Chaos Chance", "chaos_slider", 0, 100, self.update_chaos)
        ]:
            tk.Label(self.sidebar, text=text, font=("Segoe UI", 10), bg="#f3ede5").pack()
            slider = tk.Scale(self.sidebar, from_=from_, to=to, orient="horizontal",
                              command=update_fn, bg="#f3ede5", length=200)
            if varname == "chaos_slider":
                slider.set(100)
            else:
                slider.set(getattr(self, text.lower().replace(" ", "_")))

            slider.pack(pady=(0, 6))
            setattr(self, varname, slider)

        self.chaos_value_label = tk.Label(self.sidebar, text=f"{int(self.chaos_chance * 100)}%",
                                          font=("Segoe UI", 10, "italic"), bg="#f3ede5", fg="#555")
        self.chaos_value_label.pack(pady=(0, 10))

        self.restart_btn = tk.Button(self.sidebar, text="Restart Game", font=("Segoe UI", 10, "bold"),
                                     command=self.restart_game, bg="#d8f3dc", fg="#000",
                                     activebackground="#b7e4c7")
        self.restart_btn.pack(pady=(6, 8))

    def update_speed(self, val):
        self.paddle_speed = int(val)

    def update_ball_speed(self, val):
        speed = int(val)
        self.ball_dx = speed if self.ball_dx >= 0 else -speed
        self.ball_dy = -speed
        self.ball_speed = speed

    def update_chaos(self, val):
        self.chaos_chance = int(val) / 100
        self.chaos_value_label.config(text=f"{int(val)}%")

    def init_game(self):
        self.canvas.delete("all")

        self.pause_tip = self.canvas.create_text(
            WINDOW_WIDTH // 2, 12,
            text="Press SPACE to pause",
            font=("Segoe UI", 10, "italic"),
            fill="#888888"
        )

        self.paddle = self.canvas.create_rectangle(
            WINDOW_WIDTH // 2 - PADDLE_WIDTH // 2,
            WINDOW_HEIGHT - 40,
            WINDOW_WIDTH // 2 + PADDLE_WIDTH // 2,
            WINDOW_HEIGHT - 40 + PADDLE_HEIGHT,
            fill="#ffffff", outline="", width=0
        )
        self.ball = self.create_ball(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        self.ball_dx = self.ball_speed
        self.ball_dy = -self.ball_speed

        self.extra_balls = []
        self.effect_end_time = None
        self.active_effect = None
        self.reverse_controls = False
        self.ghostball = False
        self.shrunk = False
        self.pause_overlay = None
        self.pause_text = None

        self.generate_symmetric_bricks()

    def create_ball(self, x, y):
        return self.canvas.create_oval(
            x - BALL_RADIUS, y - BALL_RADIUS,
            x + BALL_RADIUS, y + BALL_RADIUS,
            fill="#ffffff", outline="", width=0
        )

    def generate_symmetric_bricks(self):
        self.bricks = []
        attempts = 0
        while True:
            self.bricks.clear()
            half_cols = BRICK_COLUMNS // 2
            for row in range(BRICK_ROWS):
                pattern = [random.choice([True, False]) for _ in range(half_cols)]
                full_pattern = pattern + pattern[::-1]
                for col, active in enumerate(full_pattern):
                    if active:
                        x1 = 25 + col * BRICK_WIDTH
                        y1 = 60 + row * BRICK_HEIGHT
                        x2 = x1 + BRICK_WIDTH - 4
                        y2 = y1 + BRICK_HEIGHT - 4
                        color = random.choice(PASTEL_COLORS)
                        self.bricks.append(self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill=color, outline="#444", width=1
                        ))
            if len(self.bricks) >= MIN_BRICKS or attempts > 5:
                break
            attempts += 1

    def bind_keys(self):
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress-Left>", lambda e: self.set_key("left", True))
        self.canvas.bind("<KeyRelease-Left>", lambda e: self.set_key("left", False))
        self.canvas.bind("<KeyPress-Right>", lambda e: self.set_key("right", True))
        self.canvas.bind("<KeyRelease-Right>", lambda e: self.set_key("right", False))
        self.canvas.bind("<space>", self.toggle_pause)

    def toggle_pause(self, event=None):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_overlay = self.canvas.create_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                                                              fill="black", stipple="gray50")
            self.pause_text = self.canvas.create_text(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
                                                      text="PAUSED", fill="#ffffff",
                                                      font=("Segoe UI", 24, "bold"))
        else:
            self.canvas.delete(self.pause_overlay)
            self.canvas.delete(self.pause_text)
            self.game_loop()

    def set_key(self, key, value):
        if key == "left":
            self.left_pressed = value
        elif key == "right":
            self.right_pressed = value

    def loop_movement(self):
        if not self.paused:
            dx = self.paddle_speed if self.right_pressed else -self.paddle_speed if self.left_pressed else 0
            if self.reverse_controls:
                dx = -dx
            if self.drunk_direction:
                dx += self.drunk_direction * 2

            if self.active_effect == "slippery":
                if dx == 0:
                    self.slippery_velocity *= 0.95
                else:
                    self.slippery_velocity += dx * 0.1
                self.move_paddle(self.slippery_velocity)
            elif self.active_effect == "splitpad":
                self.split_direction = dx
                self.move_split_paddles(dx)
            else:
                self.move_paddle(dx)
        self.update_bullets()
        self.root.after(16, self.loop_movement)

    def move_paddle(self, dx):
        x1, _, x2, _ = self.canvas.coords(self.paddle)
        if x1 + dx < 0:
            dx = -x1
        elif x2 + dx > WINDOW_WIDTH:
            dx = WINDOW_WIDTH - x2
        self.canvas.move(self.paddle, dx, 0)

    def check_collisions(self, ball_id):
        x1, y1, x2, y2 = self.canvas.coords(ball_id)
        if x1 <= 0 or x2 >= WINDOW_WIDTH:
            return "x"

        if not self.flip_applied and y1 <= 0:
            return "y"
        if self.flip_applied and y2 >= WINDOW_HEIGHT:
            return "y"

        if (not self.flip_applied and y2 >= WINDOW_HEIGHT) or (self.flip_applied and y1 <= 0):
            self.canvas.delete(ball_id)
            return "miss"

        if self.active_effect == "splitpad":
            for paddle in self.split_paddles:
                px1, py1, px2, py2 = self.canvas.coords(paddle)
                if y2 >= py1 and y1 <= py2 and x2 >= px1 and x1 <= px2:
                    return "y"

        px1, py1, px2, py2 = self.canvas.coords(self.paddle)
        if y2 >= py1 and y1 <= py2 and x2 >= px1 and x1 <= px2:
            return "y"

        if not self.ghostball:
            for brick in list(self.bricks):
                if brick not in self.canvas.find_all():
                    continue
                bx1, by1, bx2, by2 = self.canvas.coords(brick)
                if x2 >= bx1 and x1 <= bx2 and y2 >= by1 and y1 <= by2:
                    self.canvas.delete(brick)
                    self.bricks.remove(brick)
                    self.score += 100
                    self.update_status()
                    if random.random() < self.chaos_chance and not self.active_effect:
                        self.activate_chaos()
                    overlap_x = min(x2, bx2) - max(x1, bx1)
                    overlap_y = min(y2, by2) - max(y1, by1)
                    if overlap_x > overlap_y:
                        return "y"
                    else:
                        return "x"
        return None

    def activate_chaos(self):
        effect = random.choice(CHAOS_EVENTS)
        self.active_effect = effect
        self.effect_end_time = int(time.time() * 1000) + random.randint(3000, 10000)
        self.chaos_label.config(text=f"{effect.upper()}!", fg="#fff", bg=CHAOS_COLORS.get(effect, "#222"))

        if effect == "reverse":
            self.reverse_controls = True
        elif effect == "multiball":
            x1, y1, x2, y2 = self.canvas.coords(self.ball)
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            new_ball = self.create_ball(x, y)
            speed = self.ball_speed
            self.extra_balls.append((new_ball, speed, -speed))
        elif effect == "bigpaddle":
            px1, py1, px2, py2 = self.canvas.coords(self.paddle)
            center = (px1 + px2) / 2
            self.canvas.coords(self.paddle, center - 70, py1, center + 70, py2)
        elif effect == "ghostball":
            self.ghostball = True
            self.canvas.itemconfig(self.ball, fill="#cccccc")
        elif effect == "shrinkpad":
            if not self.shrunk:
                px1, py1, px2, py2 = self.canvas.coords(self.paddle)
                center = (px1 + px2) / 2
                self.canvas.coords(self.paddle, center - 30, py1, center + 30, py2)
                self.shrunk = True
        elif effect == "invisiblepad":
            self.canvas.itemconfig(self.paddle, state="hidden")
            self.invisiblepad = True
            self.flicker_paddle()
        elif effect == "drunkpad":
            self.drunk_direction = random.choice([-1, 1])
        elif effect == "partybricks":
            self.partybricks_active = True
            self.partybricks()
        elif effect == "confusion":
            self.confusion = True
        elif effect == "darkness":
            self.dark_overlay = self.canvas.create_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                                                             fill="black", stipple="gray50", tags="dark")
        elif effect == "splitpad":
            self.canvas.itemconfig(self.paddle, state="hidden")
            px1, py1, px2, py2 = self.canvas.coords(self.paddle)
            width = px2 - px1
            y = py1
            self.split_paddles = [
                self.canvas.create_rectangle(80 - width // 2, y, 80 + width // 2, y + PADDLE_HEIGHT, fill="#fff",
                                             outline=""),
                self.canvas.create_rectangle(WINDOW_WIDTH - 80 - width // 2, y, WINDOW_WIDTH - 80 + width // 2,
                                             y + PADDLE_HEIGHT, fill="#fff", outline="")
            ]
        elif effect == "slippery":
            self.slippery_velocity = 0
        elif effect == "gunpad":
            def shoot():
                if self.active_effect != "gunpad":
                    return
                x1, y1, x2, y2 = self.canvas.coords(self.paddle)
                cx = (x1 + x2) / 2
                bullet = self.canvas.create_rectangle(cx - 2, y1 - 10, cx + 2, y1, fill="red")
                self.gun_bullets.append(bullet)
                self.root.after(300, shoot)

            shoot()
        elif effect == "shuffler":
            brick_coords = [self.canvas.coords(b) for b in self.bricks]
            random.shuffle(brick_coords)
            for i, b in enumerate(self.bricks):
                self.canvas.coords(b, *brick_coords[i])
        elif effect == "flipview":
            if not self.flip_applied:
                self.canvas.scale("all", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, 1, -1)
                self.flip_applied = True

    def clear_chaos(self):
        self.reverse_controls = False
        self.ghostball = False
        self.canvas.itemconfig(self.ball, fill="#ffffff")
        if self.active_effect in ["bigpaddle", "shrinkpad"]:
            px1, py1, px2, py2 = self.canvas.coords(self.paddle)
            center = (px1 + px2) / 2
            self.canvas.coords(self.paddle, center - PADDLE_WIDTH // 2, py1, center + PADDLE_WIDTH // 2, py2)
        if self.invisiblepad:
            self.canvas.itemconfig(self.paddle, state="normal")
            self.invisiblepad = False
        if self.drunk_direction is not None:
            self.drunk_direction = None
        if self.partybricks_active:
            self.partybricks_active = False
        if self.confusion:
            self.confusion = False
        self.active_effect = None
        self.shrunk = False
        self.effect_end_time = None
        self.chaos_label.config(text="None", fg="#d00000", bg="#fffdf5")
        if self.dark_overlay:
            self.canvas.delete(self.dark_overlay)
            self.dark_overlay = None
        if self.split_paddles:
            for p in self.split_paddles:
                self.canvas.delete(p)
            self.canvas.itemconfig(self.paddle, state="normal")
            self.split_paddles = []
        self.slippery_velocity = 0
        for bullet in self.gun_bullets:
            self.canvas.delete(bullet)
        self.gun_bullets = []
        self.bullets_to_remove.clear()
        if self.flip_applied:
            self.canvas.scale("all", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, 1, -1)
            self.flip_applied = False

    def partybricks(self):
        if not self.partybricks_active:
            return
        for brick in self.bricks:
            color = random.choice(PASTEL_COLORS)
            self.canvas.itemconfig(brick, fill=color)
        self.root.after(100, self.partybricks)

    def update_bullets(self):
        bullets_to_remove = set()

        for bullet in self.gun_bullets:
            if bullet in self.bullets_to_remove:
                continue

            self.canvas.move(bullet, 0, -10)
            coords = self.canvas.coords(bullet)
            if len(coords) != 4:
                bullets_to_remove.add(bullet)
                continue

            x1, y1, x2, y2 = coords
            if y2 < 0:
                bullets_to_remove.add(bullet)
                continue

            hit = False
            for brick in list(self.bricks):
                if brick not in self.canvas.find_all():
                    continue
                bx1, by1, bx2, by2 = self.canvas.coords(brick)
                if x2 >= bx1 and x1 <= bx2 and y2 >= by1 and y1 <= by2:
                    self.canvas.delete(brick)
                    self.bricks.remove(brick)
                    self.score += 100
                    self.update_status()
                    bullets_to_remove.add(bullet)
                    hit = True
                    if random.random() < self.chaos_chance and not self.active_effect:
                        self.activate_chaos()
                    break

        for bullet in bullets_to_remove:
            if bullet in self.gun_bullets:
                self.canvas.delete(bullet)
                self.gun_bullets.remove(bullet)

    def move_split_paddles(self, dx):
        for i, paddle in enumerate(self.split_paddles):
            direction = dx if i == 0 else -dx
            x1, _, x2, _ = self.canvas.coords(paddle)
            if x1 + direction < 0:
                direction = -x1
            elif x2 + direction > WINDOW_WIDTH:
                direction = WINDOW_WIDTH - x2
            self.canvas.move(paddle, direction, 0)

    def flicker_paddle(self):
        if not self.invisiblepad:
            return
        self.canvas.itemconfig(self.paddle, state="normal")
        self.root.after(200, lambda: self.canvas.itemconfig(self.paddle, state="hidden"))
        self.root.after(1000, self.flicker_paddle)

    def move_ball(self, ball_id, dx, dy):
        if self.confusion:
            dx += random.choice([-1, 0, 1])
            dy += random.choice([-1, 0, 1])
        result = self.check_collisions(ball_id)
        if result == "x":
            dx = -dx
        elif result == "y":
            dy = -dy
        elif result == "miss":
            return None, None
        self.canvas.move(ball_id, dx, dy)
        return dx, dy

    def update_status(self):
        self.score_label.config(text=f"Score: {self.score}")
        self.highscore = max(self.highscore, self.score)
        self.highscore_label.config(text=f"High Score: {self.highscore}")
        self.lives_label.config(text=f"❤ x{self.lives}")

    def game_loop(self):
        if not self.running or self.paused:
            return

        result = self.move_ball(self.ball, self.ball_dx, self.ball_dy)
        if result != (None, None):
            self.ball_dx, self.ball_dy = result
        else:
            self.lives -= 1
            self.update_status()
            if self.lives <= 0:
                self.chaos_label.config(text="💀 GAME OVER", fg="white", bg="red")
                self.running = False
                return
            self.ball = self.create_ball(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            self.ball_dx = self.ball_speed
            self.ball_dy = -self.ball_speed

        still_alive = []
        for ball_id, dx, dy in self.extra_balls:
            res = self.move_ball(ball_id, dx, dy)
            if res != (None, None):
                still_alive.append((ball_id, *res))
        self.extra_balls = still_alive

        if self.active_effect and int(time.time() * 1000) >= self.effect_end_time:
            self.clear_chaos()

        if len(self.bricks) == 0:
            self.init_game()

        self.root.after(16, self.game_loop)

    def restart_game(self):
        self.running = True
        self.lives = 3
        self.score = 0
        self.update_status()
        self.clear_chaos()

        for ball_id, *_ in self.extra_balls:
            self.canvas.delete(ball_id)
        self.extra_balls.clear()

        self.ball_dx = self.ball_speed
        self.ball_dy = -self.ball_speed

        self.init_game()
        self.ball_dx = self.ball_speed
        self.ball_dy = -self.ball_speed

        self.game_loop()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("ChaosBreakout")
    root.resizable(False, False)
    game = ChaosBreakout(root)
    root.mainloop()