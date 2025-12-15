# Implementation Task: Optimize Spatial Queries using KD-Tree

## 1\. Context & Objective

The current implementation of the Earthquake Risk Zoning project uses a **brute-force linear search** ($O(N \cdot M)$) to calculate distances between earthquake points and geological features (faults/volcanoes). This creates a significant performance bottleneck.

**Goal:** Refactor the distance calculation logic to use a **KD-Tree** (k-dimensional tree) from `scipy.spatial`, reducing complexity to $O(N \log M)$.

## 2\. Target Files

  * `requirements.txt`: Needs dependency update.
  * `src/risk.py`: Primary location for refactoring distance logic.
  * `main.py`: Needs update to build trees during data loading.

## 3\. Detailed Implementation Steps

### Step A: Update Dependencies

Add `scipy` to `requirements.txt` to access spatial algorithms.

```text
pandas>=2.0.0
matplotlib>=3.7.0
numpy>=1.24.0
scipy>=1.10.0  <-- Add this
```

### Step B: Refactor `src/risk.py`

**Current Logic (Inefficient):**
Currently, `find_nearest_fault_distance` iterates through every row of the dataframe.

**Required Logic (KD-Tree):**

1.  Import `KDTree` from `scipy.spatial`.
2.  Modify `find_nearest_fault_distance` and `find_nearest_volcano_distance` to accept a **KDTree object** instead of a DataFrame.
3.  Use the `tree.query()` method to find the nearest neighbor.

**Code Reference for `src/risk.py`:**

```python
from scipy.spatial import KDTree

class RiskCalculator:
    # ... existing weights ...

    @staticmethod
    def build_spatial_tree(dataframe):
        """
        Helper to build a KDTree from a dataframe containing 'latitude' and 'longitude'.
        Returns None if dataframe is empty.
        """
        if dataframe is None or dataframe.empty:
            return None
        # Extract coordinates (Lat, Lon)
        # Note: KDTree calculates Euclidean distance. For small regions like Java, 
        # this is an acceptable approximation for relative risk scoring.
        coordinates = dataframe[['latitude', 'longitude']].values
        return KDTree(coordinates)

    @classmethod
    def find_nearest_fault_distance(cls, lat, lon, faults_tree):
        """
        Find distance using KDTree query.
        Args:
            lat, lon: Coordinates of the earthquake
            faults_tree: Pre-built scipy.spatial.KDTree object
        """
        if faults_tree is None:
            return 200.0 # Default max distance
        
        # tree.query returns (distance, index)
        # The distance returned is Euclidean (degrees). 
        # Approximate conversion to km: 1 degree approx 111km
        dist_degrees, _ = faults_tree.query([lat, lon])
        dist_km = dist_degrees * 111.0 
        
        return dist_km

    # Apply similar logic to find_nearest_volcano_distance
```

*Note: You also need to update `calculate_enhanced_risk_score` to accept `faults_tree` and `volcanoes_tree` instead of the dataframes, and pass them down to the distance functions.*

### Step C: Update `main.py`

1.  Load the CSV data.
2.  **Immediately build the KDTrees** using the helper method from `RiskCalculator`.
3.  Pass these trees into `calculate_risk_scores`.

**Code Reference for `main.py`:**

```python
# Inside main():

# 1. Load Data
faults_df, volcanoes_df = load_geological_data(...)

# 2. Build Trees (NEW STEP)
print("Building geological spatial trees...")
faults_tree = RiskCalculator.build_spatial_tree(faults_df)
volcanoes_tree = RiskCalculator.build_spatial_tree(volcanoes_df)

# 3. Calculate Risk (Pass trees instead of DFs)
df = calculate_risk_scores(df, faults_tree, volcanoes_tree)
```

## 4\. Verification

After implementation, run `test_implementation.py`.

  * **Performance Check:** The risk calculation step in `main.py` should be significantly faster, especially if the earthquake dataset size increases.
  * **Accuracy Check:** The calculated risk scores should remain relatively consistent with previous outputs (minor variations due to Haversine vs Euclidean approximation are expected and acceptable for this assignment context).

## 5\. Constraint Checklist

  * [ ] Do **not** remove the QuadTree implementation (that is for querying the earthquakes, KD-Tree is for the static geological features).
  * [ ] Ensure `None` checking handles cases where fault/volcano data might be missing.
  * [ ] Maintain existing CSV export functionality.
