def get_user_role(role):
    if role == None:
        return "guest"
    return role


current_role = None
print("Role assigned:", get_user_role(current_role))
