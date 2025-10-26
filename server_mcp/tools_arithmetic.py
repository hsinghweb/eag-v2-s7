import logging
import math
import sqlite3

def log_function(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper

DATABASE_PATH = r"D:\Himanshu\EAG-V2\emloyee_salary.db"

@log_function
def number_list_to_sum(lst):
    if not lst:
        return 0
    return sum(lst)


@log_function
def add_numbers(a: float, b: float):
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b

@log_function
def calculate_difference(a, b):
    return a - b

@log_function
def number_list_to_product(lst):
    if not lst:
        return 0
    result = 1
    for num in lst:
        result *= num
    return result

@log_function
def calculate_division(a, b):
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

@log_function
def strings_to_chars_to_int(s):
    return [ord(c) for c in s]

@log_function
def int_list_to_exponential_values(lst):
    return [math.e**x for x in lst]

@log_function
def fibonacci_numbers(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib[:n]

@log_function
def calculate_factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return [1]
    factorials = [1]  # 0!
    current = 1
    for i in range(1, n):
        current *= i
        factorials.append(current)
    return factorials

@log_function
def calculate_permutation(n, r):
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid values for n and r in permutation")
    return math.factorial(n) // math.factorial(n - r)


@log_function
def calculate_combination(n, r):
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid values for n and r in combination")
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r)) 


@log_function
def calculate_salary_for_id(emp_id: int, db_path: str = DATABASE_PATH):
    """Return the salary for the given employee id from the SQLite database.

    Args:
        emp_id (int): The id of the employee whose salary needs to be fetched.
        db_path (str, optional): Path to the SQLite database. Defaults to DATABASE_PATH.

    Returns:
        float | int | None: Salary of the employee if found else None.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT salary FROM employee WHERE id = ?", (emp_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if 'conn' in locals():
            conn.close()

@log_function
def calculate_salary_for_name(emp_name: str, db_path: str = DATABASE_PATH):
    """Return the salary for the given employee name from the SQLite database.

    Args:
        emp_name (str): The name of the employee whose salary needs to be fetched.
        db_path (str, optional): Path to the SQLite database. Defaults to DATABASE_PATH.

    Returns:
        float | int | None: Salary of the employee if found else None.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT salary FROM employee WHERE name = ?", (emp_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if 'conn' in locals():
            conn.close()


@log_function
def calculate_percentage(percent: float | int, number: float | int):
    """Calculate the percentage of a given number.

    Args:
        percent (float | int): The percentage value (e.g., 10 for 10%).
        number (float | int): The base number on which percentage is calculated.

    Returns:
        float: The calculated percentage value.

    Example:
        >>> calculate_percentage(10, 5000)
        500.0
    """
    return (percent / 100) * number


@log_function
def calculate_absolute_value(number: float | int):
    """Calculate the absolute value of a number.

    Args:
        number (float | int): The input number.

    Returns:
        float: The absolute value.

    Example:
        >>> calculate_absolute_value(-5)
        5
    """
    return abs(number)


@log_function
def calculate_modulo(a: float | int, b: float | int):
    """Calculate modulo (remainder after division).

    Args:
        a (float | int): The dividend.
        b (float | int): The divisor.

    Returns:
        float: The remainder.

    Example:
        >>> calculate_modulo(17, 5)
        2
    """
    if b == 0:
        raise ValueError("Modulo by zero is not allowed")
    return a % b


@log_function
def calculate_floor_division(a: float | int, b: float | int):
    """Calculate floor division (integer division).

    Args:
        a (float | int): The dividend.
        b (float | int): The divisor.

    Returns:
        int: The quotient (rounded down).

    Example:
        >>> calculate_floor_division(17, 5)
        3
    """
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a // b


@log_function
def calculate_ceiling(number: float):
    """Round number up to nearest integer.

    Args:
        number (float): The input number.

    Returns:
        int: The ceiling value.

    Example:
        >>> calculate_ceiling(4.2)
        5
    """
    return math.ceil(number)


@log_function
def calculate_floor(number: float):
    """Round number down to nearest integer.

    Args:
        number (float): The input number.

    Returns:
        int: The floor value.

    Example:
        >>> calculate_floor(4.8)
        4
    """
    return math.floor(number)


@log_function
def calculate_round(number: float, decimals: int = 0):
    """Round number to specified decimal places.

    Args:
        number (float): The input number.
        decimals (int): Number of decimal places (default: 0).

    Returns:
        float: The rounded value.

    Example:
        >>> calculate_round(3.14159, 2)
        3.14
    """
    return round(number, decimals)


