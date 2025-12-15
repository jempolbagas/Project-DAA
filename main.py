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
    

    # Validate required columns exist (simplified for enhanced calculation)
    required_cols = ['latitude', 'longitude', 'magnitude', 'depth', 'intensity', 'frequency', 'plate_zone']
    optional_cols = ['region_name']  # Optional region name column
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Handle optional region_name column
    if 'region_name' not in df.columns:
        print("Warning: 'region_name' column not found. Adding default region names.")
        df['region_name'] = 'Unknown Region'
    else:
        print(f"Region names loaded: {len(df['region_name'].unique())} unique regions")
    
    print(f"Loaded {len(df)} earthquake records")
    print(f"\nData columns: {list(df.columns)}")
    print(f"\nFirst few records:")
    print(df.head())
    return df


def load_geological_data(faults_filepath, volcanoes_filepath):
    """Load geological data (faults and volcanoes) from CSV files."""
    print(f"\nLoading geological data...")
    
    # Load faults data
    faults_df = pd.read_csv(faults_filepath)
    print(f"Loaded {len(faults_df)} fault records")
    
    # Load volcanoes data
    volcanoes_df = pd.read_csv(volcanoes_filepath)
    print(f"Loaded {len(volcanoes_df)} volcano records")
    
    print(f"\nFaults data columns: {list(faults_df.columns)}")
    print(f"Volcanoes data columns: {list(volcanoes_df.columns)}")
    
    return faults_df, volcanoes_df



def calculate_risk_scores(df, faults_tree=None, volcanoes_tree=None):
    """Calculate risk scores for all data points using enhanced geological data (KDTree)."""
    print("\nCalculating enhanced risk scores with geological data...")
    risk_scores = []
    fault_distances = []
    volcano_distances = []
    
    for idx, row in df.iterrows():
        # Use enhanced risk calculation with geological data
        score = RiskCalculator.calculate_enhanced_risk_score(
            magnitude=row['magnitude'],
            depth=row['depth'],
            intensity=row['intensity'],
            frequency=row['frequency'],
            lat=row['latitude'],
            lon=row['longitude'],
            faults_tree=faults_tree,
            volcanoes_tree=volcanoes_tree,
            plate_zone=row['plate_zone']
        )
        risk_scores.append(score)
        
        # Calculate and store distances for analysis
        fault_dist = RiskCalculator.find_nearest_fault_distance(
            row['latitude'], row['longitude'], faults_tree
        )
        volcano_dist = RiskCalculator.find_nearest_volcano_distance(
            row['latitude'], row['longitude'], volcanoes_tree
        )
        fault_distances.append(fault_dist)
        volcano_distances.append(volcano_dist)
    
    df['risk_score'] = risk_scores
    df['risk_level'] = df['risk_score'].apply(RiskCalculator.get_risk_level)
    df['fault_distance_km'] = fault_distances
    df['volcano_distance_km'] = volcano_distances
    
    print(f"Enhanced risk score statistics:")
    print(df['risk_score'].describe())
    print(f"\nAverage distance to nearest fault: {sum(fault_distances)/len(fault_distances):.2f} km")
    print(f"Average distance to nearest volcano: {sum(volcano_distances)/len(volcano_distances):.2f} km")
    
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




def visualize_risk_map(df, qt, output_file='output/visualizations/risk_map.png'):
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




def visualize_quadtree_structure(qt, df, output_file='output/visualizations/quadtree_structure.png'):
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






