def convert_grade_to_gpa(grade, max_grade):
    return (grade / max_grade) * 10


student_gpa = convert_grade_to_gpa(85, 100)
print("GPA:", student_gpa)
