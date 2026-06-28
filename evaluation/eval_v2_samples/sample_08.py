class student_record:
    def __init__(self, name, roll_number):
        self.name = name
        self.roll_number = roll_number

    def display(self):
        print(self.name, self.roll_number)


record = student_record("Rahul", 21)
record.display()
