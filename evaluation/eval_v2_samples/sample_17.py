def read_student_file(path):
    with open(path) as f:
        return f.read()


try:
    content = read_student_file("students.txt")
except Exception as error:
    print("Could not read file:", error)
    content = ""

print("File content length:", len(content))
