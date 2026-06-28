def average(scores):
    total = 0
    for score in scores:
        total = total + score
    return total / len(scores)


class_marks = [78,85,92,67,73]
print("Average score:", average(class_marks))
