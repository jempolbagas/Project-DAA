"""
Risk calculation module for earthquake risk assessment.
Calculates risk scores based on 7 parameters:
1. Magnitude
2. Depth
3. Intensity
4. Frequency
5. Distance to Faults
6. Distance to Volcanoes
7. Plate Zones
"""

import math


class RiskCalculator:
    """Calculate earthquake risk scores based on multiple parameters."""
    
    # Risk weights for each parameter (total = 1.0)
    WEIGHTS = {
        'magnitude': 0.25,      # Earthquake magnitude (Richter scale)
        'depth': 0.10,          # Depth of earthquake (km)
        'intensity': 0.20,      # Intensity (MMI scale)
        'frequency': 0.15,      # Historical frequency in area
        'fault_distance': 0.15, # Distance to nearest fault line (km)
        'volcano_distance': 0.10, # Distance to nearest volcano (km)
        'plate_zone': 0.05      # Proximity to plate boundaries
    }
    
    @staticmethod
    def normalize_magnitude(magnitude):
        """
        Normalize magnitude to 0-1 scale.
        Richter scale typically ranges 0-9+, high values = high risk.
        """
        # Scale: 0-9, normalize to 0-1
        return min(magnitude / 9.0, 1.0)
    
    @staticmethod
    def normalize_depth(depth):
        """
        Normalize depth to 0-1 scale.
        Shallow earthquakes (< 70km) are more dangerous.
        """
        # Shallow = high risk, deep = low risk
        # Inverse relationship: shallow (0-10km) = 1.0, deep (>300km) = 0.0
        if depth <= 0:
            return 1.0
        normalized = max(0, 1.0 - (depth / 300.0))
        return normalized
    
    @staticmethod
    def normalize_intensity(intensity):
        """
        Normalize intensity to 0-1 scale.
        Modified Mercalli Intensity (MMI) scale: I-XII
        """
        # Scale: 1-12, normalize to 0-1
        if intensity < 1:
            return 0.0
        return min((intensity - 1) / 11.0, 1.0)
    
    @staticmethod
    def normalize_frequency(frequency):
        """
        Normalize frequency to 0-1 scale.
        Number of earthquakes in area per year.
        """
        # Higher frequency = higher risk
        # Assume max meaningful frequency is 50 events/year
        return min(frequency / 50.0, 1.0)
    
    @staticmethod
    def normalize_fault_distance(distance):
        """
        Normalize distance to fault line to 0-1 scale.
        Closer to fault = higher risk.
        """
        # Inverse relationship: near (0-10km) = 1.0, far (>200km) = 0.0
        if distance <= 0:
            return 1.0
        normalized = max(0, 1.0 - (distance / 200.0))
        return normalized
    
    @staticmethod
    def normalize_volcano_distance(distance):
        """
        Normalize distance to volcano to 0-1 scale.
        Closer to volcano = higher risk (volcanic earthquakes).
        """
        # Inverse relationship: near (0-10km) = 1.0, far (>150km) = 0.0
        if distance <= 0:
            return 1.0
        normalized = max(0, 1.0 - (distance / 150.0))
        return normalized
    
    @staticmethod
    def normalize_plate_zone(zone_type):
        """
        Normalize plate zone type to 0-1 scale.
        Zone types: 0=stable, 1=boundary, 2=subduction
        """
        zone_risks = {
            0: 0.1,  # Stable continental interior
            1: 0.6,  # Plate boundary
            2: 1.0   # Subduction zone (highest risk)
        }
        return zone_risks.get(zone_type, 0.5)
    
    @classmethod
    def calculate_risk_score(cls, magnitude, depth, intensity, frequency,
                            fault_distance, volcano_distance, plate_zone):
        """
        Calculate comprehensive risk score (0-100).
        
        Args:
            magnitude: Earthquake magnitude (Richter scale)
            depth: Depth in km
            intensity: MMI intensity (1-12)
            frequency: Events per year
            fault_distance: Distance to nearest fault (km)
            volcano_distance: Distance to nearest volcano (km)
            plate_zone: Zone type (0=stable, 1=boundary, 2=subduction)
            
        Returns:
            Risk score (0-100)
        """
        # Normalize all parameters
        norm_magnitude = cls.normalize_magnitude(magnitude)
        norm_depth = cls.normalize_depth(depth)
        norm_intensity = cls.normalize_intensity(intensity)
        norm_frequency = cls.normalize_frequency(frequency)
        norm_fault = cls.normalize_fault_distance(fault_distance)
        norm_volcano = cls.normalize_volcano_distance(volcano_distance)
        norm_plate = cls.normalize_plate_zone(plate_zone)
        
        # Calculate weighted score
        risk_score = (
            cls.WEIGHTS['magnitude'] * norm_magnitude +
            cls.WEIGHTS['depth'] * norm_depth +
            cls.WEIGHTS['intensity'] * norm_intensity +
            cls.WEIGHTS['frequency'] * norm_frequency +
            cls.WEIGHTS['fault_distance'] * norm_fault +
            cls.WEIGHTS['volcano_distance'] * norm_volcano +
            cls.WEIGHTS['plate_zone'] * norm_plate
        )
        
        # Scale to 0-100
        return risk_score * 100
    
    @staticmethod
    def get_risk_level(score):
        """
        Get risk level category based on score.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk level string
        """
        if score >= 80:
            return "Very High"
        elif score >= 60:
            return "High"
        elif score >= 40:
            return "Moderate"
        elif score >= 20:
            return "Low"
        else:
            return "Very Low"
    
    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
