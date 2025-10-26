"""
Pydantic models for input and output validation of MCP tools.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict

# Constants for common field descriptions
LIST_OF_NUMBERS_DESC = "List of numbers"
FIRST_TERM_DESC = "First term"


# PowerPoint Tool Models
class DrawRectangleInput(BaseModel):
    """Input model for drawing rectangles in PowerPoint"""
    x1: int = Field(default=1, ge=1, le=8, description="X-coordinate of top-left corner")
    y1: int = Field(default=1, ge=1, le=8, description="Y-coordinate of top-left corner")
    x2: int = Field(default=8, ge=1, le=8, description="X-coordinate of bottom-right corner")
    y2: int = Field(default=6, ge=1, le=8, description="Y-coordinate of bottom-right corner")
    
    @validator('x2')
    def x2_must_be_greater_than_x1(cls, v, values):
        if 'x1' in values and v <= values['x1']:
            raise ValueError('x2 must be greater than x1')
        return v
    
    @validator('y2')
    def y2_must_be_greater_than_y1(cls, v, values):
        if 'y1' in values and v <= values['y1']:
            raise ValueError('y2 must be greater than y1')
        return v


class DrawRectangleOutput(BaseModel):
    """Output model for draw rectangle operation"""
    success: bool
    message: str


class AddTextInput(BaseModel):
    """Input model for adding text in PowerPoint"""
    text: str = Field(..., min_length=1, description="Text to add to the slide")


class AddTextOutput(BaseModel):
    """Output model for add text operation"""
    success: bool
    message: str


class PowerPointOperationOutput(BaseModel):
    """Generic output model for PowerPoint operations"""
    success: bool
    message: str


# Email Tool Models
class SendGmailInput(BaseModel):
    """Input model for sending Gmail"""
    content: str = Field(..., min_length=1, description="Email content to send")


class SendGmailOutput(BaseModel):
    """Output model for send Gmail operation"""
    success: bool
    message: str
    recipient: Optional[str] = None


# Math Tool Models
class NumberListInput(BaseModel):
    """Input model for list-based math operations"""
    numbers: List[float] = Field(..., min_items=1, description=LIST_OF_NUMBERS_DESC)


class NumberListOutput(BaseModel):
    """Output model for list-based math operations"""
    result: float


class TwoNumberInput(BaseModel):
    """Input model for two-number operations"""
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")


class TwoNumberOutput(BaseModel):
    """Output model for two-number operations"""
    result: float


class SingleNumberInput(BaseModel):
    """Input model for single-number operations"""
    value: float = Field(..., description="Input number")


class SingleNumberOutput(BaseModel):
    """Output model for single-number operations"""
    result: float


class SingleIntInput(BaseModel):
    """Input model for single integer operations"""
    n: int = Field(..., description="Input integer")


class TwoIntInput(BaseModel):
    """Input model for two integer operations"""
    a: int = Field(..., description="First integer")
    b: int = Field(..., description="Second integer")


class RoundInput(BaseModel):
    """Input model for rounding operations"""
    number: float = Field(..., description="Number to round")
    decimals: int = Field(default=0, ge=0, description="Number of decimal places")


class PrimeCheckOutput(BaseModel):
    """Output model for prime check"""
    result: bool
    number: int


class PrimeFactorsOutput(BaseModel):
    """Output model for prime factorization"""
    factors: List[int]


class FractionOutput(BaseModel):
    """Output model for fraction conversion"""
    numerator: int
    denominator: int


class FractionInput(BaseModel):
    """Input model for fraction conversion"""
    decimal: float = Field(..., description="Decimal number to convert")
    max_denominator: int = Field(default=100, ge=1, description="Maximum denominator")


class PercentageInput(BaseModel):
    """Input model for percentage calculation"""
    percent: float = Field(..., ge=0, description="Percentage value")
    number: float = Field(..., description="Base number")


class PercentageOutput(BaseModel):
    """Output model for percentage calculation"""
    result: float


class StringToCharsInput(BaseModel):
    """Input model for converting string to ASCII values"""
    text: str = Field(..., min_length=1, description="Input string")


class StringToCharsOutput(BaseModel):
    """Output model for string to ASCII conversion"""
    ascii_values: List[int]


class ExponentialInput(BaseModel):
    """Input model for exponential operations"""
    numbers: List[float] = Field(..., min_items=1, description="List of numbers for exponential")


class ExponentialOutput(BaseModel):
    """Output model for exponential operations"""
    values: List[float]


class FibonacciInput(BaseModel):
    """Input model for Fibonacci sequence"""
    n: int = Field(..., ge=0, description="Number of Fibonacci numbers to generate")


class FibonacciOutput(BaseModel):
    """Output model for Fibonacci sequence"""
    sequence: List[int]


class FactorialInput(BaseModel):
    """Input model for factorial calculation"""
    n: int = Field(..., ge=0, description="Number for factorial calculation")


class FactorialOutput(BaseModel):
    """Output model for factorial calculation"""
    factorials: List[int]


class PermutationInput(BaseModel):
    """Input model for permutation calculation"""
    n: int = Field(..., ge=0, description="Total number of items")
    r: int = Field(..., ge=0, description="Number of items to arrange")
    
    @validator('r')
    def r_must_not_exceed_n(cls, v, values):
        if 'n' in values and v > values['n']:
            raise ValueError('r cannot be greater than n')
        return v


class PermutationOutput(BaseModel):
    """Output model for permutation calculation"""
    result: int


class CombinationInput(BaseModel):
    """Input model for combination calculation"""
    n: int = Field(..., ge=0, description="Total number of items")
    r: int = Field(..., ge=0, description="Number of items to select")
    
    @validator('r')
    def r_must_not_exceed_n(cls, v, values):
        if 'n' in values and v > values['n']:
            raise ValueError('r cannot be greater than n')
        return v


class CombinationOutput(BaseModel):
    """Output model for combination calculation"""
    result: int


class EmployeeIdInput(BaseModel):
    """Input model for employee salary lookup by ID"""
    emp_id: int = Field(..., ge=1, description="Employee ID")


class EmployeeNameInput(BaseModel):
    """Input model for employee salary lookup by name"""
    emp_name: str = Field(..., min_length=1, description="Employee name")


class SalaryOutput(BaseModel):
    """Output model for salary queries"""
    salary: Optional[float]
    found: bool


class FallbackInput(BaseModel):
    """Input model for fallback reasoning"""
    description: str = Field(..., min_length=1, description="Description of the fallback situation")


class FallbackOutput(BaseModel):
    """Output model for fallback reasoning"""
    message: str


# ============================================
# Logical Reasoning Tool Models
# ============================================

class BooleanListInput(BaseModel):
    """Input model for boolean list operations"""
    values: List[bool] = Field(..., min_items=1, description="List of boolean values")


class BooleanOutput(BaseModel):
    """Output model for boolean operations"""
    result: bool


class TwoBooleanInput(BaseModel):
    """Input model for two-boolean operations"""
    a: bool = Field(..., description="First boolean value")
    b: bool = Field(..., description="Second boolean value")


class SingleBooleanInput(BaseModel):
    """Input model for single boolean operations"""
    value: bool = Field(..., description="Boolean value")


class LogicalExpressionInput(BaseModel):
    """Input model for complex logical expressions"""
    expression: str = Field(..., min_length=1, description="Logical expression")
    variables: Dict[str, bool] = Field(..., description="Variable assignments")


class IntOutput(BaseModel):
    """Output model for integer results"""
    result: int


# ============================================
# Algebra Tool Models
# ============================================

class LinearEquationInput(BaseModel):
    """Input model for linear equation: ax + b = 0"""
    a: Optional[float] = Field(None, description="Coefficient a")
    b: Optional[float] = Field(None, description="Constant b")
    equation_string: Optional[str] = Field(None, description="Equation string like 'x + 4 = 5' or '2x - 6 = 0'")
    
    @validator('equation_string', always=True)
    def validate_input(cls, v, values):
        a = values.get('a')
        b = values.get('b')
        
        # Must provide either (a, b) OR equation_string
        if (a is None or b is None) and v is None:
            raise ValueError('Must provide either (a, b) coefficients or equation_string')
        if (a is not None and b is not None) and v is not None:
            raise ValueError('Cannot provide both coefficients and equation_string')
        
        return v


class LinearEquationOutput(BaseModel):
    """Output model for linear equation"""
    solution: Optional[float]


class QuadraticEquationInput(BaseModel):
    """Input model for quadratic equation: ax² + bx + c = 0"""
    a: Optional[float] = Field(None, description="Coefficient a (x² term)")
    b: Optional[float] = Field(None, description="Coefficient b (x term)")
    c: Optional[float] = Field(None, description="Constant c")
    equation_string: Optional[str] = Field(None, description="Equation string like 'x^2 - 5x + 6 = 0' or '2x^2 + 3x - 2 = 0'")
    
    @validator('equation_string', always=True)
    def validate_input(cls, v, values):
        a = values.get('a')
        b = values.get('b')
        c = values.get('c')
        
        # Must provide either (a, b, c) OR equation_string
        if (a is None or b is None or c is None) and v is None:
            raise ValueError('Must provide either (a, b, c) coefficients or equation_string')
        if (a is not None and b is not None and c is not None) and v is not None:
            raise ValueError('Cannot provide both coefficients and equation_string')
        
        return v


class QuadraticEquationOutput(BaseModel):
    """Output model for quadratic equation"""
    solutions: List[float]


class PolynomialInput(BaseModel):
    """Input model for polynomial evaluation"""
    coefficients: List[float] = Field(..., min_items=1, description="Polynomial coefficients [a0, a1, a2, ...]")
    x: float = Field(..., description="Value of x to evaluate at")


class System2x2Input(BaseModel):
    """Input model for 2x2 system of equations"""
    a1: float = Field(..., description="Coefficient a1 in equation 1")
    b1: float = Field(..., description="Coefficient b1 in equation 1")
    c1: float = Field(..., description="Constant c1 in equation 1")
    a2: float = Field(..., description="Coefficient a2 in equation 2")
    b2: float = Field(..., description="Coefficient b2 in equation 2")
    c2: float = Field(..., description="Constant c2 in equation 2")


class System2x2Output(BaseModel):
    """Output model for 2x2 system"""
    x: Optional[float]
    y: Optional[float]
    has_solution: bool


class PowerInput(BaseModel):
    """Input model for power calculation"""
    base: float = Field(..., description="Base value")
    exponent: float = Field(..., description="Exponent value")


class RootInput(BaseModel):
    """Input model for nth root calculation"""
    number: float = Field(..., description="Number to find root of")
    n: int = Field(..., ge=1, description="Root degree")


class BinomialExpansionInput(BaseModel):
    """Input model for binomial expansion"""
    a: float = Field(..., description=FIRST_TERM_DESC)
    b: float = Field(..., description="Second term")
    n: int = Field(..., ge=0, description="Power")


class FloatListOutput(BaseModel):
    """Output model for list of floats"""
    values: List[float]


class ArithmeticSequenceInput(BaseModel):
    """Input model for arithmetic sequence"""
    first: float = Field(..., description=FIRST_TERM_DESC)
    common_diff: float = Field(..., description="Common difference")
    n: int = Field(..., ge=1, description="Term number or count")


class GeometricSequenceInput(BaseModel):
    """Input model for geometric sequence"""
    first: float = Field(..., description=FIRST_TERM_DESC)
    ratio: float = Field(..., description="Common ratio")
    n: int = Field(..., ge=1, description="Term number or count")


class RatioInput(BaseModel):
    """Input model for ratio simplification"""
    a: float = Field(..., description=FIRST_TERM_DESC)
    b: float = Field(..., ne=0, description="Second term (non-zero)")


class RatioOutput(BaseModel):
    """Output model for ratio"""
    simplified_a: float
    simplified_b: float


# ============================================
# Geometry Tool Models
# ============================================

class RadiusInput(BaseModel):
    """Input model for circle operations"""
    radius: float = Field(..., ge=0, description="Radius of the circle")


class RectangleInput(BaseModel):
    """Input model for rectangle operations"""
    length: float = Field(..., ge=0, description="Length of rectangle")
    width: float = Field(..., ge=0, description="Width of rectangle")


class TriangleBaseHeightInput(BaseModel):
    """Input model for triangle with base and height"""
    base: float = Field(..., ge=0, description="Base of triangle")
    height: float = Field(..., ge=0, description="Height of triangle")


class TriangleThreeSidesInput(BaseModel):
    """Input model for triangle with three sides"""
    a: float = Field(..., gt=0, description="Side a")
    b: float = Field(..., gt=0, description="Side b")
    c: float = Field(..., gt=0, description="Side c")


class CylinderInput(BaseModel):
    """Input model for cylinder operations"""
    radius: float = Field(..., ge=0, description="Radius of cylinder")
    height: float = Field(..., ge=0, description="Height of cylinder")


class CubeInput(BaseModel):
    """Input model for cube operations"""
    side: float = Field(..., ge=0, description="Side length of cube")


class RectangularPrismInput(BaseModel):
    """Input model for rectangular prism"""
    length: float = Field(..., ge=0, description="Length")
    width: float = Field(..., ge=0, description="Width")
    height: float = Field(..., ge=0, description="Height")


class Point2DInput(BaseModel):
    """Input model for 2D points"""
    x1: float = Field(..., description="X coordinate of point 1")
    y1: float = Field(..., description="Y coordinate of point 1")
    x2: float = Field(..., description="X coordinate of point 2")
    y2: float = Field(..., description="Y coordinate of point 2")


class Point3DInput(BaseModel):
    """Input model for 3D points"""
    x1: float = Field(..., description="X coordinate of point 1")
    y1: float = Field(..., description="Y coordinate of point 1")
    z1: float = Field(..., description="Z coordinate of point 1")
    x2: float = Field(..., description="X coordinate of point 2")
    y2: float = Field(..., description="Y coordinate of point 2")
    z2: float = Field(..., description="Z coordinate of point 2")


class PythagoreanInput(BaseModel):
    """Input model for Pythagorean theorem"""
    a: float = Field(..., ge=0, description="First leg")
    b: float = Field(..., ge=0, description="Second leg")


class PythagoreanLegInput(BaseModel):
    """Input model for finding a leg given hypotenuse"""
    known_leg: float = Field(..., ge=0, description="The known leg")
    hypotenuse: float = Field(..., ge=0, description="The hypotenuse")


class ChordInput(BaseModel):
    """Input model for chord length calculation"""
    radius: float = Field(..., ge=0, description="Radius of the circle")
    distance_from_center: float = Field(..., ge=0, description="Distance from center to chord")


class TrapezoidInput(BaseModel):
    """Input model for trapezoid"""
    base1: float = Field(..., ge=0, description="First base")
    base2: float = Field(..., ge=0, description="Second base")
    height: float = Field(..., ge=0, description="Height")


# ============================================
# Statistics Tool Models
# ============================================

class StatNumberListInput(BaseModel):
    """Input model for statistical operations on number lists"""
    numbers: List[float] = Field(..., min_items=1, description=LIST_OF_NUMBERS_DESC)


class StatFloatListOutput(BaseModel):
    """Output model for statistical lists"""
    values: List[float]


class VarianceInput(BaseModel):
    """Input model for variance calculation"""
    numbers: List[float] = Field(..., min_items=1, description=LIST_OF_NUMBERS_DESC)
    sample: bool = Field(default=True, description="Calculate sample variance (True) or population variance (False)")


class PercentileInput(BaseModel):
    """Input model for percentile calculation"""
    numbers: List[float] = Field(..., min_items=1, description=LIST_OF_NUMBERS_DESC)
    percentile: float = Field(..., ge=0, le=100, description="Percentile to calculate (0-100)")


class QuartilesOutput(BaseModel):
    """Output model for quartiles"""
    q1: float
    q2: float
    q3: float


class ZScoreInput(BaseModel):
    """Input model for z-score calculation"""
    value: float = Field(..., description="Value to calculate z-score for")
    mean: float = Field(..., description="Mean of the distribution")
    std_dev: float = Field(..., ne=0, description="Standard deviation (non-zero)")


class CorrelationInput(BaseModel):
    """Input model for correlation calculation"""
    x_values: List[float] = Field(..., min_items=2, description="X values")
    y_values: List[float] = Field(..., min_items=2, description="Y values")
    
    @validator('y_values')
    def lists_must_be_same_length(cls, v, values):
        if 'x_values' in values and len(v) != len(values['x_values']):
            raise ValueError('x_values and y_values must have the same length')
        return v


class RegressionOutput(BaseModel):
    """Output model for linear regression"""
    slope: float
    intercept: float


class ProbabilityUnionInput(BaseModel):
    """Input model for probability union"""
    p_a: float = Field(..., ge=0, le=1, description="P(A)")
    p_b: float = Field(..., ge=0, le=1, description="P(B)")
    p_both: float = Field(..., ge=0, le=1, description="P(A ∩ B)")


class ProbabilityInput(BaseModel):
    """Input model for probability operations"""
    p: float = Field(..., ge=0, le=1, description="Probability value")

