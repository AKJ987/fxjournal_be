import re

def is_password_valid(password):
    password_regex = (
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)"
        r"(?=.*[@$!%*?&^#()_+\-=])[A-Za-z\d@$!%*?&^#()_+\-=]{8,}$"
    )
    if not re.match(password_regex, password):
        return False

    return True
