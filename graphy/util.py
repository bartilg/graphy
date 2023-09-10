import random
import string
import json

def print_json(json_data):
    """Pretty Prints json data

    Args:
        json_data (json): the json data to be printed
    """
    json_formatted_str = json.dumps(json_data, indent=2)
    print(json_formatted_str)

def gen_password():
    """Generates a random password with w format of UpperLowerLower#####

    Returns:
        string: The randomely generated password
    """
    capital_letter = random.choice(string.ascii_uppercase)
    lowercase_letters = random.choices(string.ascii_lowercase, k=2)
    numbers = random.choices(string.digits, k=5)    
    formatted_string = f"{capital_letter}{''.join(lowercase_letters)}{''.join(numbers)}"
    return formatted_string