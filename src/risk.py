
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
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree


class RiskCalculator:
    """Calculate earthquake risk scores based on multiple parameters."""
    
    # Earth's mean radius in kilometers (for haversine distance calculations)
    EARTH_RADIUS_KM = 6371.0

    # Risk weights for each parameter (total = 1.0)
    WEIGHTS = {
        'magnitude': 0.20,      # Earthquake magnitude (Richter scale)
        'depth': 0.10,          # Depth of earthquake (km)
        'intensity': 0.15,      # Intensity (MMI scale)
        'frequency': 0.13,      # Historical frequency in area
        'fault_distance': 0.14, # Distance to nearest fault line (km)
        'volcano_distance': 0.10, # Distance to nearest volcano (km)
        'plate_zone': 0.08,     # Proximity to plate boundaries
        'population_density': 0.10  # Population density (people per km²)
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
    
    @staticmethod
    def normalize_population_density(density):
        """
        Normalize population density to 0-1 scale.
        Higher density = higher risk (more people at stake).
        """
        # Higher density = higher risk
        # Assume max density of 100,000 people/km² for normalization
        return min(density / 100000.0, 1.0)
    

    @classmethod
    def calculate_risk_score(cls, magnitude, depth, intensity, frequency,
                            fault_distance, volcano_distance, plate_zone, 
                            population_density=None):
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
            population_density: Population density (people per km²)
            
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
        
        # Normalize population density if provided
        if population_density is not None:
            norm_population = cls.normalize_population_density(population_density)
        else:
            norm_population = 0.0  # Default to no population risk if not provided
        
        # Calculate weighted score
        risk_score = (
            cls.WEIGHTS['magnitude'] * norm_magnitude +
            cls.WEIGHTS['depth'] * norm_depth +
            cls.WEIGHTS['intensity'] * norm_intensity +
            cls.WEIGHTS['frequency'] * norm_frequency +
            cls.WEIGHTS['fault_distance'] * norm_fault +
            cls.WEIGHTS['volcano_distance'] * norm_volcano +
            cls.WEIGHTS['plate_zone'] * norm_plate +
            cls.WEIGHTS['population_density'] * norm_population
        )
        
        # Scale to 0-100
        return risk_score * 100
    

    @staticmethod
    def load_jawa_regions_data(filepath):
        """
        Load Jawa regions data from CSV file.
        
        Args:
            filepath: Path to jawa_regions.csv file
            
        Returns:
            DataFrame with regional data
        """
        try:
            df = pd.read_csv(filepath)
            print(f"Loaded {len(df)} regions from {filepath}")
            return df
        except Exception as e:
            print(f"Error loading regions data: {e}")
            return None
    
    @classmethod
    def calculate_regional_risk_aggregation(cls, earthquake_df, regions_df, 
                                           aggregation_type='mean'):
        """
        Calculate regional risk aggregation by region.
        
        Args:
            earthquake_df: DataFrame with earthquake data
            regions_df: DataFrame with regions data
            aggregation_type: 'mean', 'max', 'min', 'count'
            
        Returns:
            DataFrame with regional risk statistics
        """
        if regions_df is None:
            return earthquake_df
        
        # Merge earthquake data with regions based on region_name
        merged_df = earthquake_df.merge(
            regions_df[['region_name', 'province', 'type']], 
            on='region_name', 
            how='left'
        )
        
        # Calculate regional aggregation
        if aggregation_type == 'mean':
            regional_stats = merged_df.groupby('region_name').agg({
                'risk_score': 'mean',
                'magnitude': 'mean',
                'depth': 'mean',
                'latitude': 'mean',
                'longitude': 'mean',
                'plate_zone': 'mean',
                'province': 'first',
                'type': 'first'
            }).reset_index()
        elif aggregation_type == 'max':
            regional_stats = merged_df.groupby('region_name').agg({
                'risk_score': 'max',
                'magnitude': 'max',
                'depth': 'min',  # Shallowest depth = highest risk
                'latitude': 'mean',
                'longitude': 'mean',
                'plate_zone': 'max',
                'province': 'first',
                'type': 'first'
            }).reset_index()
        elif aggregation_type == 'count':
            regional_stats = merged_df.groupby('region_name').agg({
                'risk_score': 'count',
                'province': 'first',
                'type': 'first'
            }).reset_index()
            regional_stats.rename(columns={'risk_score': 'earthquake_count'}, inplace=True)
        
        # Add risk level
        regional_stats['risk_level'] = regional_stats['risk_score'].apply(cls.get_risk_level)
        
        return regional_stats
    
    @classmethod
    def calculate_provincial_risk_analysis(cls, earthquake_df, regions_df):
        """
        Calculate provincial-level risk analysis for Jawa regions.
        
        Args:
            earthquake_df: DataFrame with earthquake data
            regions_df: DataFrame with regions data
            
        Returns:
            DataFrame with provincial statistics
        """
        if regions_df is None:
            return None
        
        # Merge data
        merged_df = earthquake_df.merge(
            regions_df[['region_name', 'province', 'type', 'population_2020']], 
            on='region_name', 
            how='left'
        )
        
        # Calculate provincial statistics
        provincial_stats = merged_df.groupby('province').agg({
            'risk_score': ['mean', 'max', 'min', 'std'],
            'magnitude': ['mean', 'max'],
            'depth': ['mean', 'min'],
            'frequency': 'mean',
            'population_2020': 'sum',
            'region_name': 'count'  # Number of regions with earthquakes
        }).reset_index()
        
        # Flatten column names
        provincial_stats.columns = [
            'province', 'avg_risk_score', 'max_risk_score', 'min_risk_score', 'risk_std',
            'avg_magnitude', 'max_magnitude', 'avg_depth', 'min_depth',
            'avg_frequency', 'total_population', 'regions_affected'
        ]
        
        # Add risk level classification
        provincial_stats['risk_level'] = provincial_stats['avg_risk_score'].apply(cls.get_risk_level)
        
        # Calculate risk per capita (normalize by population)
        provincial_stats['risk_per_100k'] = (
            provincial_stats['avg_risk_score'] * provincial_stats['regions_affected'] / 
            provincial_stats['total_population'] * 100000
        )
        
        return provincial_stats
    
    @classmethod
    def get_high_risk_regions(cls, regional_stats, top_n=10):
        """
        Get top N highest risk regions.
        
        Args:
            regional_stats: DataFrame with regional statistics
            top_n: Number of top regions to return
            
        Returns:
            DataFrame with top risk regions
        """
        if regional_stats is None:
            return None
        
        # Sort by risk score and return top N
        top_regions = regional_stats.nlargest(top_n, 'risk_score')
        
        return top_regions
    
    @classmethod
    def get_regional_comparison(cls, earthquake_df, regions_df):
        """
        Create comprehensive regional comparison analysis.
        
        Args:
            earthquake_df: DataFrame with earthquake data
            regions_df: DataFrame with regions data
            
        Returns:
            Dictionary with various regional comparisons
        """
        if regions_df is None:
            return None
        
        # Regional statistics
        regional_stats = cls.calculate_regional_risk_aggregation(earthquake_df, regions_df)
        
        # Provincial statistics
        provincial_stats = cls.calculate_provincial_risk_analysis(earthquake_df, regions_df)
        
        # High risk regions
        high_risk_regions = cls.get_high_risk_regions(regional_stats, top_n=10)
        
        # Province ranking
        if provincial_stats is not None:
            province_ranking = provincial_stats.sort_values('avg_risk_score', ascending=False)
        else:
            province_ranking = None
        
        # Risk level distribution by province
        risk_by_province = cls.get_risk_distribution_by_province(earthquake_df, regions_df)
        
        return {
            'regional_stats': regional_stats,
            'provincial_stats': provincial_stats,
            'high_risk_regions': high_risk_regions,
            'province_ranking': province_ranking,
            'risk_by_province': risk_by_province
        }
    
    @classmethod
    def get_risk_distribution_by_province(cls, earthquake_df, regions_df):
        """
        Get risk level distribution by province.
        
        Args:
            earthquake_df: DataFrame with earthquake data
            regions_df: DataFrame with regions data
            
        Returns:
            DataFrame with risk distribution by province
        """
        if regions_df is None:
            return None
        
        # Merge data
        merged_df = earthquake_df.merge(
            regions_df[['region_name', 'province', 'type']], 
            on='region_name', 
            how='left'
        )
        
        # Create crosstab
        risk_distribution = pd.crosstab(
            merged_df['province'], 
            merged_df['risk_level'], 
            margins=True
        )
        
        return risk_distribution
    
    @classmethod
    def generate_regional_summary(cls, regional_analysis):
        """
        Generate comprehensive regional summary report.
        
        Args:
            regional_analysis: Dictionary from get_regional_comparison
            
        Returns:
            Formatted string summary
        """
        if not regional_analysis:
            return "No regional analysis available."
        
        summary = []
        summary.append("="*60)
        summary.append("REGIONAL RISK ANALYSIS SUMMARY")
        summary.append("="*60)
        
        # High risk regions
        if regional_analysis['high_risk_regions'] is not None:
            summary.append("\nTOP 10 HIGHEST RISK REGIONS:")
            summary.append("-" * 40)
            top_regions = regional_analysis['high_risk_regions']
            for idx, row in top_regions.iterrows():
                summary.append(
                    f"{row['region_name']} ({row['province']}): "
                    f"Risk Score {row['risk_score']:.2f} ({row['risk_level']})"
                )
        
        # Provincial ranking
        if regional_analysis['province_ranking'] is not None:
            summary.append("\nPROVINCIAL RISK RANKING:")
            summary.append("-" * 30)
            provinces = regional_analysis['province_ranking']
            for idx, row in provinces.iterrows():
                summary.append(
                    f"{idx+1}. {row['province']}: "
                    f"Avg Risk {row['avg_risk_score']:.2f} ({row['risk_level']}), "
                    f"{row['regions_affected']} regions affected"
                )
        
        # Risk distribution
        if regional_analysis['risk_by_province'] is not None:
            summary.append("\nRISK DISTRIBUTION BY PROVINCE:")
            summary.append("-" * 35)
            summary.append(str(regional_analysis['risk_by_province']))
        
        return "\n".join(summary)
    
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
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees) using Haversine formula.
        Returns distance in kilometers.
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    @staticmethod
    def build_spatial_tree(dataframe):
        """
        Build a BallTree spatial index from a dataframe containing 'latitude' and 'longitude'.
        
        Uses BallTree with haversine metric for accurate geodesic distance calculations.
        The haversine metric accounts for Earth's curvature and provides accurate distances
        between geographic coordinates.
        
        Args:
            dataframe: pandas DataFrame with 'latitude' and 'longitude' columns
            
        Returns:
            sklearn.neighbors.BallTree object, or None if dataframe is empty/None
            
        Example:
            >>> faults_df = pd.DataFrame({'latitude': [-7.0, -7.5], 'longitude': [110.0, 110.5]})
            >>> tree = RiskCalculator.build_spatial_tree(faults_df)
            >>> # Use tree.query() to find nearest points
        """
        if dataframe is None or dataframe.empty:
            return None
        # Extract coordinates and convert to radians for haversine metric
        # BallTree expects (lat, lon) in radians for haversine distance
        coordinates = dataframe[['latitude', 'longitude']].values
        coordinates_rad = np.radians(coordinates)
        return BallTree(coordinates_rad, metric='haversine')

    @classmethod
    def find_nearest_fault_distance(cls, lat, lon, faults_tree):
        """
        Find distance to nearest fault line using BallTree spatial query with haversine metric.
        
        This method uses the haversine formula via BallTree to calculate accurate geodesic
        distances on Earth's surface, accounting for the planet's curvature. This is more
        accurate than simple Euclidean approximation, especially for longer distances.
        
        Args:
            lat (float): Latitude of the earthquake location (degrees, -90 to 90)
            lon (float): Longitude of the earthquake location (degrees, -180 to 180)
            faults_tree: Pre-built sklearn.neighbors.BallTree object with haversine metric
            
        Returns:
            float: Distance in kilometers to nearest fault line
            
        Example:
            >>> distance = RiskCalculator.find_nearest_fault_distance(-7.0, 110.0, faults_tree)
            >>> print(f"Distance to fault: {distance:.2f} km")
        """
        if faults_tree is None:
            return 200.0  # Default max distance
        
        # Convert query point to radians for haversine metric
        query_point = np.radians([[lat, lon]])
        
        # BallTree.query returns (distances, indices)
        # Distance is in radians; convert to kilometers using Earth's radius
        dist_rad, _ = faults_tree.query(query_point, k=1)
        dist_km = dist_rad[0][0] * cls.EARTH_RADIUS_KM
        
        return dist_km
    
    @classmethod
    def find_nearest_volcano_distance(cls, lat, lon, volcanoes_tree):
        """
        Find distance to nearest volcano using BallTree spatial query with haversine metric.
        
        This method uses the haversine formula via BallTree to calculate accurate geodesic
        distances on Earth's surface, accounting for the planet's curvature. This is more
        accurate than simple Euclidean approximation, especially for longer distances.
        
        Args:
            lat (float): Latitude of the earthquake location (degrees, -90 to 90)
            lon (float): Longitude of the earthquake location (degrees, -180 to 180)
            volcanoes_tree: Pre-built sklearn.neighbors.BallTree object with haversine metric
            
        Returns:
            float: Distance in kilometers to nearest volcano
            
        Example:
            >>> distance = RiskCalculator.find_nearest_volcano_distance(-7.0, 110.0, volcanoes_tree)
            >>> print(f"Distance to volcano: {distance:.2f} km")
        """
        if volcanoes_tree is None:
            return 150.0  # Default max distance
        
        # Convert query point to radians for haversine metric
        query_point = np.radians([[lat, lon]])
        
        # BallTree.query returns (distances, indices)
        # Distance is in radians; convert to kilometers using Earth's radius
        dist_rad, _ = volcanoes_tree.query(query_point, k=1)
        dist_km = dist_rad[0][0] * cls.EARTH_RADIUS_KM
        
        return dist_km
    
    @classmethod
    def calculate_enhanced_risk_score(cls, magnitude, depth, intensity, frequency,
                                    lat, lon, faults_tree=None, volcanoes_tree=None,
                                    plate_zone=1):
        """
        Calculate comprehensive risk score (0-100) with geological data integration.
        
        This implements the blueprint specification with real geological features.
        
        Args:
            magnitude: Earthquake magnitude (Richter scale)
            depth: Depth in km
            intensity: MMI intensity (1-12)
            frequency: Events per year
            lat: Latitude for distance calculations
            lon: Longitude for distance calculations
            faults_tree: BallTree object for faults (with haversine metric)
            volcanoes_tree: BallTree object for volcanoes (with haversine metric)
            plate_zone: Zone type (0=stable, 1=boundary, 2=subduction)
            
        Returns:
            Risk score (0-100)
        """
        # Calculate actual distances using BallTree with haversine metric
        fault_distance = cls.find_nearest_fault_distance(lat, lon, faults_tree)
        volcano_distance = cls.find_nearest_volcano_distance(lat, lon, volcanoes_tree)
        
        # Normalize all parameters according to blueprint
        norm_magnitude = cls.normalize_magnitude(magnitude)
        norm_depth = cls.normalize_depth(depth)
        norm_intensity = cls.normalize_intensity(intensity)
        norm_frequency = cls.normalize_frequency(frequency)
        norm_fault = cls.normalize_fault_distance(fault_distance)
        norm_volcano = cls.normalize_volcano_distance(volcano_distance)
        norm_plate = cls.normalize_plate_zone(plate_zone)
        
        # Calculate weighted score according to blueprint formula
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
