"""
Student Result Management System (Advanced Edition)
-----------------------------------------------------
Features:
  - Multiple subjects per student, with automatic total/percentage/grade calculation
  - Persistent storage in a JSON file (students_data.json) - data survives program restarts
  - Add / View / Search / Update / Delete students
  - Individual report card generation
  - Class analytics: average percentage, topper, pass %, grade distribution,
    subject-wise averages, and a rank list
  - ASCII bar chart for grade distribution (no extra dependencies needed)
  - Export full results to a CSV file (opens directly in Excel/Google Sheets)
  - Input validation throughout (marks range, unique roll numbers, numeric checks)
"""

import json
import os
import csv
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "students_data.json")

# (minimum percentage, grade letter) - checked from highest to lowest
GRADE_SCALE = [
    (90, "A+"),
    (80, "A"),
    (70, "B+"),
    (60, "B"),
    (50, "C"),
    (33, "D"),
    (0, "F"),
]
PASS_MARK = 33  # minimum marks required in EACH subject to pass


def c(text, color=None, bold=False):
    """Wrap text in color codes if colorama is available, otherwise return as-is."""
    if not COLOR_ENABLED or color is None:
        return text
    prefix = (Style.BRIGHT if bold else "") + color
    return f"{prefix}{text}{Style.RESET_ALL}"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Student:
    def __init__(self, roll_no, name, class_section, subjects=None):
        self.roll_no = roll_no
        self.name = name
        self.class_section = class_section
        self.subjects = subjects or {}  # {subject_name: marks}

    def total(self):
        return sum(self.subjects.values())

    def percentage(self):
        if not self.subjects:
            return 0.0
        return round(self.total() / len(self.subjects), 2)

    def grade(self):
        pct = self.percentage()
        for threshold, letter in GRADE_SCALE:
            if pct >= threshold:
                return letter
        return "F"

    def result(self):
        if not self.subjects:
            return "N/A"
        return "Pass" if all(m >= PASS_MARK for m in self.subjects.values()) else "Fail"

    def to_dict(self):
        return {
            "roll_no": self.roll_no,
            "name": self.name,
            "class_section": self.class_section,
            "subjects": self.subjects,
        }

    @staticmethod
    def from_dict(d):
        return Student(d["roll_no"], d["name"], d["class_section"], d.get("subjects", {}))


# ---------------------------------------------------------------------------
# Manager: handles storage, CRUD, and analytics
# ---------------------------------------------------------------------------

class StudentManager:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.students = {}  # roll_no -> Student
        self.load()

    def load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.students = {roll_no: Student.from_dict(d) for roll_no, d in raw.items()}
            except (json.JSONDecodeError, KeyError, TypeError):
                print(c("Warning: data file was corrupted. Starting with an empty database.",
                        Fore.RED if COLOR_ENABLED else None))
                self.students = {}

    def save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({r: s.to_dict() for r, s in self.students.items()}, f, indent=2)

    # --- CRUD ---

    def add_student(self, roll_no, name, class_section, subjects):
        if roll_no in self.students:
            return False, "A student with this roll number already exists."
        self.students[roll_no] = Student(roll_no, name, class_section, subjects)
        self.save()
        return True, "Student added successfully."

    def get_student(self, roll_no):
        return self.students.get(roll_no)

    def search(self, query):
        query = query.strip().lower()
        return [s for s in self.students.values()
                if query in s.name.lower() or query in s.roll_no.lower()]

    def update_marks(self, roll_no, subject, marks):
        student = self.students.get(roll_no)
        if not student:
            return False, "Student not found."
        student.subjects[subject] = marks
        self.save()
        return True, f"Marks for {subject} updated to {marks}."

    def delete_student(self, roll_no):
        if roll_no in self.students:
            del self.students[roll_no]
            self.save()
            return True, "Student deleted."
        return False, "Student not found."

    # --- Analytics ---

    def rank_list(self):
        return sorted(self.students.values(), key=lambda s: s.percentage(), reverse=True)

    def class_average(self):
        if not self.students:
            return 0.0
        return round(sum(s.percentage() for s in self.students.values()) / len(self.students), 2)

    def topper(self):
        if not self.students:
            return None
        return max(self.students.values(), key=lambda s: s.percentage())

    def pass_percentage(self):
        if not self.students:
            return 0.0
        passed = sum(1 for s in self.students.values() if s.result() == "Pass")
        return round(passed / len(self.students) * 100, 2)

    def grade_distribution(self):
        dist = {}
        for s in self.students.values():
            g = s.grade()
            dist[g] = dist.get(g, 0) + 1
        return dist

    def subject_averages(self):
        totals, counts = {}, {}
        for s in self.students.values():
            for subj, mark in s.subjects.items():
                totals[subj] = totals.get(subj, 0) + mark
                counts[subj] = counts.get(subj, 0) + 1
        return {subj: round(totals[subj] / counts[subj], 2) for subj in totals}

    def export_csv(self, filename=None):
        if not self.students:
            return None
        if filename is None:
            filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(BASE_DIR, filename)
        all_subjects = sorted({subj for s in self.students.values() for subj in s.subjects})
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Roll No", "Name", "Class", *all_subjects,
                              "Total", "Percentage", "Grade", "Result"])
            for i, s in enumerate(self.rank_list(), start=1):
                row = [i, s.roll_no, s.name, s.class_section]
                row += [s.subjects.get(subj, "") for subj in all_subjects]
                row += [s.total(), s.percentage(), s.grade(), s.result()]
                writer.writerow(row)
        return filepath


