def evaluate_expression(user_expression):
    result = eval(user_expression)
    return result


expression = input("Enter a math expression: ")
print("Result:", evaluate_expression(expression))
