def positive_int(value, field="quantity"):
    try: value=int(value)
    except (TypeError,ValueError): raise ValueError(f"{field} must be a whole number")
    if value <= 0: raise ValueError(f"{field} must be greater than zero")
    return value

def validate_barcode(value):
    value=str(value).strip()
    if not value.isdigit() or not (8 <= len(value) <= 14):
        raise ValueError("Barcode must contain 8–14 digits")
    return value
