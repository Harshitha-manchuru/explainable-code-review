def calculate_total_invoice(unit_price, quantity, tax_rate, shipping_fee):
    subtotal = unit_price * quantity
    return subtotal + (subtotal * tax_rate) + shipping_fee


invoice_total = calculate_total_invoice(unit_price=499, quantity=3, tax_rate=0.18, shipping_fee=49)
print("Invoice total:", invoice_total)
