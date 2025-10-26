"""
Geometry Tools
Tools for calculating areas, perimeters, volumes, and other geometric properties
"""
import logging
import math

# Error message constants
ERR_RADIUS_NEGATIVE = "Radius cannot be negative"
ERR_DIMENSIONS_NEGATIVE = "Dimensions cannot be negative"

def log_function(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper


@log_function
def calculate_circle_area(radius: float) -> float:
    """
    Calculate area of a circle: π * r²
    """
    if radius < 0:
        raise ValueError(ERR_RADIUS_NEGATIVE)
    return math.pi * radius ** 2


@log_function
def calculate_circle_circumference(radius: float) -> float:
    """
    Calculate circumference of a circle: 2 * π * r
    """
    if radius < 0:
        raise ValueError(ERR_RADIUS_NEGATIVE)
    return 2 * math.pi * radius


@log_function
def calculate_rectangle_area(length: float, width: float) -> float:
    """
    Calculate area of a rectangle: length * width
    """
    if length < 0 or width < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return length * width


@log_function
def calculate_rectangle_perimeter(length: float, width: float) -> float:
    """
    Calculate perimeter of a rectangle: 2 * (length + width)
    """
    if length < 0 or width < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return 2 * (length + width)


@log_function
def calculate_triangle_area(base: float, height: float) -> float:
    """
    Calculate area of a triangle: (base * height) / 2
    """
    if base < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return (base * height) / 2


@log_function
def calculate_triangle_area_heron(a: float, b: float, c: float) -> float:
    """
    Calculate area of a triangle using Heron's formula.
    Given three sides a, b, c.
    """
    if a <= 0 or b <= 0 or c <= 0:
        raise ValueError("Side lengths must be positive")
    
    # Check triangle inequality
    if a + b <= c or b + c <= a or a + c <= b:
        raise ValueError("Invalid triangle: sides don't satisfy triangle inequality")
    
    s = (a + b + c) / 2  # semi-perimeter
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    return area


@log_function
def calculate_sphere_volume(radius: float) -> float:
    """
    Calculate volume of a sphere: (4/3) * π * r³
    """
    if radius < 0:
        raise ValueError(ERR_RADIUS_NEGATIVE)
    return (4/3) * math.pi * radius ** 3


@log_function
def calculate_sphere_surface_area(radius: float) -> float:
    """
    Calculate surface area of a sphere: 4 * π * r²
    """
    if radius < 0:
        raise ValueError(ERR_RADIUS_NEGATIVE)
    return 4 * math.pi * radius ** 2


@log_function
def calculate_cylinder_volume(radius: float, height: float) -> float:
    """
    Calculate volume of a cylinder: π * r² * h
    """
    if radius < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return math.pi * radius ** 2 * height


@log_function
def calculate_cylinder_surface_area(radius: float, height: float) -> float:
    """
    Calculate surface area of a cylinder: 2πr(r + h)
    """
    if radius < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return 2 * math.pi * radius * (radius + height)


@log_function
def calculate_cone_volume(radius: float, height: float) -> float:
    """
    Calculate volume of a cone: (1/3) * π * r² * h
    """
    if radius < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return (1/3) * math.pi * radius ** 2 * height


@log_function
def calculate_cube_volume(side: float) -> float:
    """
    Calculate volume of a cube: side³
    """
    if side < 0:
        raise ValueError("Side length cannot be negative")
    return side ** 3


@log_function
def calculate_cube_surface_area(side: float) -> float:
    """
    Calculate surface area of a cube: 6 * side²
    """
    if side < 0:
        raise ValueError("Side length cannot be negative")
    return 6 * side ** 2


@log_function
def calculate_rectangular_prism_volume(length: float, width: float, height: float) -> float:
    """
    Calculate volume of a rectangular prism: length * width * height
    """
    if length < 0 or width < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return length * width * height


@log_function
def calculate_distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate distance between two points in 2D: √((x2-x1)² + (y2-y1)²)
    """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


@log_function
def calculate_distance_3d(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
    """
    Calculate distance between two points in 3D: √((x2-x1)² + (y2-y1)² + (z2-z1)²)
    """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)


@log_function
def calculate_pythagorean_theorem(a: float, b: float) -> float:
    """
    Calculate hypotenuse using Pythagorean theorem: c = √(a² + b²)
    """
    if a < 0 or b < 0:
        raise ValueError("Side lengths cannot be negative")
    return math.sqrt(a**2 + b**2)


@log_function
def calculate_pythagorean_leg(known_leg: float, hypotenuse: float) -> float:
    """
    Calculate unknown leg using Pythagorean theorem: b = √(c² - a²)
    Given one leg and the hypotenuse, find the other leg.
    
    Args:
        known_leg: The known leg length
        hypotenuse: The hypotenuse length
        
    Returns:
        The unknown leg length
    """
    if known_leg < 0 or hypotenuse < 0:
        raise ValueError("Side lengths cannot be negative")
    if known_leg >= hypotenuse:
        raise ValueError("Leg cannot be greater than or equal to hypotenuse")
    
    return math.sqrt(hypotenuse**2 - known_leg**2)


@log_function
def calculate_chord_length(radius: float, distance_from_center: float) -> float:
    """
    Calculate the length of a chord in a circle.
    
    Given a circle with radius r and a chord at distance d from the center,
    the chord length = 2 * √(r² - d²)
    
    Args:
        radius: Radius of the circle
        distance_from_center: Perpendicular distance from center to chord
        
    Returns:
        The length of the chord
    """
    if radius < 0 or distance_from_center < 0:
        raise ValueError("Radius and distance cannot be negative")
    if distance_from_center > radius:
        raise ValueError("Distance from center cannot exceed radius")
    
    # Using Pythagorean theorem: half_chord = √(r² - d²)
    half_chord = math.sqrt(radius**2 - distance_from_center**2)
    return 2 * half_chord


@log_function
def calculate_trapezoid_area(base1: float, base2: float, height: float) -> float:
    """
    Calculate area of a trapezoid: ((base1 + base2) / 2) * height
    """
    if base1 < 0 or base2 < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return ((base1 + base2) / 2) * height


@log_function
def calculate_parallelogram_area(base: float, height: float) -> float:
    """
    Calculate area of a parallelogram: base * height
    """
    if base < 0 or height < 0:
        raise ValueError(ERR_DIMENSIONS_NEGATIVE)
    return base * height

