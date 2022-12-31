from timelength.constants import CONNECTORS, ABBREVIATIONS

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

def check_valid_values(buffer: str):
    if isfloat(buffer) or buffer in CONNECTORS or buffer in ABBREVIATIONS:
        return True
    else:
        return False