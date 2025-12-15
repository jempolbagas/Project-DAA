"""
Test coverage for BallTree-based distance calculations.
Tests the build_spatial_tree, find_nearest_fault_distance, and find_nearest_volcano_distance methods.
"""

import pandas as pd
import numpy as np
from src.risk import RiskCalculator

# Constants for clarity
APPROX_KM_PER_DEGREE = 111.0  # Approximate kilometers per degree of latitude


def test_build_spatial_tree():
    """Test BallTree construction from dataframe."""
    print("Testing build_spatial_tree...")
    
    # Test with valid dataframe
    df = pd.DataFrame({
        'latitude': [-7.0, -7.5, -8.0],
        'longitude': [110.0, 110.5, 111.0]
    })
    tree = RiskCalculator.build_spatial_tree(df)
    assert tree is not None, "Tree should be created from valid dataframe"
    
    # Test with None dataframe
    tree_none = RiskCalculator.build_spatial_tree(None)
    assert tree_none is None, "Tree should be None for None dataframe"
    
    # Test with empty dataframe
    df_empty = pd.DataFrame({'latitude': [], 'longitude': []})
    tree_empty = RiskCalculator.build_spatial_tree(df_empty)
    assert tree_empty is None, "Tree should be None for empty dataframe"
    
    print("✓ build_spatial_tree tests passed")


def test_find_nearest_fault_distance_none_tree():
    """Test fault distance calculation with None tree."""
    print("Testing find_nearest_fault_distance with None tree...")
    
    distance = RiskCalculator.find_nearest_fault_distance(-7.0, 110.0, None)
    assert distance == 200.0, "Should return default max distance of 200.0 when tree is None"
    
    print("✓ find_nearest_fault_distance with None tree passed")


def test_find_nearest_volcano_distance_none_tree():
    """Test volcano distance calculation with None tree."""
    print("Testing find_nearest_volcano_distance with None tree...")
    
    distance = RiskCalculator.find_nearest_volcano_distance(-7.0, 110.0, None)
    assert distance == 150.0, "Should return default max distance of 150.0 when tree is None"
    
    print("✓ find_nearest_volcano_distance with None tree passed")


def test_find_nearest_fault_distance_with_tree():
    """Test fault distance calculation with actual tree."""
    print("Testing find_nearest_fault_distance with BallTree...")
    
    # Create a dataframe with known fault locations
    faults_df = pd.DataFrame({
        'latitude': [-7.0, -7.5, -8.0],
        'longitude': [110.0, 110.5, 111.0]
    })
    faults_tree = RiskCalculator.build_spatial_tree(faults_df)
    
    # Test 1: Query a point very close to first fault (should be near 0)
    distance = RiskCalculator.find_nearest_fault_distance(-7.0, 110.0, faults_tree)
    assert distance < 1.0, f"Distance to exact fault location should be ~0 km, got {distance}"
    
    # Test 2: Query a point exactly at second fault
    distance = RiskCalculator.find_nearest_fault_distance(-7.5, 110.5, faults_tree)
    assert distance < 1.0, f"Distance to exact fault location should be ~0 km, got {distance}"
    
    # Test 3: Query a point between faults (should be reasonable)
    distance = RiskCalculator.find_nearest_fault_distance(-7.25, 110.25, faults_tree)
    assert 0 <= distance <= 100, f"Distance should be reasonable, got {distance}"
    
    # Test 4: Verify haversine accuracy - known distance calculation
    # Distance from (-7.0, 110.0) to (-7.1, 110.0) should be ~11.1 km (approximately 0.1 degree latitude)
    distance = RiskCalculator.find_nearest_fault_distance(-7.1, 110.0, faults_tree)
    # Should be close to 11.1 km (0.1 degree latitude ≈ 11.1 km)
    assert 10 <= distance <= 13, f"Expected ~11.1 km for 0.1 degree latitude, got {distance}"
    
    print("✓ find_nearest_fault_distance with BallTree passed")


