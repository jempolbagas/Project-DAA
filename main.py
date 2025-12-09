"""
Main script for Earthquake Risk Zoning using Quadtree.
Loads data with Pandas, visualizes with Matplotlib, and compares
Quadtree vs Linear Search performance.
"""

import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from src.quadtree import QuadTree, Point, Rectangle
from src.risk import RiskCalculator


def load_earthquake_data(filepath):
    """Load earthquake data from CSV using Pandas."""
    print(f"Loading earthquake data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Remove any empty rows
    df = df.dropna(how='all')
    
    # Validate required columns exist
    required_cols = ['latitude', 'longitude', 'magnitude', 'depth', 'intensity', 
                     'frequency', 'fault_distance', 'volcano_distance', 'plate_zone']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    print(f"Loaded {len(df)} earthquake records")
    print(f"\nData columns: {list(df.columns)}")
    print(f"\nFirst few records:")
    print(df.head())
    return df


def calculate_risk_scores(df):
    """Calculate risk scores for all data points."""
    print("\nCalculating risk scores...")
    risk_scores = []
    
    for idx, row in df.iterrows():
        score = RiskCalculator.calculate_risk_score(
            magnitude=row['magnitude'],
            depth=row['depth'],
            intensity=row['intensity'],
            frequency=row['frequency'],
            fault_distance=row['fault_distance'],
            volcano_distance=row['volcano_distance'],
            plate_zone=row['plate_zone']
        )
        risk_scores.append(score)
    
    df['risk_score'] = risk_scores
    df['risk_level'] = df['risk_score'].apply(RiskCalculator.get_risk_level)
    
    print(f"Risk score statistics:")
    print(df['risk_score'].describe())
    return df


def build_quadtree(df):
    """Build quadtree from earthquake data."""
    print("\nBuilding QuadTree...")
    
    # Determine bounds
    lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
    lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
    
    # Add padding
    lat_center = (lat_min + lat_max) / 2
    lon_center = (lon_min + lon_max) / 2
    lat_range = (lat_max - lat_min) / 2 * 1.2
    lon_range = (lon_max - lon_min) / 2 * 1.2
    
    # Create quadtree
    boundary = Rectangle(lon_center, lat_center, lon_range, lat_range)
    qt = QuadTree(boundary, capacity=4)
    
    # Insert points
    for idx, row in df.iterrows():
        point = Point(
            row['longitude'],
            row['latitude'],
            data={
                'index': idx,
                'risk_score': row['risk_score'],
                'magnitude': row['magnitude']
            }
        )
        qt.insert(point)
    
    print(f"QuadTree built with {qt.count_nodes()} nodes")
    return qt


def linear_search(df, center_lat, center_lon, radius):
    """Linear search for points within radius."""
    results = []
    
    for idx, row in df.iterrows():
        distance = RiskCalculator.calculate_distance(
            center_lon, center_lat,
            row['longitude'], row['latitude']
        )
        if distance <= radius:
            results.append(idx)
    
    return results


def quadtree_search(qt, center_lat, center_lon, radius):
    """QuadTree search for points within radius."""
    center_point = Point(center_lon, center_lat)
    results = qt.query_radius(center_point, radius)
    return results


def compare_performance(df, qt, num_queries=100):
    """Compare QuadTree vs Linear search performance."""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON: QuadTree vs Linear Search")
    print("="*60)
    
    # Generate random query points
    lat_mean = df['latitude'].mean()
    lon_mean = df['longitude'].mean()
    lat_std = df['latitude'].std()
    lon_std = df['longitude'].std()
    
    # Test with different radii
    radii = [0.5, 1.0, 2.0, 3.0]
    
    results = []
    
    for radius in radii:
        print(f"\nRadius: {radius}°")
        
        # QuadTree search timing
        qt_times = []
        qt_results_count = []
        
        for i in range(num_queries):
            # Random center point
            center_lat = lat_mean + (i % 10 - 5) * lat_std / 10
            center_lon = lon_mean + (i % 10 - 5) * lon_std / 10
            
            start = time.perf_counter()
            qt_results = quadtree_search(qt, center_lat, center_lon, radius)
            end = time.perf_counter()
            
            qt_times.append(end - start)
            qt_results_count.append(len(qt_results))
        
        # Linear search timing
        linear_times = []
        linear_results_count = []
        
        for i in range(num_queries):
            center_lat = lat_mean + (i % 10 - 5) * lat_std / 10
            center_lon = lon_mean + (i % 10 - 5) * lon_std / 10
            
            start = time.perf_counter()
            linear_results = linear_search(df, center_lat, center_lon, radius)
            end = time.perf_counter()
            
            linear_times.append(end - start)
            linear_results_count.append(len(linear_results))
        
        # Calculate statistics
        avg_qt_time = sum(qt_times) / len(qt_times) * 1000  # ms
        avg_linear_time = sum(linear_times) / len(linear_times) * 1000  # ms
        speedup = avg_linear_time / avg_qt_time if avg_qt_time > 0 else 0
        
        print(f"  QuadTree avg time: {avg_qt_time:.4f} ms")
        print(f"  Linear avg time:   {avg_linear_time:.4f} ms")
        print(f"  Speedup:           {speedup:.2f}x")
        print(f"  Avg results found: {sum(qt_results_count)/len(qt_results_count):.1f}")
        
        results.append({
            'radius': radius,
            'quadtree_time': avg_qt_time,
            'linear_time': avg_linear_time,
            'speedup': speedup
        })
    
    return results


def visualize_risk_map(df, qt, output_file='risk_map.png'):
    """Visualize earthquake risk map with Matplotlib."""
    print(f"\nGenerating risk visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # 1. Risk Score Heatmap
    ax1 = axes[0, 0]
    scatter1 = ax1.scatter(
        df['longitude'],
        df['latitude'],
        c=df['risk_score'],
        s=df['magnitude'] * 20,
        cmap='YlOrRd',
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title('Earthquake Risk Score Map\n(Size = Magnitude)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Risk Score', rotation=270, labelpad=20)
    
    # 2. Risk Level Categories
    ax2 = axes[0, 1]
    risk_colors = {
        'Very High': 'darkred',
        'High': 'red',
        'Moderate': 'orange',
        'Low': 'yellow',
        'Very Low': 'lightgreen'
    }
    
    for level, color in risk_colors.items():
        level_data = df[df['risk_level'] == level]
        if len(level_data) > 0:
            ax2.scatter(
                level_data['longitude'],
                level_data['latitude'],
                c=color,
                s=80,
                label=level,
                alpha=0.7,
                edgecolors='black',
                linewidth=0.5
            )
    
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.set_title('Risk Level Categories', fontsize=12, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # 3. Magnitude vs Depth
    ax3 = axes[1, 0]
    scatter3 = ax3.scatter(
        df['magnitude'],
        df['depth'],
        c=df['risk_score'],
        s=100,
        cmap='YlOrRd',
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )
    ax3.set_xlabel('Magnitude')
    ax3.set_ylabel('Depth (km)')
    ax3.set_title('Magnitude vs Depth (colored by Risk Score)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.invert_yaxis()  # Depth increases downward
    cbar3 = plt.colorbar(scatter3, ax=ax3)
    cbar3.set_label('Risk Score', rotation=270, labelpad=20)
    
    # 4. Risk Distribution
    ax4 = axes[1, 1]
    risk_counts = df['risk_level'].value_counts()
    risk_order = ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
    risk_counts = risk_counts.reindex(risk_order, fill_value=0)
    
    colors = [risk_colors.get(level, 'gray') for level in risk_order]
    bars = ax4.bar(risk_order, risk_counts, color=colors, edgecolor='black', linewidth=1.5)
    ax4.set_xlabel('Risk Level')
    ax4.set_ylabel('Number of Locations')
    ax4.set_title('Risk Level Distribution', fontsize=12, fontweight='bold')
    ax4.grid(True, axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Risk map saved to {output_file}")
    
    return fig


def visualize_quadtree_structure(qt, df, output_file='quadtree_structure.png'):
    """Visualize QuadTree structure."""
    print(f"\nGenerating QuadTree structure visualization...")
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Draw quadtree boundaries
    def draw_boundary(node, depth=0):
        if node is None:
            return
        
        rect = node.boundary
        alpha = max(0.1, 1.0 - depth * 0.15)
        color = plt.cm.viridis(depth / 8)
        
        rectangle = patches.Rectangle(
            (rect.x - rect.width, rect.y - rect.height),
            rect.width * 2,
            rect.height * 2,
            linewidth=1,
            edgecolor=color,
            facecolor='none',
            alpha=alpha
        )
        ax.add_patch(rectangle)
        
        if node.divided:
            draw_boundary(node.northeast, depth + 1)
            draw_boundary(node.northwest, depth + 1)
            draw_boundary(node.southeast, depth + 1)
            draw_boundary(node.southwest, depth + 1)
    
    draw_boundary(qt)
    
    # Overlay earthquake points
    scatter = ax.scatter(
        df['longitude'],
        df['latitude'],
        c=df['risk_score'],
        s=50,
        cmap='YlOrRd',
        alpha=0.8,
        edgecolors='black',
        linewidth=0.5,
        zorder=5
    )
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('QuadTree Spatial Partitioning Structure\n(Divide & Conquer)', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Risk Score', rotation=270, labelpad=20)
    
    # Add text info
    info_text = f"Total Nodes: {qt.count_nodes()}\nTotal Points: {len(df)}"
    ax.text(0.02, 0.98, info_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"QuadTree structure saved to {output_file}")
    
    return fig


def main():
    """Main execution function."""
    print("="*60)
    print("EARTHQUAKE RISK ZONING - QUADTREE IMPLEMENTATION")
    print("Using Divide & Conquer Algorithm")
    print("="*60)
    
    # Load data
    df = load_earthquake_data('data/earthquake_data.csv')
    
    # Calculate risk scores
    df = calculate_risk_scores(df)
    
    # Build QuadTree
    qt = build_quadtree(df)
    
    # Compare performance
    performance_results = compare_performance(df, qt, num_queries=100)
    
    # Visualize
    visualize_risk_map(df, qt, 'risk_map.png')
    visualize_quadtree_structure(qt, df, 'quadtree_structure.png')
    
    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nRisk Level Distribution:")
    print(df['risk_level'].value_counts().sort_index())
    
    print(f"\nTop 5 Highest Risk Locations:")
    top_risk = df.nlargest(5, 'risk_score')[['latitude', 'longitude', 'magnitude', 
                                               'depth', 'risk_score', 'risk_level']]
    print(top_risk.to_string(index=False))
    
    print(f"\n{'='*60}")
    print("Analysis complete! Check generated visualizations:")
    print("  - risk_map.png")
    print("  - quadtree_structure.png")
    print("="*60)


if __name__ == "__main__":
    main()