@log_function
def calculate_gcd(a: int, b: int):
    """Calculate Greatest Common Divisor (GCD) of two numbers.

    Args:
        a (int): First number.
        b (int): Second number.

    Returns:
        int: The GCD.

    Example:
        >>> calculate_gcd(48, 18)
        6
    """
    return math.gcd(a, b)


@log_function
def calculate_lcm(a: int, b: int):
    """Calculate Least Common Multiple (LCM) of two numbers.

    Args:
        a (int): First number.
        b (int): Second number.

    Returns:
        int: The LCM.

    Example:
        >>> calculate_lcm(12, 18)
        36
    """
    return abs(a * b) // math.gcd(a, b) if a and b else 0


@log_function
def is_prime(n: int):
    """Check if a number is prime.

    Args:
        n (int): The number to check.

    Returns:
        bool: True if prime, False otherwise.

    Example:
        >>> is_prime(17)
        True
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


@log_function
def find_prime_factors(n: int):
    """Find all prime factors of a number.

    Args:
        n (int): The number to factorize.

    Returns:
        list: List of prime factors.

    Example:
        >>> find_prime_factors(60)
        [2, 2, 3, 5]
    """
    if n < 2:
        return []
    
    factors = []
    # Check for 2s
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    
    # Check for odd factors
    i = 3
    while i * i <= n:
        while n % i == 0:
            factors.append(i)
            n //= i
        i += 2
    
    # If n is still greater than 2, it's prime
    if n > 2:
        factors.append(n)
    
    return factors


@log_function
def calculate_average(numbers: list):
    """Calculate average (mean) of a list of numbers.

    Args:
        numbers (list): List of numbers.

    Returns:
        float: The average value.

    Example:
        >>> calculate_average([10, 20, 30])
        20.0
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


@log_function
def find_max(numbers: list):
    """Find maximum value in a list.

    Args:
        numbers (list): List of numbers.

    Returns:
        float: The maximum value.

    Example:
        >>> find_max([10, 20, 5, 30])
        30
    """
    if not numbers:
        raise ValueError("Cannot find max of empty list")
    return max(numbers)


@log_function
def find_min(numbers: list):
    """Find minimum value in a list.

    Args:
        numbers (list): List of numbers.

    Returns:
        float: The minimum value.

    Example:
        >>> find_min([10, 20, 5, 30])
        5
    """
    if not numbers:
        raise ValueError("Cannot find min of empty list")
    return min(numbers)


@log_function
def calculate_square(number: float | int):
    """Calculate square of a number.

    Args:
        number (float | int): The input number.

    Returns:
        float: The square value.

    Example:
        >>> calculate_square(5)
        25
    """
    return number ** 2


@log_function
def calculate_square_root(number: float | int):
    """Calculate square root of a number.

    Args:
        number (float | int): The input number.

    Returns:
        float: The square root.

    Example:
        >>> calculate_square_root(25)
        5.0
    """
    if number < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(number)


@log_function
def calculate_cube(number: float | int):
    """Calculate cube of a number.

    Args:
        number (float | int): The input number.

    Returns:
        float: The cube value.

    Example:
        >>> calculate_cube(3)
        27
    """
    return number ** 3


@log_function
def calculate_cube_root(number: float | int):
    """Calculate cube root of a number.

    Args:
        number (float | int): The input number.

    Returns:
        float: The cube root.

    Example:
        >>> calculate_cube_root(27)
        3.0
    """
    if number < 0:
        return -(abs(number) ** (1/3))
    return number ** (1/3)


@log_function
def convert_to_fraction(decimal: float, max_denominator: int = 100):
    """Convert decimal to fraction.

    Args:
        decimal (float): The decimal number.
        max_denominator (int): Maximum denominator to try (default: 100).

    Returns:
        tuple: (numerator, denominator).

    Example:
        >>> convert_to_fraction(0.75)
        (3, 4)
    """
    from fractions import Fraction
    frac = Fraction(decimal).limit_denominator(max_denominator)
    return (frac.numerator, frac.denominator)


@log_function
def calculate_reciprocal(number: float | int):
    """Calculate reciprocal (1/x) of a number.

    Args:
        number (float | int): The input number.

    Returns:
        float: The reciprocal.

    Example:
        >>> calculate_reciprocal(4)
        0.25
    """
    if number == 0:
        raise ValueError("Reciprocal of zero is undefined")
    return 1 / number