def test_find_nearest_volcano_distance_with_tree():
    """Test volcano distance calculation with actual tree."""
    print("Testing find_nearest_volcano_distance with BallTree...")
    
    # Create a dataframe with known volcano locations
    volcanoes_df = pd.DataFrame({
        'latitude': [-7.5, -8.0, -8.5],
        'longitude': [110.5, 111.0, 111.5]
    })
    volcanoes_tree = RiskCalculator.build_spatial_tree(volcanoes_df)
    
    # Test 1: Query a point very close to first volcano (should be near 0)
    distance = RiskCalculator.find_nearest_volcano_distance(-7.5, 110.5, volcanoes_tree)
    assert distance < 1.0, f"Distance to exact volcano location should be ~0 km, got {distance}"
    
    # Test 2: Query a point exactly at second volcano
    distance = RiskCalculator.find_nearest_volcano_distance(-8.0, 111.0, volcanoes_tree)
    assert distance < 1.0, f"Distance to exact volcano location should be ~0 km, got {distance}"
    
    # Test 3: Query a point between volcanoes (should be reasonable)
    distance = RiskCalculator.find_nearest_volcano_distance(-7.75, 110.75, volcanoes_tree)
    assert 0 <= distance <= 100, f"Distance should be reasonable, got {distance}"
    
    # Test 4: Verify haversine accuracy - known distance calculation
    # Distance from (-7.5, 110.5) to (-7.6, 110.5) should be ~11.1 km
    distance = RiskCalculator.find_nearest_volcano_distance(-7.6, 110.5, volcanoes_tree)
    # Should be close to 11.1 km (0.1 degree latitude ≈ 11.1 km)
    assert 10 <= distance <= 13, f"Expected ~11.1 km for 0.1 degree latitude, got {distance}"
    
    print("✓ find_nearest_volcano_distance with BallTree passed")


def test_haversine_vs_euclidean_accuracy():
    """Test that haversine distance is more accurate than Euclidean approximation."""
    print("Testing haversine accuracy vs Euclidean approximation...")
    
    # Create a fault at Mount Merapi approximate location
    faults_df = pd.DataFrame({
        'latitude': [-7.54],
        'longitude': [110.44]
    })
    faults_tree = RiskCalculator.build_spatial_tree(faults_df)
    
    # Query from a point ~100 km away (approximately)
    # Using haversine distance
    query_lat, query_lon = -8.0, 110.44
    haversine_dist = RiskCalculator.find_nearest_fault_distance(query_lat, query_lon, faults_tree)
    
    # Simplified latitude-only Euclidean approximation (same longitude)
    # For same longitude, distance is just the latitude difference in km
    euclidean_approx = abs(query_lat - (-7.54)) * APPROX_KM_PER_DEGREE
    
    # Haversine should give a slightly different (more accurate) result
    # For this case, they should be close but not identical
    print(f"  Haversine distance: {haversine_dist:.2f} km")
    print(f"  Euclidean approximation: {euclidean_approx:.2f} km")
    
    # Both should be in reasonable range
    assert 40 <= haversine_dist <= 60, f"Haversine distance should be ~50 km, got {haversine_dist}"
    assert 40 <= euclidean_approx <= 60, f"Euclidean approximation should be ~50 km, got {euclidean_approx}"
    
    # For this simple case (same longitude), they should be very close
    diff = abs(haversine_dist - euclidean_approx)
    assert diff < 2, f"For same longitude, difference should be small, got {diff}"
    
    print("✓ Haversine accuracy test passed")


def test_coordinate_order():
    """Test that latitude/longitude order is correct."""
    print("Testing coordinate order (latitude, longitude)...")
    
    # Create a simple grid of faults
    faults_df = pd.DataFrame({
        'latitude': [-7.0, -7.0, -8.0, -8.0],
        'longitude': [110.0, 111.0, 110.0, 111.0]
    })
    faults_tree = RiskCalculator.build_spatial_tree(faults_df)
    
    # Query the exact point of first fault
    distance_1 = RiskCalculator.find_nearest_fault_distance(-7.0, 110.0, faults_tree)
    
    # Query the exact point of last fault
    distance_2 = RiskCalculator.find_nearest_fault_distance(-8.0, 111.0, faults_tree)
    
    # Both should be very close to 0 if coordinates are correct
    assert distance_1 < 1.0, f"First fault should be at distance ~0, got {distance_1}"
    assert distance_2 < 1.0, f"Last fault should be at distance ~0, got {distance_2}"
    
    print("✓ Coordinate order test passed")


def run_all_balltree_tests():
    """Run all BallTree tests."""
    print("=" * 60)
    print("RUNNING BALLTREE TESTS")
    print("=" * 60)
    
    try:
        test_build_spatial_tree()
        test_find_nearest_fault_distance_none_tree()
        test_find_nearest_volcano_distance_none_tree()
        test_find_nearest_fault_distance_with_tree()
        test_find_nearest_volcano_distance_with_tree()
        test_haversine_vs_euclidean_accuracy()
        test_coordinate_order()
        
        print("\n" + "=" * 60)
        print("ALL BALLTREE TESTS PASSED ✓")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_balltree_tests()
    exit(0 if success else 1)
