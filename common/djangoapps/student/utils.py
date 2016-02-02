def base36encode(number):
    """Encode number to string of alphanumeric characters (0 to z). (Code taken from Wikipedia)."""
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')

    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36

    return base36 or alphabet[0]


def base36decode(numstr):
    """Convert a base-36 string (made of alphanumeric characters) to its numeric value."""
    return int(numstr,36)
