def isfloat(num: str):
    try:
        float(num)
        return True
    except ValueError:
        return False

def check_alphanumeric(char: str):
    if isfloat(char):
        return 1
    elif char.isalpha():
        return 2
    else:
        return None