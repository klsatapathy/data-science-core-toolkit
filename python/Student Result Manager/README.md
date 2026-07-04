
# 🎓 Student Result Management System

A complete Python-based Student Result Management System that helps manage student records, calculate results, generate analytics, and export data efficiently.

---

## 🚀 Features

- ➕ Add, View, Search, Update, and Delete students
- 📚 Multiple subjects per student
- 🧮 Automatic calculation of:
  - Total marks
  - Percentage
  - Grade
- 💾 Persistent storage using JSON (`students_data.json`)
- 🏆 Rank list based on performance
- 📊 Class analytics:
  - Class average
  - Topper details
  - Pass percentage
  - Subject-wise averages
  - Grade distribution (ASCII bar chart)
- 🧾 Individual report card generation
- 📤 Export data to CSV (Excel / Google Sheets compatible)
- ⚠️ Input validation (marks, roll numbers, etc.)
- 🎨 Optional colored terminal output (Colorama)

---

## 📁 Project Structure

```

Student Result Manager/
│
├── main.py
├── students_data.json
├── students_export.csv   (auto-generated)
└── README.md

````

---

## ▶️ How to Run

### 1. Clone the repository
```bash
git clone https://github.com/your-username/data-science-core-toolkit.git
````

### 2. Go to project folder

```bash
cd data-science-core-toolkit/Python/Student\ Result\ Manager
```

### 3. Run the program

```bash
python main.py
```

---

## 🧪 How It Works

1. Run the program
2. Choose an option from the menu:

   * Add Student
   * View Students
   * Search Student
   * Update Marks
   * Delete Student
   * Generate Report Card
   * View Analytics
   * Export CSV
3. Data is automatically saved in JSON file

---

## 📊 Sample Report Card

```
=============================================
             REPORT CARD
=============================================
Roll No     : 01
Name        : Aarav Sharma
Class       : X-A
---------------------------------------------
Math            92   Pass
Science         88   Pass
English         90   Pass
Computer        95   Pass
Social Science  86   Pass
---------------------------------------------
Total       : 451
Percentage  : 90.2%
Grade       : A+
Result      : PASS
=============================================
```

---

## 📈 Analytics Example

```
Class Average    : 78.4%
Pass Percentage  : 92%
Topper           : Priya Singh (98.6%)
```

Grade Distribution:

```
A+ | #######
A  | ##########
B+ | #####
B  | ###
C  | ##
D  | #
```

---

## 🛠️ Tech Stack

* Python 🐍
* JSON (data storage)
* CSV (export feature)
* OOP (Object-Oriented Programming)
* CLI (Command Line Interface)

---

## 🎯 Learning Outcomes

This project demonstrates:

* Object-Oriented Programming (OOP)
* File handling (JSON, CSV)
* Data validation techniques
* Real-world CRUD system design
* Data analytics basics
* CLI application development

---

## 🔮 Future Improvements

* 🌐 Web version using Flask / Django
* 🗄️ Database integration (SQLite / MySQL)
* 📊 Graphical dashboard (Matplotlib / Plotly)
* 🔐 Login system (Admin/Teacher)
* 📱 Mobile app version

---

## ⚠️ Disclaimer

This project is created for educational purposes only.

---

## ⭐ Support

If you like this project:

* Give a ⭐ on GitHub
* Fork it
* Improve it further

---
