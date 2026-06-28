def calculate_compound_interest(principal, rate, years):
    amount = principal * ((1 + rate / 100) ** years)
    return amount - principal


interest = calculate_compound_interest(10000, 5, 3)
print("Compound interest earned:", interest)
