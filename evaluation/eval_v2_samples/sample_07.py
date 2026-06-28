def CalculateAverageMarks(marks_list):
    total_marks = sum(marks_list)
    count = len(marks_list)
    return total_marks / count


student_marks = [88, 76, 95, 60]
print("Average marks:", CalculateAverageMarks(student_marks))
