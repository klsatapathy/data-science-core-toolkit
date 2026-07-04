"""
Logical Number Guesser - GUI Edition (Tkinter)
------------------------------------------------
Features:
  - Difficulty levels (Easy / Medium / Hard) selectable on a start screen
  - Live timer and attempt counter
  - Visual number-line (Canvas) showing the shrinking search space and each guess
  - Guess history list (too high / too low / correct)
  - AI opponent: shows the binary search algorithm's step-by-step guesses
    after you win, then compares your attempts to the optimal algorithm
  - Persistent leaderboard (best attempts/time per difficulty) saved to
    leaderboard.json, so your best scores survive closing the app
"""

import tkinter as tk
import random
import time
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCORES_FILE = os.path.join(BASE_DIR, "leaderboard.json")

DIFFICULTIES = {
    "Easy (1-50)": (1, 50),
    "Medium (1-100)": (1, 100),
    "Hard (1-500)": (1, 500),
}


def computer_optimal_guess(low, high, target):
    """Simulates a Binary Search algorithm guessing the number.
    Returns (attempt_count, list_of_steps) where each step is (guess, low, high)."""
    attempts = 0
    steps = []
    while low <= high:
        attempts += 1
        guess = (low + high) // 2
        steps.append((guess, low, high))
        if guess == target:
            return attempts, steps
        elif guess < target:
            low = guess + 1
        else:
            high = guess - 1
    return attempts, steps


class LeaderboardManager:
    """Handles loading/saving best scores per difficulty to a JSON file."""

    def __init__(self, filepath=SCORES_FILE):
        self.filepath = filepath
        self.data = self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def record(self, difficulty, attempts, duration):
        """Saves the score if it's a new best for this difficulty. Returns True if it's a new best."""
        entry = {"attempts": attempts, "time": duration}
        best = self.data.get(difficulty)
        if best is None or (attempts, duration) < (best["attempts"], best["time"]):
            self.data[difficulty] = entry
            self.save()
            return True
        return False


class NumberGuesserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Logical Number Guesser")
        self.root.geometry("780x640")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2f")

        self.leaderboard = LeaderboardManager()

        self.difficulty_var = tk.StringVar(value=list(DIFFICULTIES.keys())[1])
        self.low = 1
        self.high = 100
        self.current_low = 1
        self.current_high = 100
        self.secret = None
        self.attempts = 0
        self.start_time = None
        self.timer_job = None
        self.guess_history = []  # list of (guess, feedback_type)
        self.current_difficulty = None

        self.container = tk.Frame(root, bg="#1e1e2f")
        self.container.pack(fill="both", expand=True)

        self.canvas = None
        self.build_start_screen()

    # ---------------- Start Screen ----------------

    def build_start_screen(self):
        self.clear_container()
        tk.Label(self.container, text="\U0001F9E9 LOGICAL NUMBER GUESSER \U0001F9E9",
                 font=("Segoe UI", 22, "bold"), bg="#1e1e2f", fg="#f5c518").pack(pady=(40, 10))

        tk.Label(self.container,
                 text="Guess the secret number. Can you beat the computer's binary search?",
                 font=("Segoe UI", 12), bg="#1e1e2f", fg="#cccccc", wraplength=600
                 ).pack(pady=(0, 30))

        tk.Label(self.container, text="Choose difficulty:", font=("Segoe UI", 13, "bold"),
                 bg="#1e1e2f", fg="white").pack(pady=(10, 5))

        diff_frame = tk.Frame(self.container, bg="#1e1e2f")
        diff_frame.pack(pady=5)
        for name in DIFFICULTIES:
            tk.Radiobutton(diff_frame, text=name, variable=self.difficulty_var, value=name,
                           font=("Segoe UI", 11), bg="#1e1e2f", fg="white",
                           selectcolor="#33334d", activebackground="#1e1e2f",
                           activeforeground="#f5c518", indicatoron=True
                           ).pack(anchor="w", pady=3)

        tk.Button(self.container, text="Start Game", font=("Segoe UI", 13, "bold"),
                  bg="#f5c518", fg="#1e1e2f", activebackground="#ffd84d",
                  relief="flat", padx=20, pady=8, command=self.start_game).pack(pady=25)

        tk.Button(self.container, text="View Leaderboard", font=("Segoe UI", 10),
                  bg="#33334d", fg="white", relief="flat", padx=12, pady=6,
                  command=self.show_leaderboard).pack()

    def show_leaderboard(self):
        win = tk.Toplevel(self.root)
        win.title("Leaderboard")
        win.geometry("380x280")
        win.configure(bg="#1e1e2f")
        tk.Label(win, text="\U0001F3C6 Best Scores \U0001F3C6", font=("Segoe UI", 14, "bold"),
                 bg="#1e1e2f", fg="#f5c518").pack(pady=10)
        if not self.leaderboard.data:
            tk.Label(win, text="No scores yet. Play a game!", bg="#1e1e2f", fg="white").pack(pady=20)
        else:
            for diff, entry in self.leaderboard.data.items():
                text = f"{diff}:  {entry['attempts']} attempts, {entry['time']}s"
                tk.Label(win, text=text, font=("Segoe UI", 11), bg="#1e1e2f", fg="white"
                         ).pack(anchor="w", padx=20, pady=4)

    # ---------------- Game Screen ----------------

    def start_game(self):
        diff_name = self.difficulty_var.get()
        self.low, self.high = DIFFICULTIES[diff_name]
        self.current_difficulty = diff_name
        self.secret = random.randint(self.low, self.high)
        self.attempts = 0
        self.guess_history = []
        self.current_low = self.low
        self.current_high = self.high
        self.start_time = time.time()

        self.build_game_screen()
        self.update_timer()

    def build_game_screen(self):
        self.clear_container()

        top_frame = tk.Frame(self.container, bg="#1e1e2f")
        top_frame.pack(pady=(20, 10), fill="x")

        self.range_label = tk.Label(top_frame, text=f"Range: {self.low} - {self.high}",
                                     font=("Segoe UI", 12, "bold"), bg="#1e1e2f", fg="white")
        self.range_label.pack(side="left", padx=30)

        self.attempts_label = tk.Label(top_frame, text="Attempts: 0",
                                        font=("Segoe UI", 12, "bold"), bg="#1e1e2f", fg="white")
        self.attempts_label.pack(side="left", padx=30)

        self.timer_label = tk.Label(top_frame, text="Time: 0.0s",
                                     font=("Segoe UI", 12, "bold"), bg="#1e1e2f", fg="white")
        self.timer_label.pack(side="left", padx=30)

        self.canvas_width = 700
        self.canvas_height = 100
        self.canvas = tk.Canvas(self.container, width=self.canvas_width, height=self.canvas_height,
                                 bg="#2b2b40", highlightthickness=0)
        self.canvas.pack(pady=15)
        self.draw_number_line()

        entry_frame = tk.Frame(self.container, bg="#1e1e2f")
        entry_frame.pack(pady=10)

        self.guess_var = tk.StringVar()
        self.guess_entry = tk.Entry(entry_frame, textvariable=self.guess_var, font=("Segoe UI", 14),
                                     width=10, justify="center")
        self.guess_entry.pack(side="left", padx=10)
        self.guess_entry.bind("<Return>", lambda e: self.submit_guess())
        self.guess_entry.focus()

        tk.Button(entry_frame, text="Guess", font=("Segoe UI", 12, "bold"),
                  bg="#f5c518", fg="#1e1e2f", relief="flat", padx=15, pady=5,
                  command=self.submit_guess).pack(side="left")

        self.feedback_label = tk.Label(self.container, text="Make your first guess!",
                                        font=("Segoe UI", 13, "bold"), bg="#1e1e2f", fg="#f5c518")
        self.feedback_label.pack(pady=15)

        tk.Label(self.container, text="Guess History:", font=("Segoe UI", 11, "bold"),
                 bg="#1e1e2f", fg="white").pack()

        self.history_box = tk.Listbox(self.container, height=6, width=50, font=("Consolas", 10),
                                       bg="#2b2b40", fg="white", relief="flat")
        self.history_box.pack(pady=5)

    def draw_number_line(self):
        self.canvas.delete("all")
        margin = 40
        line_y = 60
        total_range = max(self.high - self.low, 1)

        def x_pos(value):
            return margin + (value - self.low) / total_range * (self.canvas_width - 2 * margin)

        self.canvas.create_line(margin, line_y, self.canvas_width - margin, line_y,
                                 fill="#555577", width=2)

        x1, x2 = x_pos(self.current_low), x_pos(self.current_high)
        self.canvas.create_rectangle(x1, line_y - 8, x2, line_y + 8, fill="#3a3a5c", outline="")

        self.canvas.create_text(margin, line_y + 25, text=str(self.low),
                                 fill="#aaaaaa", font=("Segoe UI", 9))
        self.canvas.create_text(self.canvas_width - margin, line_y + 25, text=str(self.high),
                                 fill="#aaaaaa", font=("Segoe UI", 9))

        colors = {"low": "#4da3ff", "high": "#ff6b6b", "correct": "#4caf50"}
        for guess, feedback in self.guess_history:
            gx = x_pos(guess)
            self.canvas.create_oval(gx - 5, line_y - 5, gx + 5, line_y + 5,
                                     fill=colors[feedback], outline="")

    def update_timer(self):
        if self.start_time is not None:
            elapsed = round(time.time() - self.start_time, 1)
            self.timer_label.config(text=f"Time: {elapsed}s")
            self.timer_job = self.root.after(100, self.update_timer)

    def submit_guess(self):
        raw = self.guess_var.get().strip()
        if not raw.lstrip("-").isdigit():
            self.feedback_label.config(text="\u26A0\uFE0F Please enter a valid whole number.", fg="#ff6b6b")
            return
        guess = int(raw)
        if guess < self.low or guess > self.high:
            self.feedback_label.config(
                text=f"\u274C Out of bounds! Guess between {self.low}-{self.high}.", fg="#ff6b6b")
            return

        self.attempts += 1
        self.attempts_label.config(text=f"Attempts: {self.attempts}")
        self.guess_var.set("")

        if guess == self.secret:
            self.guess_history.append((guess, "correct"))
            self.history_box.insert("end", f"{guess}   Correct!")
            self.end_game()
            return
        elif guess < self.secret:
            self.guess_history.append((guess, "low"))
            self.history_box.insert("end", f"{guess}   Too low")
            self.feedback_label.config(text="\U0001F4C9 Too low! Try higher.", fg="#4da3ff")
            self.current_low = max(self.current_low, guess + 1)
        else:
            self.guess_history.append((guess, "high"))
            self.history_box.insert("end", f"{guess}   Too high")
            self.feedback_label.config(text="\U0001F4C8 Too high! Try lower.", fg="#ff6b6b")
            self.current_high = min(self.current_high, guess - 1)

        self.history_box.see("end")
        self.draw_number_line()

    def end_game(self):
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
        duration = round(time.time() - self.start_time, 2)
        self.timer_label.config(text=f"Time: {duration}s")
        self.draw_number_line()

        ai_attempts, ai_steps = computer_optimal_guess(self.low, self.high, self.secret)
        is_best = self.leaderboard.record(self.current_difficulty, self.attempts, duration)
        self.show_result_screen(duration, ai_attempts, ai_steps, is_best)

    def show_result_screen(self, duration, ai_attempts, ai_steps, is_best):
        win = tk.Toplevel(self.root)
        win.title("Result")
        win.geometry("450x560")
        win.configure(bg="#1e1e2f")
        win.grab_set()

        tk.Label(win, text="\U0001F389 Correct! \U0001F389", font=("Segoe UI", 18, "bold"),
                 bg="#1e1e2f", fg="#4caf50").pack(pady=(15, 5))
        tk.Label(win, text=f"You found {self.secret} in {self.attempts} attempts ({duration}s).",
                 font=("Segoe UI", 11), bg="#1e1e2f", fg="white", wraplength=400).pack(pady=5)

        if is_best:
            tk.Label(win, text="\u2B50 New personal best for this difficulty! \u2B50",
                     font=("Segoe UI", 11, "bold"), bg="#1e1e2f", fg="#f5c518").pack(pady=5)

        tk.Label(win, text="AI Opponent (Binary Search) steps:",
                 font=("Segoe UI", 11, "bold"), bg="#1e1e2f", fg="white").pack(pady=(15, 5))

        ai_box = tk.Listbox(win, height=8, width=45, font=("Consolas", 10),
                             bg="#2b2b40", fg="white", relief="flat")
        ai_box.pack(pady=5)
        for i, (g, lo, hi) in enumerate(ai_steps, start=1):
            ai_box.insert("end", f"Step {i}: guess {g}  (range {lo}-{hi})")

        tk.Label(win, text=f"The computer found it in {ai_attempts} attempts.",
                 font=("Segoe UI", 11), bg="#1e1e2f", fg="white").pack(pady=10)

        if self.attempts < ai_attempts:
            verdict, color = "\U0001F3C6 Masterclass! You beat the optimal algorithm!", "#4caf50"
        elif self.attempts == ai_attempts:
            verdict, color = "\U0001F91D You matched the optimal algorithm!", "#f5c518"
        else:
            verdict, color = "\U0001F4A1 The algorithm won this time. Keep sharpening your logic!", "#ff6b6b"
        tk.Label(win, text=verdict, font=("Segoe UI", 12, "bold"), bg="#1e1e2f", fg=color,
                 wraplength=400).pack(pady=15)

        btn_frame = tk.Frame(win, bg="#1e1e2f")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Play Again", font=("Segoe UI", 11, "bold"),
                  bg="#f5c518", fg="#1e1e2f", relief="flat", padx=12, pady=6,
                  command=lambda: [win.destroy(), self.build_start_screen()]).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Close", font=("Segoe UI", 11), bg="#33334d", fg="white",
                  relief="flat", padx=12, pady=6, command=win.destroy).pack(side="left", padx=8)

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()


def main():
    root = tk.Tk()
    NumberGuesserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