# ---------------------------------------------------------------------------
# Input helpers (validation lives here so the menu code stays clean)
# ---------------------------------------------------------------------------

def input_nonempty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field can't be empty.")


def input_float_range(prompt, low=0, high=100):
    while True:
        raw = input(prompt).strip()
        try:
            val = float(raw)
            if low <= val <= high:
                return val
            print(f"Please enter a value between {low} and {high}.")
        except ValueError:
            print("Please enter a valid number.")


def input_subjects():
    subjects = {}
    print("Enter subjects one at a time. Type 'done' as the subject name when finished.")
    while True:
        subj = input("Subject name (or 'done'): ").strip()
        if subj.lower() == "done":
            if not subjects:
                print("Add at least one subject before finishing.")
                continue
            break
        if not subj:
            print("Subject name can't be empty.")
            continue
        if subj in subjects:
            print(f"'{subj}' was already entered. Skipping duplicate.")
            continue
        mark = input_float_range(f"Marks for {subj} (0-100): ")
        subjects[subj] = mark
    return subjects


def print_bar_chart(data, title):
    print(f"\n{c(title, Fore.CYAN if COLOR_ENABLED else None, bold=True)}")
    if not data:
        print("  (no data)")
        return
    max_val = max(data.values()) or 1
    for label in sorted(data.keys()):
        val = data[label]
        bar_len = int((val / max_val) * 40)
        bar = "#" * bar_len
        print(f"  {str(label):>5} | {bar} {val}")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_student_row(rank, student):
    result_color = None
    if COLOR_ENABLED:
        result_color = Fore.GREEN if student.result() == "Pass" else Fore.RED
    print(f"{rank:<5}{student.roll_no:<10}{student.name:<20}{student.class_section:<10}"
          f"{student.total():<8}{student.percentage():<10}{student.grade():<6}"
          f"{c(student.result(), result_color)}")


def print_table_header():
    print(f"{'Rank':<5}{'Roll No':<10}{'Name':<20}{'Class':<10}"
          f"{'Total':<8}{'%':<10}{'Grade':<6}{'Result'}")
    print("-" * 75)


def print_report_card(student):
    print("\n" + "=" * 45)
    print(c("REPORT CARD".center(45), Fore.BLUE if COLOR_ENABLED else None, bold=True))
    print("=" * 45)
    print(f"Roll No     : {student.roll_no}")
    print(f"Name        : {student.name}")
    print(f"Class       : {student.class_section}")
    print("-" * 45)
    for subj, mark in student.subjects.items():
        status = "Pass" if mark >= PASS_MARK else "Fail"
        color = (Fore.GREEN if status == "Pass" else Fore.RED) if COLOR_ENABLED else None
        print(f"  {subj:<25} {mark:>6.1f}   {c(status, color)}")
    print("-" * 45)
    print(f"Total       : {student.total()}")
    print(f"Percentage  : {student.percentage()}%")
    print(f"Grade       : {student.grade()}")
    result_color = (Fore.GREEN if student.result() == "Pass" else Fore.RED) if COLOR_ENABLED else None
    print(f"Result      : {c(student.result(), result_color, bold=True)}")
    print("=" * 45)


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def action_add_student(mgr):
    print("\n--- Add Student ---")
    roll_no = input_nonempty("Enter roll number: ")
    if mgr.get_student(roll_no):
        print(c("A student with this roll number already exists.", Fore.RED if COLOR_ENABLED else None))
        return
    name = input_nonempty("Enter student name: ")
    class_section = input_nonempty("Enter class/section (e.g. 10-A): ")
    subjects = input_subjects()
    ok, msg = mgr.add_student(roll_no, name, class_section, subjects)
    color = Fore.GREEN if ok else Fore.RED
    print(c(msg, color if COLOR_ENABLED else None))


