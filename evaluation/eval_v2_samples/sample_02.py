def apply_discount(price, percent):
    discount = price*percent/100
    final_price = price-discount
    return final_price


item_price = 250
discount_percent = 10
print("Final price:", apply_discount(item_price, discount_percent))
