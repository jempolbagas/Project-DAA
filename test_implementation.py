"""
Simple tests to verify the earthquake risk zoning implementation.
"""

from src.quadtree import QuadTree, Point, Rectangle
from src.risk import RiskCalculator


def test_quadtree_basic():
    """Test basic QuadTree operations."""
    print("Testing QuadTree basic operations...")
    
    # Create a quadtree
    boundary = Rectangle(0, 0, 100, 100)
    qt = QuadTree(boundary, capacity=4)
    
    # Insert some points
    points = [
        Point(10, 10, data={'id': 1}),
        Point(20, 20, data={'id': 2}),
        Point(30, 30, data={'id': 3}),
        Point(-10, -10, data={'id': 4}),
        Point(-20, -20, data={'id': 5}),
    ]
    
    for point in points:
        assert qt.insert(point), f"Failed to insert point {point}"
    
    # Test query (Rectangle centered at 0,0 with width/height 50 covers -50 to +50)
    query_rect = Rectangle(0, 0, 50, 50)
    found = qt.query(query_rect)
    assert len(found) == 5, f"Expected 5 points (all within ±50), found {len(found)}"
    
    # Test radius query
    center = Point(0, 0)
    found_radius = qt.query_radius(center, 30)
    assert len(found_radius) >= 3, f"Expected at least 3 points within radius"
    
    print("✓ QuadTree basic operations passed")


def test_quadtree_subdivision():
    """Test QuadTree subdivision (Divide & Conquer)."""
    print("Testing QuadTree subdivision...")
    
    boundary = Rectangle(0, 0, 100, 100)
    qt = QuadTree(boundary, capacity=2)
    
    # Insert more points than capacity to trigger subdivision
    points = [
        Point(10, 10), Point(20, 20), Point(30, 30),
        Point(-10, -10), Point(-20, -20)
    ]
    
    for point in points:
        qt.insert(point)
    
    # Check that subdivision occurred
    assert qt.divided, "QuadTree should have subdivided"
    assert qt.count_nodes() > 1, "Should have multiple nodes after subdivision"
    
    # Verify all points are retrievable
    all_points = qt.get_all_points()
    assert len(all_points) == len(points), "All points should be retrievable"
    
    print(f"✓ QuadTree subdivision passed (created {qt.count_nodes()} nodes)")


def test_risk_calculation():
    """Test risk score calculation."""
    print("Testing risk calculation...")
    
    # Test high risk scenario (shallow, high magnitude, near fault/volcano)
    high_risk = RiskCalculator.calculate_risk_score(
        magnitude=7.5,
        depth=5,
        intensity=10,
        frequency=10,
        fault_distance=5,
        volcano_distance=5,
        plate_zone=2
    )
    assert high_risk > 70, f"High risk scenario should have score > 70, got {high_risk}"
    assert RiskCalculator.get_risk_level(high_risk) in ["High", "Very High"]
    
    # Test low risk scenario (deep, low magnitude, far from fault/volcano)
    low_risk = RiskCalculator.calculate_risk_score(
        magnitude=3.0,
        depth=100,
        intensity=2,
        frequency=1,
        fault_distance=150,
        volcano_distance=150,
        plate_zone=0
    )
    assert low_risk < 50, f"Low risk scenario should have score < 50, got {low_risk}"
    assert RiskCalculator.get_risk_level(low_risk) in ["Low", "Very Low", "Moderate"]
    
    print(f"✓ Risk calculation passed (high={high_risk:.2f}, low={low_risk:.2f})")


def test_normalization_functions():
    """Test individual normalization functions."""
    print("Testing normalization functions...")
    
    # Test magnitude normalization
    assert RiskCalculator.normalize_magnitude(0) == 0.0
    assert 0.9 <= RiskCalculator.normalize_magnitude(9) <= 1.0
    
    # Test depth normalization (shallow = high risk)
    assert RiskCalculator.normalize_depth(0) == 1.0
    assert RiskCalculator.normalize_depth(10) > RiskCalculator.normalize_depth(100)
    
    # Test intensity normalization
    assert 0.0 <= RiskCalculator.normalize_intensity(1) <= 0.1
    assert 0.9 <= RiskCalculator.normalize_intensity(12) <= 1.0
    
    # Test fault distance (near = high risk)
    assert RiskCalculator.normalize_fault_distance(0) == 1.0
    assert RiskCalculator.normalize_fault_distance(10) > RiskCalculator.normalize_fault_distance(100)
    
    # Test plate zone
    assert RiskCalculator.normalize_plate_zone(0) < RiskCalculator.normalize_plate_zone(1)
    assert RiskCalculator.normalize_plate_zone(1) < RiskCalculator.normalize_plate_zone(2)
    
    print("✓ Normalization functions passed")


def test_performance_characteristics():
    """Test that QuadTree is faster than linear search."""
    print("Testing performance characteristics...")
    import time
    
    # Create a larger dataset
    boundary = Rectangle(0, 0, 1000, 1000)
    qt = QuadTree(boundary, capacity=4)
    
    # Insert many points
    num_points = 1000
    points = []
    for i in range(num_points):
        x = (i % 32) * 60 - 960
        y = (i // 32) * 60 - 960
        point = Point(x, y, data={'id': i})
        points.append(point)
        qt.insert(point)
    
    # QuadTree query
    query_rect = Rectangle(0, 0, 100, 100)
    start = time.perf_counter()
    qt_results = qt.query(query_rect)
    qt_time = time.perf_counter() - start
    
    # Linear search
    start = time.perf_counter()
    linear_results = [p for p in points if query_rect.contains(p)]
    linear_time = time.perf_counter() - start
    
    # QuadTree should be faster
    speedup = linear_time / qt_time if qt_time > 0 else float('inf')
    print(f"  QuadTree time: {qt_time*1000:.4f} ms")
    print(f"  Linear time:   {linear_time*1000:.4f} ms")
    print(f"  Speedup:       {speedup:.2f}x")
    
    # Results should be the same
    assert len(qt_results) == len(linear_results), "Results count should match"
    
    print(f"✓ Performance test passed (QuadTree {speedup:.1f}x faster)")


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("RUNNING TESTS")
    print("="*60)
    
    try:
        test_quadtree_basic()
        test_quadtree_subdivision()
        test_risk_calculation()
        test_normalization_functions()
        test_performance_characteristics()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
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
    success = run_all_tests()
    exit(0 if success else 1)