def action_view_all(mgr):
    print("\n--- All Students (ranked by percentage) ---")
    ranked = mgr.rank_list()
    if not ranked:
        print("No students found!")
        return
    print_table_header()
    for i, s in enumerate(ranked, start=1):
        print_student_row(i, s)


def action_search(mgr):
    print("\n--- Search Student ---")
    query = input_nonempty("Enter name or roll number to search: ")
    results = mgr.search(query)
    if not results:
        print("No matching students found.")
        return
    print_table_header()
    ranked = mgr.rank_list()
    for s in results:
        rank = ranked.index(s) + 1
        print_student_row(rank, s)


def action_update_marks(mgr):
    print("\n--- Update Student Marks ---")
    roll_no = input_nonempty("Enter roll number: ")
    student = mgr.get_student(roll_no)
    if not student:
        print(c("Student not found.", Fore.RED if COLOR_ENABLED else None))
        return
    print(f"Existing subjects: {', '.join(student.subjects.keys()) or '(none)'}")
    subj = input_nonempty("Enter subject to add/update: ")
    mark = input_float_range(f"Enter new marks for {subj} (0-100): ")
    ok, msg = mgr.update_marks(roll_no, subj, mark)
    print(c(msg, (Fore.GREEN if ok else Fore.RED) if COLOR_ENABLED else None))


def action_delete_student(mgr):
    print("\n--- Delete Student ---")
    roll_no = input_nonempty("Enter roll number: ")
    confirm = input(f"Are you sure you want to delete '{roll_no}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return
    ok, msg = mgr.delete_student(roll_no)
    print(c(msg, (Fore.GREEN if ok else Fore.RED) if COLOR_ENABLED else None))


def action_report_card(mgr):
    print("\n--- Generate Report Card ---")
    roll_no = input_nonempty("Enter roll number: ")
    student = mgr.get_student(roll_no)
    if not student:
        print(c("Student not found.", Fore.RED if COLOR_ENABLED else None))
        return
    print_report_card(student)


def action_analytics(mgr):
    print("\n--- Class Analytics & Reports ---")
    if not mgr.students:
        print("No students found! Add some students first.")
        return

    print(f"Total Students   : {len(mgr.students)}")
    print(f"Class Average    : {mgr.class_average()}%")
    print(f"Pass Percentage  : {mgr.pass_percentage()}%")

    topper = mgr.topper()
    if topper:
        print(f"Topper           : {topper.name} ({topper.roll_no}) - {topper.percentage()}%")

    subj_avgs = mgr.subject_averages()
    if subj_avgs:
        print("\nSubject-wise Averages:")
        for subj, avg in subj_avgs.items():
            print(f"  {subj:<20} {avg}")

    print_bar_chart(mgr.grade_distribution(), "Grade Distribution")


def action_export_csv(mgr):
    print("\n--- Export to CSV ---")
    path = mgr.export_csv()
    if path:
        print(c(f"Exported to: {path}", Fore.GREEN if COLOR_ENABLED else None))
    else:
        print("No students to export yet.")


# ---------------------------------------------------------------------------
# Main menu loop
# ---------------------------------------------------------------------------

def main():
    mgr = StudentManager()
    print(c("=" * 55, Fore.BLUE if COLOR_ENABLED else None))
    print(c("   STUDENT RESULT MANAGEMENT SYSTEM (Advanced)".center(55),
            Fore.BLUE if COLOR_ENABLED else None, bold=True))
    print(c("=" * 55, Fore.BLUE if COLOR_ENABLED else None))

    menu_actions = {
        "1": action_add_student,
        "2": action_view_all,
        "3": action_search,
        "4": action_update_marks,
        "5": action_delete_student,
        "6": action_report_card,
        "7": action_analytics,
        "8": action_export_csv,
    }

    while True:
        print("\n1. Add Student")
        print("2. View All Students")
        print("3. Search Student")
        print("4. Update Student Marks")
        print("5. Delete Student")
        print("6. Generate Report Card")
        print("7. Class Analytics & Reports")
        print("8. Export to CSV")
        print("9. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "9":
            print(c("\nExiting the program. All data has been saved. Goodbye!",
                    Fore.CYAN if COLOR_ENABLED else None))
            break
        elif choice in menu_actions:
            menu_actions[choice](mgr)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
