"""
Quadtree implementation for spatial partitioning of earthquake data.
Uses Divide & Conquer approach for efficient spatial queries.
"""

class Point:
    """Represents a point in 2D space with associated data."""
    
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"


class Rectangle:
    """Represents a rectangular boundary."""
    
    def __init__(self, x, y, width, height):
        self.x = x  # Center x
        self.y = y  # Center y
        self.width = width
        self.height = height
    
    def contains(self, point):
        """Check if point is within this rectangle."""
        return (self.x - self.width <= point.x <= self.x + self.width and
                self.y - self.height <= point.y <= self.y + self.height)
    
    def intersects(self, range_rect):
        """Check if this rectangle intersects with another rectangle."""
        return not (range_rect.x - range_rect.width > self.x + self.width or
                   range_rect.x + range_rect.width < self.x - self.width or
                   range_rect.y - range_rect.height > self.y + self.height or
                   range_rect.y + range_rect.height < self.y - self.height)


class QuadTree:
    """
    QuadTree data structure for efficient spatial partitioning.
    Uses Divide & Conquer to recursively partition 2D space.
    """
    
    def __init__(self, boundary, capacity=4):
        """
        Initialize QuadTree node.
        
        Args:
            boundary: Rectangle defining the bounds of this node
            capacity: Maximum points before subdivision
        """
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False
        
        # Child quadrants (NE, NW, SE, SW)
        self.northeast = None
        self.northwest = None
        self.southeast = None
        self.southwest = None
    
    def subdivide(self):
        """Divide this node into 4 quadrants (Divide & Conquer)."""
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.width / 2
        h = self.boundary.height / 2
        
        ne_boundary = Rectangle(x + w, y + h, w, h)
        self.northeast = QuadTree(ne_boundary, self.capacity)
        
        nw_boundary = Rectangle(x - w, y + h, w, h)
        self.northwest = QuadTree(nw_boundary, self.capacity)
        
        se_boundary = Rectangle(x + w, y - h, w, h)
        self.southeast = QuadTree(se_boundary, self.capacity)
        
        sw_boundary = Rectangle(x - w, y - h, w, h)
        self.southwest = QuadTree(sw_boundary, self.capacity)
        
        self.divided = True
    
    def insert(self, point):
        """
        Insert a point into the quadtree.
        
        Args:
            point: Point object to insert
            
        Returns:
            bool: True if insertion successful, False otherwise
        """
        # Check if point is within boundary
        if not self.boundary.contains(point):
            return False
        
        # If capacity not reached, add point here
        if len(self.points) < self.capacity:
            self.points.append(point)
            return True
        
        # Otherwise, subdivide and insert into appropriate quadrant
        if not self.divided:
            self.subdivide()
        
        # Try inserting into child quadrants
        if self.northeast.insert(point):
            return True
        if self.northwest.insert(point):
            return True
        if self.southeast.insert(point):
            return True
        if self.southwest.insert(point):
            return True
        
        return False
    
    def query(self, range_rect, found=None):
        """
        Query all points within a rectangular range (Divide & Conquer).
        
        Args:
            range_rect: Rectangle defining search area
            found: List to accumulate found points
            
        Returns:
            List of points within the range
        """
        if found is None:
            found = []
        
        # If boundary doesn't intersect range, return empty
        if not self.boundary.intersects(range_rect):
            return found
        
        # Check points in this node
        for point in self.points:
            if range_rect.contains(point):
                found.append(point)
        
        # If divided, recursively search quadrants
        if self.divided:
            self.northeast.query(range_rect, found)
            self.northwest.query(range_rect, found)
            self.southeast.query(range_rect, found)
            self.southwest.query(range_rect, found)
        
        return found
    
    def query_radius(self, center_point, radius):
        """
        Query all points within a circular radius.
        
        Args:
            center_point: Point at center of search
            radius: Search radius
            
        Returns:
            List of points within radius
        """
        # Create bounding rectangle for circular area
        range_rect = Rectangle(center_point.x, center_point.y, radius, radius)
        candidates = self.query(range_rect)
        
        # Filter to only points actually within circular radius
        found = []
        for point in candidates:
            dx = point.x - center_point.x
            dy = point.y - center_point.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= radius:
                found.append(point)
        
        return found
    
    def get_all_points(self):
        """Get all points in the quadtree."""
        all_points = list(self.points)
        
        if self.divided:
            all_points.extend(self.northeast.get_all_points())
            all_points.extend(self.northwest.get_all_points())
            all_points.extend(self.southeast.get_all_points())
            all_points.extend(self.southwest.get_all_points())
        
        return all_points
    
    def count_nodes(self):
        """Count total number of nodes in the tree."""
        count = 1
        if self.divided:
            count += self.northeast.count_nodes()
            count += self.northwest.count_nodes()
            count += self.southeast.count_nodes()
            count += self.southwest.count_nodes()
        return count
