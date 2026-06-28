def load_student_config(path):
    with open(path) as config_file:
        return config_file.read()


try:
    settings = load_student_config("config.txt")
except:
    settings = None

print("Settings loaded:", settings is not None)
