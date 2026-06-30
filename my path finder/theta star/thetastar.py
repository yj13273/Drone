import time
import math
import heapq
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any

class BattlefieldPathPlanner:
    """
    UAV Routing framework using A* and Theta* with a customizable threat threshold.
    Operates on an externally provided cost matrix environment.
    """
    def __init__(self, cost_matrix: np.ndarray, threat_threshold: float):
        self.cost_matrix = cost_matrix
        self.height, self.width = cost_matrix.shape
        self.threat_threshold = threat_threshold  # Cells above this cost are blocked
        
        # 8-Directional movement offsets and kinematic weights
        self.movements = [
            (0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0),
            (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), 
            (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))
        ]

    def _euclidean_heuristic(self, node: Tuple[int, int], goal: Tuple[int, int]) -> float:
        return math.sqrt((node[0] - goal[0])**2 + (node[1] - goal[1])**2)

    def _is_valid(self, node: Tuple[int, int]) -> bool:
        x, y = node
        return 0 <= x < self.height and 0 <= y < self.width and self.cost_matrix[x, y] < self.threat_threshold and not np.isinf(self.cost_matrix[x, y])

    def bresenham_los_cost(self, start: Tuple[int, int], end: Tuple[int, int]) -> Tuple[bool, float]:
        """Checks straight-line visibility and calculates continuous path cost."""
        x0, y0 = start
        x1, y1 = end
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        total_cost = 0.0
        steps = 0
        curr_x, curr_y = x0, y0
        
        while True:
            if not self._is_valid((curr_x, curr_y)):
                return False, float('inf')
            
            total_cost += self.cost_matrix[curr_x, curr_y]
            steps += 1
            
            if curr_x == x1 and curr_y == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy
                
        actual_dist = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
        if steps > 0:
            total_cost = (total_cost / steps) * actual_dist
        return True, total_cost

    def plan_route(self, start: Tuple[int, int], goal: Tuple[int, int], fuel_capacity: float, use_theta_star: bool = True) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        if not self._is_valid(start) or not self._is_valid(goal):
            return {
                "success": False, 
                "path": [], 
                "total_cost": 0.0,
                "fuel_consumed": 0.0, 
                "nodes_expanded": 0,
                "los_optimizations": 0,
                "runtime_seconds": time.perf_counter() - start_time,
                "msg": "Mission Failed: Start/Goal in lethal threat zone."
            }

        # Open set elements: (f_score, (row, col))
        open_set = []
        heapq.heappush(open_set, (0.0, start))
        
        parents = {start: start}
        g_score = {start: 0.0}
        f_score = {start: self._euclidean_heuristic(start, goal)}
        explored_nodes = set()
        los_optimizations = 0
        success = False

        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                success = True
                break

            if current in explored_nodes:
                continue
            explored_nodes.add(current)

            for dx, dy, move_cost in self.movements:
                neighbor = (current[0] + dx, current[1] + dy)
                if not self._is_valid(neighbor) or neighbor in explored_nodes:
                    continue

                edge_cost = self.cost_matrix[neighbor] * move_cost
                
                if use_theta_star:
                    parent_node = parents[current]
                    has_los, los_cost = self.bresenham_los_cost(parent_node, neighbor)
                    if has_los and (g_score[parent_node] + los_cost < g_score[current] + edge_cost):
                        tentative_g = g_score[parent_node] + los_cost
                        tentative_parent = parent_node
                        is_optimized = True
                    else:
                        tentative_g = g_score[current] + edge_cost
                        tentative_parent = current
                        is_optimized = False
                else:
                    tentative_g = g_score[current] + edge_cost
                    tentative_parent = current
                    is_optimized = False

                # Hard Constraint: Reject paths exceeding fuel budget
                if tentative_g > fuel_capacity:
                    continue

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._euclidean_heuristic(neighbor, goal)
                    parents[neighbor] = tentative_parent
                    if is_optimized: 
                        los_optimizations += 1
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        runtime = time.perf_counter() - start_time
        
        # Path reconstruction
        path = []
        if success:
            curr = goal
            while curr != start:
                path.append(curr)
                curr = parents[curr]
            path.append(start)
            path.reverse()
            total_cost = g_score[goal]
        else:
            total_cost = 0.0

        return {
            "success": success,
            "path": path,
            "total_cost": total_cost,
            "fuel_consumed": total_cost,
            "nodes_expanded": len(explored_nodes),
            "los_optimizations": los_optimizations if use_theta_star else 0,
            "runtime_seconds": runtime,
            "msg": "Mission Success" if success else "No viable route within thresholds."
        }

