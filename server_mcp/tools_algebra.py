"""
Algebraic Tools
Tools for solving equations, simplifying expressions, and algebraic operations
"""
import logging
import math
import re
from typing import List, Tuple, Optional

def log_function(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper


def parse_linear_equation(equation_string: str) -> Tuple[float, float]:
    """
    Parse a linear equation string like "2x + 5 = 0" or "x + 4 = 5" into coefficients.
    
    Args:
        equation_string: String representation of equation
        
    Returns:
        Tuple of (a, b) where equation is ax + b = 0
    """
    # Remove spaces
    eq = equation_string.replace(" ", "").lower()
    
    # Split by equals sign
    if "=" not in eq:
        raise ValueError("Equation must contain '=' sign")
    
    left, right = eq.split("=")
    
    # Parse right side
    try:
        right_val = float(right)
    except ValueError:
        raise ValueError("Right side of equation must be a number")
    
    # Parse left side for ax + b form
    # Handle patterns like: 2x+5, x+5, -x+5, 2x-5, etc.
    
    # Initialize coefficients
    a = 0  # coefficient of x
    b = 0  # constant term
    
    # Find x coefficient
    x_match = re.search(r'([+-]?\d*\.?\d*)x', left)
    if x_match:
        coef = x_match.group(1)
        if coef in ['', '+']:
            a = 1
        elif coef == '-':
            a = -1
        else:
            a = float(coef)
    
    # Find constant term (number not attached to x)
    # Remove the x term first
    left_without_x = re.sub(r'[+-]?\d*\.?\d*x', '', left)
    if left_without_x:
        # Handle remaining constants
        const_match = re.search(r'([+-]?\d+\.?\d*)', left_without_x)
        if const_match:
            b = float(const_match.group(1))
    
    # Adjust for equation form: ax + b = c becomes ax + (b-c) = 0
    b = b - right_val
    
    return (a, b)


def _parse_coefficient(coef: str) -> float:
    """Parse coefficient string to float value."""
    if coef in ['', '+']:
        return 1
    elif coef == '-':
        return -1
    return float(coef)


def _extract_x2_coefficient(left: str) -> float:
    """Extract x² coefficient from equation left side."""
    x2_patterns = [r'([+-]?\d*\.?\d*)x\*\*2', r'([+-]?\d*\.?\d*)x2', r'([+-]?\d*\.?\d*)x²']
    for pattern in x2_patterns:
        x2_match = re.search(pattern, left)
        if x2_match:
            return _parse_coefficient(x2_match.group(1))
    return 0


def _extract_x_coefficient(left: str) -> float:
    """Extract x coefficient (not x²) from equation left side."""
    left_temp = re.sub(r'[+-]?\d*\.?\d*x(\*\*2|2|²)', '', left)
    x_match = re.search(r'([+-]?\d*\.?\d*)x', left_temp)
    if x_match:
        return _parse_coefficient(x_match.group(1))
    return 0


def _extract_constant(left: str) -> float:
    """Extract constant term from equation left side."""
    left_temp = re.sub(r'[+-]?\d*\.?\d*x(\*\*2|2|²)?', '', left)
    if left_temp:
        const_match = re.search(r'([+-]?\d+\.?\d*)', left_temp)
        if const_match:
            return float(const_match.group(1))
    return 0


def parse_quadratic_equation(equation_string: str) -> Tuple[float, float, float]:
    """
    Parse a quadratic equation string like "x^2 - 5x + 6 = 0" into coefficients.
    
    Args:
        equation_string: String representation of equation
        
    Returns:
        Tuple of (a, b, c) where equation is ax² + bx + c = 0
    """
    eq = equation_string.replace(" ", "").lower().replace("^", "**")
    
    if "=" not in eq:
        raise ValueError("Equation must contain '=' sign")
    
    left, right = eq.split("=")
    
    try:
        right_val = float(right)
    except ValueError:
        raise ValueError("Right side of equation must be a number")
    
    a = _extract_x2_coefficient(left)
    b = _extract_x_coefficient(left)
    c = _extract_constant(left) - right_val
    
    return (a, b, c)


@log_function
def solve_linear_equation(a: float, b: float) -> Optional[float]:
    """
    Solve linear equation: ax + b = 0
    Returns x value or None if no solution exists.
    """
    if a == 0:
        return None  # No solution or infinite solutions
    return -b / a


@log_function
def solve_quadratic_equation(a: float, b: float, c: float) -> List[float]:
    """
    Solve quadratic equation: ax² + bx + c = 0
    Returns list of real solutions (0, 1, or 2 solutions).
    """
    if a == 0:
        # Not a quadratic equation, try linear
        if b == 0:
            return []
        return [-c / b]
    
    discriminant = b**2 - 4*a*c
    
    if discriminant < 0:
        return []  # No real solutions
    elif discriminant == 0:
        return [-b / (2*a)]  # One solution
    else:
        sqrt_discriminant = math.sqrt(discriminant)
        x1 = (-b + sqrt_discriminant) / (2*a)
        x2 = (-b - sqrt_discriminant) / (2*a)
        return [x1, x2]


@log_function
def evaluate_polynomial(coefficients: List[float], x: float) -> float:
    """
    Evaluate polynomial at x.
    coefficients: [a0, a1, a2, ...] represents a0 + a1*x + a2*x² + ...
    """
    result = 0
    for i, coeff in enumerate(coefficients):
        result += coeff * (x ** i)
    return result


@log_function
def solve_system_2x2(a1: float, b1: float, c1: float, a2: float, b2: float, c2: float) -> Optional[Tuple[float, float]]:
    """
    Solve system of 2 linear equations:
    a1*x + b1*y = c1
    a2*x + b2*y = c2
    
    Returns (x, y) or None if no unique solution.
    """
    determinant = a1*b2 - a2*b1
    
    if determinant == 0:
        return None  # No unique solution
    
    x = (c1*b2 - c2*b1) / determinant
    y = (a1*c2 - a2*c1) / determinant
    
    return (x, y)


@log_function
def calculate_power(base: float, exponent: float) -> float:
    """
    Calculate base raised to exponent.
    """
    return base ** exponent


@log_function
def calculate_nth_root(number: float, n: int) -> float:
    """
    Calculate nth root of a number.
    """
    if n == 0:
        raise ValueError("Root degree cannot be zero")
    if number < 0 and n % 2 == 0:
        raise ValueError("Even root of negative number is not real")
    
    if number < 0:
        return -(abs(number) ** (1/n))
    return number ** (1/n)


@log_function
def expand_binomial(a: float, b: float, n: int) -> List[float]:
    """
    Expand (a + b)^n using binomial theorem.
    Returns coefficients [c0, c1, c2, ...] where result is c0*a^n + c1*a^(n-1)*b + ...
    """
    coefficients = []
    for k in range(n + 1):
        # Binomial coefficient C(n, k)
        binom_coeff = math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
        # Calculate a^(n-k) * b^k with the binomial coefficient
        term_value = binom_coeff * (a ** (n - k)) * (b ** k)
        coefficients.append(term_value)
    return coefficients


@log_function
def calculate_arithmetic_sequence_sum(first: float, last: float, n: int) -> float:
    """
    Calculate sum of arithmetic sequence.
    Sum = n * (first + last) / 2
    """
    return n * (first + last) / 2


@log_function
def calculate_geometric_sequence_sum(first: float, ratio: float, n: int) -> float:
    """
    Calculate sum of geometric sequence.
    Sum = first * (1 - ratio^n) / (1 - ratio) if ratio != 1
    """
    if ratio == 1:
        return first * n
    return first * (1 - ratio**n) / (1 - ratio)


@log_function
def find_arithmetic_sequence_term(first: float, common_diff: float, n: int) -> float:
    """
    Find nth term of arithmetic sequence.
    a_n = first + (n-1) * common_diff
    """
    return first + (n - 1) * common_diff


@log_function
def find_geometric_sequence_term(first: float, ratio: float, n: int) -> float:
    """
    Find nth term of geometric sequence.
    a_n = first * ratio^(n-1)
    """
    return first * (ratio ** (n - 1))


@log_function
def simplify_ratio(a: float, b: float) -> Tuple[float, float]:
    """
    Simplify ratio a:b to lowest terms.
    Returns (simplified_a, simplified_b)
    """
    if b == 0:
        raise ValueError("Second term of ratio cannot be zero")
    
    # Find GCD
    def gcd(x, y):
        x, y = abs(x), abs(y)
        while y:
            x, y = y, x % y
        return x
    
    divisor = gcd(int(a), int(b))
    if divisor == 0:
        return (a, b)
    
    return (a / divisor, b / divisor)

