"""
Logical Reasoning Tools
Tools for logical operations, boolean logic, truth tables, and reasoning
"""
import logging
from typing import List, Dict

# Constants for logical operators
OP_AND = " and "
OP_OR = " or "
OP_NOT = " not "

def log_function(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper


@log_function
def evaluate_logical_and(values: List[bool]) -> bool:
    """
    Evaluate logical AND of a list of boolean values.
    Returns True only if all values are True.
    """
    return all(values)


@log_function
def evaluate_logical_or(values: List[bool]) -> bool:
    """
    Evaluate logical OR of a list of boolean values.
    Returns True if at least one value is True.
    """
    return any(values)


@log_function
def evaluate_logical_not(value: bool) -> bool:
    """
    Evaluate logical NOT of a boolean value.
    """
    return not value


@log_function
def evaluate_implication(premise: bool, conclusion: bool) -> bool:
    """
    Evaluate logical implication: premise → conclusion
    Returns False only if premise is True and conclusion is False.
    """
    return (not premise) or conclusion


@log_function
def evaluate_biconditional(a: bool, b: bool) -> bool:
    """
    Evaluate biconditional: a ↔ b
    Returns True if both have the same truth value.
    """
    return a == b


@log_function
def evaluate_xor(a: bool, b: bool) -> bool:
    """
    Evaluate exclusive OR (XOR): a ⊕ b
    Returns True if exactly one is True.
    """
    return a != b


@log_function
def solve_syllogism(major_premise: bool, minor_premise: bool) -> bool:
    """
    Solve a simple syllogism using modus ponens.
    If major_premise AND minor_premise are both True, conclusion is True.
    """
    return major_premise and minor_premise


@log_function
def count_true_values(values: List[bool]) -> int:
    """
    Count the number of True values in a list.
    """
    return sum(values)


@log_function
def majority_vote(values: List[bool]) -> bool:
    """
    Return True if majority of values are True, False otherwise.
    """
    if not values:
        return False
    true_count = sum(values)
    return true_count > len(values) / 2


@log_function
def evaluate_complex_expression(expression: str, variables: Dict[str, bool]) -> bool:
    """
    Evaluate a complex logical expression with given variable values.
    Supports: AND (and, &), OR (or, |), NOT (not, ~), parentheses
    
    Example: "A and (B or not C)" with {"A": True, "B": False, "C": True}
    """
    # Replace variable names with their values
    expr = expression
    for var, val in variables.items():
        expr = expr.replace(var, str(val))
    
    # Replace logical operators with Python operators
    expr = expr.replace(OP_AND, OP_AND)
    expr = expr.replace(OP_OR, OP_OR)
    expr = expr.replace(OP_NOT, OP_NOT)
    expr = expr.replace("&", OP_AND)
    expr = expr.replace("|", OP_OR)
    expr = expr.replace("~", OP_NOT)
    
    try:
        return eval(expr)
    except Exception as e:
        logging.error(f"Error evaluating expression '{expression}': {e}")
        raise ValueError(f"Invalid logical expression: {expression}")

