def build_roster_summary(student_names):
    summary = ""
    for name in student_names:
        summary += name + ", "
    return summary


roster = ["Asha", "Rahul", "Priya", "Kiran"]
print(build_roster_summary(roster))
