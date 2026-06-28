def add_enrolled_course(course_name, enrolled_courses=[]):
    enrolled_courses.append(course_name)
    return enrolled_courses


first_student_courses = add_enrolled_course("Data Structures")
second_student_courses = add_enrolled_course("Operating Systems")
print(second_student_courses)
