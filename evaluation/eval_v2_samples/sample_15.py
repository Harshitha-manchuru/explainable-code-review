attendance_count = 0


def mark_present():
    global attendance_count
    attendance_count += 1


mark_present()
mark_present()
print("Total attendance marked:", attendance_count)
