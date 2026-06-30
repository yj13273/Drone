import time
import math
import heapq
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any, Optional

class PriorityQueue:
    """Optimized priority queue for D* Lite with a tie-breaker counter."""
    def __init__(self):
        self.heap = []
        self.vertices = {}
        self.counter = 0

    def insert(self, vertex: Tuple[int, int], key: Tuple[float, float]):
        if vertex in self.vertices:
            self.update(vertex, key)
            return
        entry = [key[0], key[1], self.counter, vertex]
        self.counter += 1
        self.vertices[vertex] = entry
        heapq.heappush(self.heap, entry)

    def remove(self, vertex: Tuple[int, int]):
        if vertex in self.vertices:
            entry = self.vertices.pop(vertex)
            entry[-1] = None

    def pop(self) -> Optional[Tuple[Tuple[int, int], Tuple[float, float]]]:
        while self.heap:
            k0, k1, _, vertex = heapq.heappop(self.heap)
            if vertex is not None:
                del self.vertices[vertex]
                return vertex, (k0, k1)
        return None

    def top_key(self) -> Tuple[float, float]:
        while self.heap:
            k0, k1, _, vertex = self.heap[0]
            if vertex is not None:
                return (k0, k1)
            heapq.heappop(self.heap)
        return (float('inf'), float('inf'))

    def update(self, vertex: Tuple[int, int], new_key: Tuple[float, float]):
        if vertex in self.vertices:
            self.remove(vertex)
        self.insert(vertex, new_key)

    def contains(self, vertex: Tuple[int, int]) -> bool:
        return vertex in self.vertices


class DStarLiteUAV:
    """Incremental D* Lite Path Planner adjusted for UAV constraints."""
    def __init__(self, cost_matrix: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int], threat_threshold: float):
        self.cost_matrix = cost_matrix
        self.rows, self.cols = cost_matrix.shape
        self.start = start
        self.current_position = start
        self.goal = goal
        self.threat_threshold = threat_threshold

        self.g = {}
        self.rhs = {}
        self.km = 0.0
        self.s_last = self.start
        self.U = PriorityQueue()
        
        self.nodes_expanded = 0
        self.initialize()

    def initialize(self):
        self.rhs[self.goal] = 0.0
        self.U.insert(self.goal, self.calculate_key(self.goal))

    def get_g(self, s: Tuple[int, int]) -> float:
        return self.g.get(s, float('inf'))

    def get_rhs(self, s: Tuple[int, int]) -> float:
        return self.rhs.get(s, float('inf'))

    def heuristic(self, s1: Tuple[int, int], s2: Tuple[int, int]) -> float:
        # Octile distance for accurate 8-directional heuristic tracking
        dx, dy = abs(s1[0] - s2[0]), abs(s1[1] - s2[1])
        return min(dx, dy) * math.sqrt(2) + abs(dx - dy)

    def calculate_key(self, s: Tuple[int, int]) -> Tuple[float, float]:
        g_rhs = min(self.get_g(s), self.get_rhs(s))
        return (g_rhs + self.heuristic(self.current_position, s) + self.km, g_rhs)

    def get_neighbors(self, s: Tuple[int, int]) -> List[Tuple[int, int]]:
        neighbors = []
        directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        for dx, dy in directions:
            nx, ny = s[0] + dx, s[1] + dy
            if 0 <= nx < self.rows and 0 <= ny < self.cols:
                # Dynamic Filter: Check threat thresholds immediately
                if self.cost_matrix[nx, ny] >= self.threat_threshold or np.isinf(self.cost_matrix[nx, ny]):
                    continue
                neighbors.append((nx, ny))
        return neighbors

    def transition_cost(self, s1: Tuple[int, int], s2: Tuple[int, int]) -> float:
        step_dist = math.sqrt(2) if (s1[0] != s2[0] and s1[1] != s2[1]) else 1.0
        # Average threat multiplier between cell step transitions
        avg_multiplier = (self.cost_matrix[s1[0], s1[1]] + self.cost_matrix[s2[0], s2[1]]) / 2.0
        return step_dist * avg_multiplier

    def update_vertex(self, u: Tuple[int, int]):
        if u != self.goal:
            neighbors = self.get_neighbors(u)
            if neighbors:
                self.rhs[u] = min(self.transition_cost(u, s_prime) + self.get_g(s_prime) for s_prime in neighbors)
            else:
                self.rhs[u] = float('inf')
                
        if self.U.contains(u): 
            self.U.remove(u)
        if self.get_g(u) != self.get_rhs(u): 
            self.U.insert(u, self.calculate_key(u))

    def compute_shortest_path(self):
        while (self.U.top_key() < self.calculate_key(self.current_position) or 
               self.get_rhs(self.current_position) != self.get_g(self.current_position)):
            k_old = self.U.top_key()
            u, _ = self.U.pop() or (None, None)
            if u is None: 
                break
            
            self.nodes_expanded += 1
            if k_old < self.calculate_key(u):
                self.U.insert(u, self.calculate_key(u))
            elif self.get_g(u) > self.get_rhs(u):
                self.g[u] = self.get_rhs(u)
                for s_prime in self.get_neighbors(u): 
                    self.update_vertex(s_prime)
            else:
                self.g[u] = float('inf')
                self.update_vertex(u)
                for s_prime in self.get_neighbors(u): 
                    self.update_vertex(s_prime)

    def extract_path(self) -> List[Tuple[int, int]]:
        path = [self.current_position]
        curr = self.current_position
        visited = {curr}
        while curr != self.goal:
            best_next, min_cost = None, float('inf')
            for n in self.get_neighbors(curr):
                if n in visited: 
                    continue
                cost = self.transition_cost(curr, n) + self.get_g(n)
                if cost < min_cost:
                    min_cost, best_next = cost, n
            if best_next is None or min_cost == float('inf'): 
                return []
            path.append(best_next)
            curr = best_next
            visited.add(curr)
        return path