# ==============================================================================
# PIPELINE INTEGRATION FUNCTION
# ==============================================================================

def execute_pipeline(cost_matrix: np.ndarray, 
                     fuel_capacity: float, 
                     start_pos: Tuple[int, int] = (5, 5), 
                     goal_pos: Tuple[int, int] = (90, 95),
                     threat_threshold: float = 120.0,
                     use_theta_star: bool = True,
                     visualize: bool = True) -> Dict[str, Any]:
    """
    Primary interface for external modules. Pass your teammate's cost matrix 
    and fuel limits straight into this function.
    """
    # Initialize optimization components
    planner = BattlefieldPathPlanner(cost_matrix, threat_threshold=threat_threshold)
    
    # Run Routing Optimization
    metrics = planner.plan_route(start_pos, goal_pos, fuel_capacity, use_theta_star=use_theta_star)
    algo_name = "THETA*" if use_theta_star else "A*"

    # Mission Summary Logging
    print("\n" + "="*45)
    print(f"            MISSION SUMMARY ({algo_name})")
    print("="*45)
    print(f"Total Cells Covered (Path Length): {len(metrics['path'])}")
    print(f"Total Fuel Consumed:               {metrics['fuel_consumed']:.2f} units / {fuel_capacity:.2f} max")
    print(f"Mission Success:                   {'SUCCESS' if metrics['success'] else 'FAILED'}")
    print(f"Line-of-Sight Optimizations:       {metrics.get('los_optimizations', 0)}")
    print("="*45)
    print(f"Total Nodes Expanded:              {metrics['nodes_expanded']}")
    print(f"Execution Runtime:                 {metrics['runtime_seconds']:.4f} seconds\n")

    # Dynamic Visualization
    if visualize and metrics['success']:
        path_coords = np.array(metrics['path'])
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Mirroring the layout style from the Dijkstra configuration
        cmap = ax.imshow(cost_matrix, cmap='YlOrRd', origin='upper', vmax=threat_threshold)
        cbar = fig.colorbar(cmap, ax=ax)
        cbar.set_label('Threat Risk Level', rotation=270, labelpad=15)
        
        ax.plot(path_coords[:, 1], path_coords[:, 0], color='cyan', linewidth=3, label=f"Optimal Route ({algo_name})")
        ax.scatter(start_pos[1], start_pos[0], color='lime', marker='^', s=150, edgecolors='black', label="Start")
        ax.scatter(goal_pos[1], goal_pos[0], color='magenta', marker='X', s=150, edgecolors='black', label="Goal")
        
        ax.set_title(f"UAV Threat-Aware {algo_name} Path Planning Optimization", fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()
        
    return metrics

# ==============================================================================
# LOCAL TESTING SUITE (Ignored when imported by your teammate)
# ==============================================================================
if __name__ == "__main__":
    print("Running local algorithm validation test...")
    
    # Mocking external matrix inputs
    mock_cost_matrix = np.ones((100, 100)) 
    # Create a threat bar in the grid middle
    mock_cost_matrix[40:60, 20:80] = 150.0  
    mock_fuel_input = 1500.0
    
    # Testing Theta* Pipeline execution
    execute_pipeline(
        cost_matrix=mock_cost_matrix, 
        fuel_capacity=mock_fuel_input,
        start_pos=(5, 5),
        goal_pos=(90, 95),
        threat_threshold=120.0,
        use_theta_star=True,
        visualize=True
    )