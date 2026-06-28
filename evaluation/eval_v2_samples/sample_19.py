def is_list_of_marks(marks):
    if type(marks) == list:
        return True
    return False


sample_marks = [80, 90, 70]
print("Is a list:", is_list_of_marks(sample_marks))