# ==============================================================================
# PIPELINE INTEGRATION FUNCTION
# ==============================================================================

def execute_pipeline(cost_matrix: np.ndarray, 
                     fuel_capacity: float, 
                     start_pos: Tuple[int, int] = (10, 10), 
                     goal_pos: Tuple[int, int] = (90, 90),
                     threat_threshold: float = 30.0,
                     visualize: bool = True) -> Dict[str, Any]:
    """
    Primary interface for external modules. Pass your teammate's cost matrix 
    and fuel limits straight into this function to calculate D* Lite routes.
    """
    start_time = time.perf_counter()
    
    # Initialize Engine components using external inputs
    planner = DStarLiteUAV(cost_matrix, start_pos, goal_pos, threat_threshold=threat_threshold)
    
    # Compute initial route
    path = planner.extract_path() if planner.compute_shortest_path() else planner.extract_path()
    
    # Calculate operational metrics
    total_cells_covered = len(path)
    total_fuel_consumed = 0.0
    success = False
    
    if total_cells_covered > 0:
        for i in range(total_cells_covered - 1):
            total_fuel_consumed += planner.transition_cost(path[i], path[i+1])
            
        # Hard Fuel Constraint Verification
        if total_fuel_consumed <= fuel_capacity:
            success = True

    runtime = time.perf_counter() - start_time
    
    metrics = {
        "success": success,
        "path": path,
        "total_cost": total_fuel_consumed,
        "fuel_consumed": total_fuel_consumed,
        "nodes_expanded": planner.nodes_expanded,
        "runtime_seconds": runtime
    }

    # Mission Summary Logging (Matched to Dijkstra Layout)
    print("\n" + "="*45)
    print("              MISSION SUMMARY (D*)")
    print("="*45)
    print(f"Total Cells Covered (Path Length): {total_cells_covered}")
    print(f"Total Fuel Consumed:               {metrics['fuel_consumed']:.2f} units / {fuel_capacity:.2f} max")
    print(f"Mission Success:                   {'SUCCESS' if metrics['success'] else 'FAILED'}")
    print("="*45)
    print(f"Total Nodes Expanded:              {metrics['nodes_expanded']}")
    print(f"Execution Runtime:                 {metrics['runtime_seconds']:.4f} seconds\n")

    # Matched Dynamic Visualization Style
    if visualize and metrics['success']:
        path_coords = np.array(metrics['path'])
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Consistent layout, colormap, orientation, and contrast elements
        cmap = ax.imshow(cost_matrix, cmap='YlOrRd', origin='upper', vmax=threat_threshold)
        cbar = fig.colorbar(cmap, ax=ax)
        cbar.set_label('Threat Risk Level', rotation=270, labelpad=15)
        
        ax.plot(path_coords[:, 1], path_coords[:, 0], color='cyan', linewidth=3, label="Optimal Route (D* Lite)")
        ax.scatter(start_pos[1], start_pos[0], color='lime', marker='^', s=150, edgecolors='black', label="Start")
        ax.scatter(goal_pos[1], goal_pos[0], color='magenta', marker='X', s=150, edgecolors='black', label="Goal")
        
        ax.set_title("UAV Threat-Aware Path Planning Optimization (D* Lite)", fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()
        
    return metrics


# ==============================================================================
# LOCAL TESTING SUITE (Ignored when imported by your teammate)
# ==============================================================================
if __name__ == "__main__":
    print("Running local D* Lite code verification test...")
    
    # Mocking external inputs from your teammate
    mock_cost_matrix = np.ones((100, 100)) 
    mock_cost_matrix[40:60, 40:60] = 45.0  # Dense radar obstacle threat block
    mock_fuel_input = 600.0                
    
    # Executing pipeline with identical test data layout
    execute_pipeline(cost_matrix=mock_cost_matrix, fuel_capacity=mock_fuel_input)