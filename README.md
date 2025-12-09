# Earthquake Risk Zoning using Quadtree (Divide & Conquer)

A Python project implementing earthquake risk assessment using **QuadTree spatial partitioning** and the **Divide & Conquer** algorithm. This project analyzes earthquake risk based on multiple parameters and compares the performance of QuadTree vs linear search.

## Features

- **Spatial Partitioning**: Implements QuadTree data structure for efficient spatial queries
- **Risk Assessment**: Calculates risk scores based on 7 key parameters:
  1. Magnitude (Richter scale)
  2. Depth (km)
  3. Intensity (MMI scale)
  4. Historical Frequency
  5. Distance to Fault Lines
  6. Distance to Volcanoes
  7. Plate Zone Type
- **Performance Comparison**: Benchmarks QuadTree vs Linear Search
- **Visualization**: Generates comprehensive risk maps using Matplotlib
- **Data Processing**: Uses Pandas for efficient data handling

## Project Structure

```
daa-guweh/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── quadtree.py          # QuadTree implementation (Divide & Conquer)
│   └── risk.py              # Risk calculation module
├── data/
│   └── earthquake_data.csv  # Sample earthquake data
├── main.py                  # Main execution script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jempolbagas/daa-guweh.git
cd daa-guweh
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script to perform risk analysis and generate visualizations:

```bash
python main.py
```

This will:
1. Load earthquake data from CSV
2. Calculate risk scores for all locations
3. Build QuadTree structure
4. Compare performance (QuadTree vs Linear Search)
5. Generate visualizations:
   - `risk_map.png` - Comprehensive risk analysis
   - `quadtree_structure.png` - Spatial partitioning visualization

## QuadTree Algorithm (Divide & Conquer)

The QuadTree uses a recursive divide-and-conquer approach:

1. **Divide**: Split space into 4 quadrants when capacity is exceeded
2. **Conquer**: Insert points into appropriate quadrants
3. **Query**: Recursively search only relevant quadrants

### Time Complexity
- **Insert**: O(log n) average case
- **Query**: O(log n + k) where k is the number of results
- **Linear Search**: O(n)

### Space Complexity
- O(n) where n is the number of points

## Risk Calculation

Risk scores (0-100) are calculated using weighted parameters:

| Parameter | Weight | Description |
|-----------|--------|-------------|
| Magnitude | 25% | Earthquake strength (Richter scale) |
| Depth | 10% | Depth of hypocenter (shallow = higher risk) |
| Intensity | 20% | Modified Mercalli Intensity (MMI) |
| Frequency | 15% | Historical earthquake frequency |
| Fault Distance | 15% | Distance to nearest fault line |
| Volcano Distance | 10% | Distance to nearest volcano |
| Plate Zone | 5% | Tectonic plate zone type |

### Risk Levels
- **Very High**: 80-100
- **High**: 60-79
- **Moderate**: 40-59
- **Low**: 20-39
- **Very Low**: 0-19

## Data Format

The CSV file should contain the following columns:

```csv
latitude,longitude,magnitude,depth,intensity,frequency,fault_distance,volcano_distance,plate_zone
-6.2,106.8,6.5,10,8,5,15,25,2
```

- `latitude`, `longitude`: Geographic coordinates
- `magnitude`: Richter scale (0-9+)
- `depth`: Depth in km
- `intensity`: MMI scale (1-12)
- `frequency`: Events per year
- `fault_distance`: Distance to nearest fault (km)
- `volcano_distance`: Distance to nearest volcano (km)
- `plate_zone`: 0=stable, 1=boundary, 2=subduction

## Example Output

```
PERFORMANCE COMPARISON: QuadTree vs Linear Search
============================================================

Radius: 0.5°
  QuadTree avg time: 0.0234 ms
  Linear avg time:   0.1567 ms
  Speedup:           6.70x
  Avg results found: 2.3

Radius: 1.0°
  QuadTree avg time: 0.0456 ms
  Linear avg time:   0.1589 ms
  Speedup:           3.48x
  Avg results found: 5.8
```

## Visualizations

The project generates two main visualizations:

1. **risk_map.png**: 4-panel visualization showing:
   - Risk score heatmap
   - Risk level categories
   - Magnitude vs Depth analysis
   - Risk distribution histogram

2. **quadtree_structure.png**: Shows the QuadTree spatial partitioning overlaid with earthquake locations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Authors

- jempolbagas

## Acknowledgments

- Design & Analysis of Algorithms course project
- QuadTree data structure implementation
- Divide & Conquer algorithm paradigm