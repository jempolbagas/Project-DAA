"""
Earthquake Risk Zoning Package
"""

from .quadtree import QuadTree, Point, Rectangle
from .risk import RiskCalculator

__all__ = ['QuadTree', 'Point', 'Rectangle', 'RiskCalculator']
