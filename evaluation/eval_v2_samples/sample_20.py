def compute_final_grade(internal_marks, external_marks):
    total = internal_marks + external_marks
    weighted_average = total / 2
    bonus_points = 5
    return weighted_average


final_grade = compute_final_grade(35, 55)
print("Final grade:", final_grade)
