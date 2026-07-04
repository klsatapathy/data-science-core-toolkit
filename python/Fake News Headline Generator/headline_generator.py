"""
Fake + Funny News Headline Generator
--------------------------------------------------------
Features:
  - Multiple categories (Politics, Bollywood, Sports, Tech, Local, or Random Mix)
  - Multiple sentence templates for varied headline structures
  - No-repeat logic (won't show the same headline twice in a row)
  - Batch generation (generate several headlines at once)
  - Colored terminal output (falls back to plain text if colorama isn't installed)
  - Fun extras: credibility score, fake share/like counts, hashtags
  - Save your generated headlines to a timestamped .txt file
  - Word bank is loaded from an external word_banks.json, so you can add
    your own subjects/actions/objects/places without touching the code
"""

import json
import random
import os
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False


# ---------- Color helpers (safe no-ops if colorama isn't installed) ----------

def c(text, color=None, bold=False):
    if not COLOR_ENABLED or color is None:
        return text
    prefix = (Style.BRIGHT if bold else "") + color
    return f"{prefix}{text}{Style.RESET_ALL}"


# ---------- Data loading ----------

WORD_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "word_banks.json")

TEMPLATES = [
    "Breaking News: {subject} {action} {object} {place}.",
    "SHOCKING: {subject} {action} {object} {place}!",
    "You won't believe it — {subject} just {action} {object} {place}.",
    "Reports confirm {subject} {action} {object} {place}.",
    "Local sources say {subject} {action} {object} {place}, and nobody is okay.",
    "Exclusive: {subject} {action} {object} {place}. Twitter is losing it.",
]

HASHTAG_WORDS = ["Shocking", "Breaking", "Unbelievable", "ViralNow", "NotAJoke",
                 "SatireAlert", "TrendingNow", "WhatJustHappened"]


def load_word_bank():
    with open(WORD_BANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


WORD_BANK = load_word_bank()


# ---------- Core generator ----------

class HeadlineGenerator:
    def __init__(self, word_bank):
        self.word_bank = word_bank
        self.history = []          # all headlines generated this session
        self.last_headline = None  # used to avoid immediate repeats

    def _pick_category_data(self, category):
        if category == "random":
            category = random.choice(list(self.word_bank.keys()))
        return category, self.word_bank[category]

    def generate(self, category="random"):
        for _ in range(10):  # try a few times to avoid a repeat
            cat_name, data = self._pick_category_data(category)
            template = random.choice(TEMPLATES)
            headline = template.format(
                subject=random.choice(data["subjects"]),
                action=random.choice(data["actions"]),
                object=random.choice(data["objects"]),
                place=random.choice(data["places"]),
            )
            if headline != self.last_headline:
                break

        self.last_headline = headline
        credibility = random.randint(0, 15)  # always low, it's fake news!
        shares = random.randint(100, 999_999)
        likes = random.randint(50, 500_000)
        hashtags = " ".join(f"#{tag}" for tag in random.sample(HASHTAG_WORDS, 2))

        entry = {
            "headline": headline,
            "category": cat_name,
            "credibility": credibility,
            "shares": shares,
            "likes": likes,
            "hashtags": hashtags,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.history.append(entry)
        return entry

    def generate_batch(self, n, category="random"):
        return [self.generate(category) for _ in range(n)]

    def save_history(self, filename=None):
        if not self.history:
            return None
        if filename is None:
            filename = f"headlines_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in self.history:
                f.write(f"[{entry['timestamp']}] ({entry['category'].title()})\n")
                f.write(f"{entry['headline']}\n")
                f.write(f"Credibility: {entry['credibility']}%  |  "
                        f"{entry['shares']:,} shares  |  {entry['likes']:,} likes\n")
                f.write(f"{entry['hashtags']}\n")
                f.write("-" * 60 + "\n")
        return filepath


# ---------- Display helpers ----------

def print_entry(entry):
    print()
    print(c(entry["headline"], Fore.GREEN if COLOR_ENABLED else None, bold=True))
    print(c(f"Category: {entry['category'].title()}", Fore.CYAN if COLOR_ENABLED else None))
    print(c(f"Credibility Score: {entry['credibility']}%  "
            f"(trust nothing)", Fore.RED if COLOR_ENABLED else None))
    print(c(f"{entry['shares']:,} shares | {entry['likes']:,} likes",
            Fore.YELLOW if COLOR_ENABLED else None))
    print(c(entry["hashtags"], Fore.MAGENTA if COLOR_ENABLED else None))


def choose_category():
    categories = list(WORD_BANK.keys())
    print("\nChoose a category:")
    print("  0. Random Mix")
    for i, cat in enumerate(categories, start=1):
        print(f"  {i}. {cat.title()}")
    choice = input("Enter number (or press Enter for Random Mix): ").strip()
    if choice == "" or choice == "0":
        return "random"
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(categories):
            return categories[idx]
    except ValueError:
        pass
    print("Invalid choice, defaulting to Random Mix.")
    return "random"


def main_menu():
    gen = HeadlineGenerator(WORD_BANK)
    print(c("=" * 60, Fore.BLUE if COLOR_ENABLED else None))
    print(c("   FAKE + FUNNY NEWS HEADLINE GENERATOR (Advanced)", Fore.BLUE if COLOR_ENABLED else None, bold=True))
    print(c("=" * 60, Fore.BLUE if COLOR_ENABLED else None))

    while True:
        print("\nWhat would you like to do?")
        print("  1. Generate a single headline")
        print("  2. Generate a batch of headlines")
        print("  3. Save session history to file")
        print("  4. View session history")
        print("  5. Exit")
        choice = input("Enter choice (1-5): ").strip()

        if choice == "1":
            category = choose_category()
            entry = gen.generate(category)
            print_entry(entry)

        elif choice == "2":
            category = choose_category()
            try:
                n = int(input("How many headlines? ").strip())
            except ValueError:
                print("Please enter a valid number.")
                continue
            entries = gen.generate_batch(n, category)
            for entry in entries:
                print_entry(entry)

        elif choice == "3":
            path = gen.save_history()
            if path:
                print(c(f"\nSaved {len(gen.history)} headline(s) to: {path}",
                        Fore.GREEN if COLOR_ENABLED else None))
            else:
                print("No headlines generated yet in this session.")

        elif choice == "4":
            if not gen.history:
                print("No headlines generated yet in this session.")
            else:
                for entry in gen.history:
                    print_entry(entry)

        elif choice == "5":
            print(c("\nExiting the news generator. Thank you for using it! Goodbye!",
                    Fore.CYAN if COLOR_ENABLED else None))
            break

        else:
            print("Invalid choice, please enter a number from 1-5.")


if __name__ == "__main__":
    main_menu()
