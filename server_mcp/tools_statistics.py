"""
Statistics Tools
Tools for statistical calculations: mean, median, mode, standard deviation, etc.
"""
import logging
import math
from typing import List, Tuple
from collections import Counter

def log_function(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper


@log_function
def calculate_mean(numbers: List[float]) -> float:
    """
    Calculate arithmetic mean (average) of a list of numbers.
    """
    if not numbers:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(numbers) / len(numbers)


@log_function
def calculate_median(numbers: List[float]) -> float:
    """
    Calculate median of a list of numbers.
    """
    if not numbers:
        raise ValueError("Cannot calculate median of empty list")
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 0:
        # Even number of elements - return average of middle two
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        # Odd number of elements - return middle element
        return sorted_numbers[n//2]


@log_function
def calculate_mode(numbers: List[float]) -> List[float]:
    """
    Calculate mode(s) of a list of numbers.
    Returns list of most frequent values. Can be multiple modes.
    """
    if not numbers:
        raise ValueError("Cannot calculate mode of empty list")
    
    counter = Counter(numbers)
    max_count = max(counter.values())
    modes = [num for num, count in counter.items() if count == max_count]
    
    return sorted(modes)


@log_function
def calculate_range(numbers: List[float]) -> float:
    """
    Calculate range (max - min) of a list of numbers.
    """
    if not numbers:
        raise ValueError("Cannot calculate range of empty list")
    
    return max(numbers) - min(numbers)


@log_function
def calculate_variance(numbers: List[float], sample: bool = True) -> float:
    """
    Calculate variance of a list of numbers.
    
    Args:
        numbers: List of numbers
        sample: If True, calculate sample variance (n-1). If False, population variance (n).
    """
    if not numbers:
        raise ValueError("Cannot calculate variance of empty list")
    
    if sample and len(numbers) < 2:
        raise ValueError("Need at least 2 values for sample variance")
    
    mean = calculate_mean(numbers)
    squared_diffs = [(x - mean) ** 2 for x in numbers]
    
    divisor = len(numbers) - 1 if sample else len(numbers)
    return sum(squared_diffs) / divisor


@log_function
def calculate_standard_deviation(numbers: List[float], sample: bool = True) -> float:
    """
    Calculate standard deviation of a list of numbers.
    
    Args:
        numbers: List of numbers
        sample: If True, calculate sample std dev. If False, population std dev.
    """
    variance = calculate_variance(numbers, sample)
    return math.sqrt(variance)


@log_function
def calculate_percentile(numbers: List[float], percentile: float) -> float:
    """
    Calculate the nth percentile of a list of numbers.
    
    Args:
        numbers: List of numbers
        percentile: Percentile to calculate (0-100)
    """
    if not numbers:
        raise ValueError("Cannot calculate percentile of empty list")
    
    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    # Use linear interpolation
    rank = (percentile / 100) * (n - 1)
    lower_index = int(math.floor(rank))
    upper_index = int(math.ceil(rank))
    
    if lower_index == upper_index:
        return sorted_numbers[lower_index]
    
    # Interpolate
    fraction = rank - lower_index
    return sorted_numbers[lower_index] + fraction * (sorted_numbers[upper_index] - sorted_numbers[lower_index])


@log_function
def calculate_quartiles(numbers: List[float]) -> Tuple[float, float, float]:
    """
    Calculate Q1, Q2 (median), Q3 quartiles of a list of numbers.
    
    Returns:
        Tuple of (Q1, Q2, Q3)
    """
    if not numbers:
        raise ValueError("Cannot calculate quartiles of empty list")
    
    q1 = calculate_percentile(numbers, 25)
    q2 = calculate_percentile(numbers, 50)
    q3 = calculate_percentile(numbers, 75)
    
    return (q1, q2, q3)


@log_function
def calculate_interquartile_range(numbers: List[float]) -> float:
    """
    Calculate IQR (Interquartile Range) = Q3 - Q1
    """
    q1, _, q3 = calculate_quartiles(numbers)
    return q3 - q1


@log_function
def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """
    Calculate z-score: (value - mean) / std_dev
    """
    if std_dev == 0:
        raise ValueError("Standard deviation cannot be zero")
    
    return (value - mean) / std_dev


@log_function
def calculate_correlation_coefficient(x_values: List[float], y_values: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two variables.
    
    Returns value between -1 and 1.
    """
    if not x_values or not y_values:
        raise ValueError("Cannot calculate correlation with empty lists")
    
    if len(x_values) != len(y_values):
        raise ValueError("Lists must have the same length")
    
    n = len(x_values)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    
    mean_x = calculate_mean(x_values)
    mean_y = calculate_mean(y_values)
    
    # Calculate covariance
    covariance = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
    
    # Calculate standard deviations
    std_x = calculate_standard_deviation(x_values, sample=False)
    std_y = calculate_standard_deviation(y_values, sample=False)
    
    if std_x == 0 or std_y == 0:
        raise ValueError("Standard deviation cannot be zero")
    
    return covariance / (n * std_x * std_y)


@log_function
def calculate_linear_regression(x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
    """
    Calculate linear regression: y = mx + b
    
    Returns:
        Tuple of (slope m, intercept b)
    """
    if not x_values or not y_values:
        raise ValueError("Cannot calculate regression with empty lists")
    
    if len(x_values) != len(y_values):
        raise ValueError("Lists must have the same length")
    
    n = len(x_values)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    
    mean_x = calculate_mean(x_values)
    mean_y = calculate_mean(y_values)
    
    # Calculate slope
    numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
    denominator = sum((x_values[i] - mean_x) ** 2 for i in range(n))
    
    if denominator == 0:
        raise ValueError("Cannot calculate slope: all x values are the same")
    
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    
    return (slope, intercept)


@log_function
def calculate_factorial_stat(n: int) -> int:
    """
    Calculate factorial for statistical calculations (n!)
    """
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return math.factorial(n)


@log_function
def calculate_combinations_stat(n: int, r: int) -> int:
    """
    Calculate combinations C(n,r) = n! / (r! * (n-r)!)
    """
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid values for n and r")
    
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))


@log_function
def calculate_probability_union(p_a: float, p_b: float, p_both: float) -> float:
    """
    Calculate P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
    """
    if not (0 <= p_a <= 1 and 0 <= p_b <= 1 and 0 <= p_both <= 1):
        raise ValueError("Probabilities must be between 0 and 1")
    
    return p_a + p_b - p_both


@log_function
def calculate_probability_complement(p: float) -> float:
    """
    Calculate complement probability: P(A') = 1 - P(A)
    """
    if not 0 <= p <= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    return 1 - p

