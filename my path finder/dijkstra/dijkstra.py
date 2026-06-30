import time
import math
import heapq
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any

class BattlefieldGrid:
    """Manages the 2D battlefield environment, movement dynamics, and constraints."""
    def __init__(self, cost_matrix: np.ndarray, threat_threshold: float):
        self.cost_matrix = cost_matrix
        self.rows, self.cols = cost_matrix.shape
        self.threat_threshold = threat_threshold
        
        # 8-directional movements: (dx, dy, distance_multiplier)
        self.movements = [
            (0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0),
            (1, 1, math.sqrt(2)), (-1, 1, math.sqrt(2)), 
            (1, -1, math.sqrt(2)), (-1, -1, math.sqrt(2))
        ]

    def is_valid(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int, float]]:
        neighbors = []
        for dr, dc, move_mult in self.movements:
            nr, nc = r + dr, c + dc
            if self.is_valid(nr, nc):
                cell_cost = self.cost_matrix[nr, nc]
                
                # Dynamic Check: Abort if cell exceeds the maximum allowed threat threshold
                if cell_cost >= self.threat_threshold or np.isinf(cell_cost):
                    continue
                
                transition_cost = move_mult * cell_cost
                neighbors.append((nr, nc, transition_cost))
        return neighbors

class ThreatAwarePathPlanner:
    """Executes fuel and threat-constrained Dijkstra path planning."""
    def __init__(self, grid: BattlefieldGrid):
        self.grid = grid

    def plan_dijkstra(self, start: Tuple[int, int], goal: Tuple[int, int], fuel_capacity: float) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        # Priority Queue: (accumulated_cost, row, col)
        pq = [(0.0, start[0], start[1])]
        
        distances = np.full((self.grid.rows, self.grid.cols), np.inf)
        distances[start[0], start[1]] = 0.0
        
        parent_map = {}
        visited = set()
        nodes_expanded = 0
        success = False

        while pq:
            curr_cost, r, c = heapq.heappop(pq)
            
            if curr_cost > distances[r, c] or (r, c) in visited:
                continue
            
            visited.add((r, c))
            nodes_expanded += 1

            if (r, c) == goal:
                success = True
                break

            for nr, nc, transition_cost in self.grid.get_neighbors(r, c):
                next_cost = curr_cost + transition_cost
                
                # Hard Constraint: Reject paths exceeding fuel budget
                if next_cost > fuel_capacity:
                    continue
                
                if next_cost < distances[nr, nc]:
                    distances[nr, nc] = next_cost
                    parent_map[(nr, nc)] = (r, c)
                    heapq.heappush(pq, (next_cost, nr, nc))

        runtime = time.perf_counter() - start_time
        
        # Path reconstruction
        path = []
        if success:
            curr = goal
            while curr != start:
                path.append(curr)
                curr = parent_map[curr]
            path.append(start)
            path.reverse()
            total_cost = distances[goal[0], goal[1]]
        else:
            total_cost = 0.0

        return {
            "success": success,
            "path": path,
            "total_cost": total_cost,
            "fuel_consumed": total_cost,
            "nodes_expanded": nodes_expanded,
            "runtime_seconds": runtime
        }

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
    and fuel limits straight into this function.
    """
    # Initialize Engine components using external inputs
    battlefield = BattlefieldGrid(cost_matrix, threat_threshold=threat_threshold)
    planner = ThreatAwarePathPlanner(battlefield)
    
    # Run Routing Optimization
    metrics = planner.plan_dijkstra(start_pos, goal_pos, fuel_capacity)

    # Mission Summary Logging
    print("\n" + "="*45)
    print("              MISSION SUMMARY")
    print("="*45)
    print(f"Total Cells Covered (Path Length): {len(metrics['path'])}")
    print(f"Total Fuel Consumed:               {metrics['fuel_consumed']:.2f} units / {fuel_capacity:.2f} max")
    print(f"Mission Success:                   {'SUCCESS' if metrics['success'] else 'FAILED'}")
    print("="*45)
    print(f"Total Nodes Expanded:              {metrics['nodes_expanded']}")
    print(f"Execution Runtime:                 {metrics['runtime_seconds']:.4f} seconds\n")

    # Dynamic Visualization
    if visualize and metrics['success']:
        path_coords = np.array(metrics['path'])
        fig, ax = plt.subplots(figsize=(10, 8))
        
        cmap = ax.imshow(cost_matrix, cmap='YlOrRd', origin='upper', vmax=threat_threshold)
        cbar = fig.colorbar(cmap, ax=ax)
        cbar.set_label('Threat Risk Level', rotation=270, labelpad=15)
        
        ax.plot(path_coords[:, 1], path_coords[:, 0], color='cyan', linewidth=3, label="Optimal Route")
        ax.scatter(start_pos[1], start_pos[0], color='lime', marker='^', s=150, edgecolors='black', label="Start")
        ax.scatter(goal_pos[1], goal_pos[0], color='magenta', marker='X', s=150, edgecolors='black', label="Goal")
        
        ax.set_title("UAV Threat-Aware Path Planning Optimization", fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()
        
    return metrics

# ==============================================================================
# LOCAL TESTING SUITE (Ignored when imported by your teammate)
# ==============================================================================
if __name__ == "__main__":
    print("Running local code verification test...")
    
    # Mocking what your teammate will send you
    mock_cost_matrix = np.ones((100, 100)) 
    mock_cost_matrix[40:60, 40:60] = 45.0  # Put a massive threat block in the center
    mock_fuel_input = 600.0                # Input fuel capacity
    
    # Executing the pipeline with mock data
    execute_pipeline(cost_matrix=mock_cost_matrix, fuel_capacity=mock_fuel_input)