def visualize_regional_analysis(df, regions_df, regional_analysis, output_file='output/visualizations/regional_analysis.png'):
    """Visualize regional risk analysis for Pulau Jawa."""
    print(f"\nGenerating regional analysis visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    
    # Risk colors mapping
    risk_colors = {
        'Very High': 'darkred',
        'High': 'red',
        'Moderate': 'orange',
        'Low': 'yellow',
        'Very Low': 'lightgreen'
    }
    
    # 1. Regional Risk Score Map
    ax1 = axes[0, 0]
    
    if regional_analysis['regional_stats'] is not None:
        regional_stats = regional_analysis['regional_stats']
        scatter1 = ax1.scatter(
            regional_stats['longitude'],
            regional_stats['latitude'],
            c=regional_stats['risk_score'],
            s=200,
            cmap='YlOrRd',
            alpha=0.8,
            edgecolors='black',
            linewidth=1
        )
        
        # Add region labels
        for idx, row in regional_stats.iterrows():
            ax1.annotate(
                row['region_name'][:8],  # Abbreviated name
                (row['longitude'], row['latitude']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                alpha=0.7
            )
    
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title('Regional Risk Scores - Pulau Jawa\n(Size & Color = Risk Level)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Regional Risk Score', rotation=270, labelpad=20)
    
    # 2. Provincial Risk Comparison
    ax2 = axes[0, 1]
    
    if regional_analysis['provincial_stats'] is not None:
        provincial_stats = regional_analysis['provincial_stats']
        
        # Sort by risk score for better visualization
        provincial_stats_sorted = provincial_stats.sort_values('avg_risk_score', ascending=True)
        
        bars = ax2.barh(
            provincial_stats_sorted['province'],
            provincial_stats_sorted['avg_risk_score'],
            color=[risk_colors.get(RiskCalculator.get_risk_level(score), 'gray') 
                   for score in provincial_stats_sorted['avg_risk_score']],
            edgecolor='black',
            linewidth=1
        )
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{width:.1f}', ha='left', va='center', fontweight='bold')
    
    ax2.set_xlabel('Average Risk Score')
    ax2.set_title('Provincial Risk Comparison', fontsize=12, fontweight='bold')
    ax2.grid(True, axis='x', alpha=0.3)
    
    # 3. Risk Level Distribution by Province
    ax3 = axes[1, 0]
    
    if regional_analysis['risk_by_province'] is not None:
        risk_by_province = regional_analysis['risk_by_province']
        
        # Remove the 'All' row and column for better visualization
        if 'All' in risk_by_province.index:
            risk_by_province = risk_by_province.drop('All', axis=0)
        if 'All' in risk_by_province.columns:
            risk_by_province = risk_by_province.drop('All', axis=1)
        
        # Create stacked bar chart
        risk_by_province.plot(kind='bar', stacked=True, ax=ax3, 
                             color=[risk_colors.get(col, 'gray') for col in risk_by_province.columns],
                             edgecolor='black', linewidth=0.5)
    
    ax3.set_xlabel('Province')
    ax3.set_ylabel('Number of Regions')
    ax3.set_title('Risk Level Distribution by Province', fontsize=12, fontweight='bold')
    ax3.legend(title='Risk Level', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, axis='y', alpha=0.3)
    
    # 4. Top Risk Regions
    ax4 = axes[1, 1]
    
    if regional_analysis['high_risk_regions'] is not None:
        top_regions = regional_analysis['high_risk_regions'].head(10)
        
        bars = ax4.barh(
            range(len(top_regions)),
            top_regions['risk_score'],
            color=[risk_colors.get(RiskCalculator.get_risk_level(score), 'gray') 
                   for score in top_regions['risk_score']],
            edgecolor='black',
            linewidth=1
        )
        
        # Set y-tick labels with region names and provinces
        labels = [f"{row['region_name'][:12]} ({row['province'][:8]})" 
                 for _, row in top_regions.iterrows()]
        ax4.set_yticks(range(len(top_regions)))
        ax4.set_yticklabels(labels, fontsize=9)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax4.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{width:.1f}', ha='left', va='center', fontweight='bold')
    
    ax4.set_xlabel('Risk Score')
    ax4.set_title('Top 10 Highest Risk Regions', fontsize=12, fontweight='bold')
    ax4.grid(True, axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Regional analysis visualization saved to {output_file}")
    
    return fig


def main():
    """Main execution function."""
    print("="*60)
    print("EARTHQUAKE RISK ZONING - QUADTREE IMPLEMENTATION")
    print("Using Divide & Conquer Algorithm")
    print("Enhanced with Geological Data Integration")
    print("="*60)
    
    # Load earthquake data
    df = load_earthquake_data('data/earthquake_data.csv')
    
    # Load geological data (faults and volcanoes)
    faults_data, volcanoes_data = load_geological_data(
        'data/faults_data.csv', 
        'data/volcanoes_data.csv'
    )

    # Build geological spatial trees
    print("\nBuilding geological spatial trees...")
    faults_tree = RiskCalculator.build_spatial_tree(faults_data)
    volcanoes_tree = RiskCalculator.build_spatial_tree(volcanoes_data)
    
    # Calculate enhanced risk scores with geological data
    df = calculate_risk_scores(df, faults_tree, volcanoes_tree)
    
    # Build QuadTree
    qt = build_quadtree(df)
    
    # Compare performance
    performance_results = compare_performance(df, qt, num_queries=100)
    


    # Visualize
    visualize_risk_map(df, qt, 'output/visualizations/risk_map.png')
    visualize_quadtree_structure(qt, df, 'output/visualizations/quadtree_structure.png')
    
    # Enhanced summary statistics
    print("\n" + "="*60)
    print("ENHANCED SUMMARY WITH GEOLOGICAL DATA")
    print("="*60)
    print(f"\nRisk Level Distribution:")
    print(df['risk_level'].value_counts().sort_index())
    

    print(f"\nTop 5 Highest Risk Locations:")
    top_risk = df.nlargest(5, 'risk_score')[['latitude', 'longitude', 'magnitude', 
                                               'depth', 'risk_score', 'risk_level',
                                               'fault_distance_km', 'volcano_distance_km', 'region_name']]
    print(top_risk.to_string(index=False))
    

    # Load Jawa regions data
    print(f"\n" + "="*60)
    print("REGIONAL ANALYSIS FOR PULAU JAWA")
    print("="*60)
    
    regions_df = RiskCalculator.load_jawa_regions_data('data/jawa_regions.csv')
    
    if regions_df is not None:
        # Comprehensive regional analysis
        regional_analysis = RiskCalculator.get_regional_comparison(df, regions_df)
        
        # Display regional summary
        print("\n" + RiskCalculator.generate_regional_summary(regional_analysis))
        
        # Export regional data
        if regional_analysis['regional_stats'] is not None:
            regional_stats = regional_analysis['regional_stats']



            print(f"\nExporting regional statistics to 'output/data/regional_risk_analysis.csv'...")
            regional_stats.to_csv('output/data/regional_risk_analysis.csv', index=False)
            print(f"Regional statistics saved successfully!")
        
        if regional_analysis['provincial_stats'] is not None:
            provincial_stats = regional_analysis['provincial_stats']



            print(f"\nExporting provincial statistics to 'output/data/provincial_risk_analysis.csv'...")
            provincial_stats.to_csv('output/data/provincial_risk_analysis.csv', index=False)
            print(f"Provincial statistics saved successfully!")
        


        # Enhanced regional visualization
        print(f"\nGenerating regional risk visualization...")
        visualize_regional_analysis(df, regions_df, regional_analysis, 'output/visualizations/regional_analysis.png')
        
        # Detailed regional breakdown
        print(f"\nDetailed Regional Analysis:")
        print(f"Total regions analyzed: {len(regional_analysis['regional_stats']) if regional_analysis['regional_stats'] is not None else 0}")
        print(f"Total provinces: {len(regional_analysis['provincial_stats']) if regional_analysis['provincial_stats'] is not None else 0}")
        
        if regional_analysis['regional_stats'] is not None:
            print(f"\nTop 5 Highest Risk Regions:")
            top_regions = regional_analysis['regional_stats'].nlargest(5, 'risk_score')
            for idx, row in top_regions.iterrows():
                print(f"  {row['region_name']} ({row['province']}): Risk Score {row['risk_score']:.2f}")
        
        if regional_analysis['provincial_stats'] is not None:
            print(f"\nProvincial Risk Summary:")
            for idx, row in regional_analysis['provincial_stats'].iterrows():
                print(f"  {row['province']}: Avg Risk {row['avg_risk_score']:.2f}, {row['regions_affected']} regions")
    else:
        # Fallback to basic regional analysis if regions data not available
        print(f"\nBasic Regional Risk Analysis:")
        region_stats = df.groupby('region_name').agg({
            'risk_score': ['mean', 'count'],
            'magnitude': 'mean',
            'latitude': 'mean',
            'longitude': 'mean'
        }).round(2)
        
        region_stats.columns = ['Avg_Risk_Score', 'Earthquake_Count', 'Avg_Magnitude', 'Avg_Lat', 'Avg_Lon']
        region_stats = region_stats.sort_values('Avg_Risk_Score', ascending=False)
        print(region_stats.to_string())
    
    # Geological analysis
    print(f"\nGeological Analysis:")
    print(f"Closest to fault line: {df.loc[df['fault_distance_km'].idxmin(), 'fault_distance_km']:.2f} km")
    print(f"Closest to volcano: {df.loc[df['volcano_distance_km'].idxmin(), 'volcano_distance_km']:.2f} km")
    
    # Risk level by region
    print(f"\nRisk Level Distribution by Region:")
    risk_by_region = pd.crosstab(df['region_name'], df['risk_level'])
    print(risk_by_region.to_string())
    
    print(f"\n{'='*60}")
    print("Analysis complete! Check generated visualizations:")
    print("  - risk_map.png")
    print("  - quadtree_structure.png")
    print("="*60)


if __name__ == "__main__":
    main()
