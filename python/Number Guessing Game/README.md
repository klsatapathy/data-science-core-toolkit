# 🎯 Logical Number Guesser - GUI Edition

A modern **Python Tkinter GUI** game where you try to guess a randomly generated number while competing against the **Binary Search algorithm**.

The game isn't just about guessing—it's about improving your logical thinking and comparing your strategy with the optimal computer algorithm.

---

## ✨ Features

### 🎮 Gameplay
- Three difficulty levels:
  - 🟢 Easy (1–50)
  - 🟡 Medium (1–100)
  - 🔴 Hard (1–500)

- Live timer
- Attempt counter
- Instant feedback after every guess
- Interactive GUI built with Tkinter

---

### 📈 Visual Learning

- Dynamic number line visualization
- Search range shrinks after every guess
- Guess history with:
  - 📉 Too Low
  - 📈 Too High
  - ✅ Correct

---

### 🤖 AI Opponent

After winning, the game shows how a computer using the **Binary Search Algorithm** would solve the same problem.

It displays:

- Every AI guess
- Remaining search range
- Total AI attempts
- Comparison between your performance and the optimal algorithm

---

### 🏆 Leaderboard

Your best score is automatically saved for each difficulty.

The leaderboard tracks:

- Least attempts
- Fastest completion time

Scores are stored locally in:

```
leaderboard.json
```

So your progress remains even after closing the application.

---

## 📁 Project Structure

```
Number Guessing Game/
│
├── number_guesser_gui.py
├── leaderboard.json
└── README.md
```

---

## 🚀 Getting Started

### Clone the repository

```bash
git clone https://github.com/your-username/data-science-core-toolkit.git
```

### Navigate to the project

```bash
cd data-science-core-toolkit/Python/"Number Guessing Game"
```

### Run the application

```bash
python number_guesser_gui.py
```

---

## 🖥️ How to Play

1. Select a difficulty level.
2. Click **Start Game**.
3. Enter your guess.
4. The game will tell you whether your guess is:
   - Too High
   - Too Low
   - Correct
5. Keep narrowing the search range until you find the secret number.
6. Compare your performance with the Binary Search AI.

---

## 🎯 Difficulty Levels

| Difficulty | Range |
|------------|-------|
| Easy | 1 - 50 |
| Medium | 1 - 100 |
| Hard | 1 - 500 |

---

## 📊 Technologies Used

- Python 3
- Tkinter
- JSON
- Object-Oriented Programming (OOP)

---

## 🧠 Concepts Demonstrated

This project demonstrates:

- GUI Development using Tkinter
- Event-driven Programming
- Binary Search Algorithm
- JSON File Handling
- Object-Oriented Programming
- Data Persistence
- Canvas Graphics
- User Input Validation

---

## 📸 Screens

The application includes:

- 🎮 Start Screen
- 📊 Live Number Line Visualization
- 📜 Guess History
- ⏱️ Timer & Attempt Counter
- 🏆 Leaderboard
- 🤖 AI Comparison Window

---

## 🔮 Future Improvements

- Multiple themes (Dark / Light)
- Sound effects
- Difficulty customization
- Multiplayer mode
- Online leaderboard
- Animated transitions
- Hint system

---

## 💡 Why This Project?

Unlike a basic number guessing game, this project focuses on **algorithmic thinking**.

Players can compare their own strategy against the **Binary Search Algorithm**, making it both educational and entertaining.

---

## 📄 License

This project is open-source and intended for learning and educational purposes.

---

## 👨‍💻 Author

Developed with ❤️ using Python.
