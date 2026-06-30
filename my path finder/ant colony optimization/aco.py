import time
import random
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any

class BattlefieldGrid:
    """Manages the 2D battlefield environment, movement dynamics, and constraints."""
    def __init__(self, cost_matrix: np.ndarray):
        self.matrix = cost_matrix
        self.height, self.width = cost_matrix.shape

    def is_valid_coordinate(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        neighbors = []
        # 8-directional offsets: (dx, dy, step_distance)
        directions = [
            (0, -1, 1.0), (0, 1, 1.0), (-1, 0, 1.0), (1, 0, 1.0),
            (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)
        ]
        for dx, dy, dist in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid_coordinate(nx, ny):
                neighbors.append((nx, ny, dist))
        return neighbors

    def calculate_step_cost(self, x2: int, y2: int, dist: float) -> float:
        # Movement Distance * Destination Cell Base Cost
        return dist * self.matrix[y2, x2]


class AntColonyRoutePlanner:
    """Executes heuristic-driven, pheromone-based threat and fuel-constrained path planning."""
    def __init__(self, 
                 grid: BattlefieldGrid, 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int],
                 num_ants: int = 30,
                 iterations: int = 50,
                 alpha: float = 1.0,
                 beta: float = 2.0,
                 rho: float = 0.1,
                 Q: float = 100.0,
                 fuel_capacity: float = 500.0,
                 max_path_length: int = 300,
                 threat_threshold: float = 30.0):
        
        self.grid = grid
        self.start = start
        self.goal = goal
        self.num_ants = num_ants
        self.iterations = iterations
        self.alpha = alpha  
        self.beta = beta    
        self.rho = rho      
        self.Q = Q          
        self.fuel_capacity = fuel_capacity
        self.max_path_length = max_path_length
        self.threat_threshold = threat_threshold
        
        self.pheromones = np.full((grid.height, grid.width), 1.0, dtype=float)
        self.best_path = None
        self.best_cost = float('inf')
        self.best_fuel_consumed = 0.0
        self.convergence_history = []

    def _get_heuristic(self, x: int, y: int, dist: float) -> float:
        cost = self.grid.calculate_step_cost(x, y, dist)
        return 1.0 / (cost + 1e-6)

    def _construct_ant_path(self) -> Tuple[List[Tuple[int, int]], float, bool]:
        path = [self.start]
        visited = {self.start}
        current_fuel = self.fuel_capacity
        total_cost = 0.0
        
        while path[-1] != self.goal:
            cx, cy = path[-1]
            neighbors = self.grid.get_neighbors(cx, cy)
            unvisited = [(nx, ny, dist) for nx, ny, dist in neighbors if (nx, ny) not in visited]
            
            if not unvisited:
                return path, total_cost, False 
            
            probabilities = []
            valid_candidates = []
            
            for nx, ny, dist in unvisited:
                # Dynamic Check: Abort if cell exceeds maximum allowed threat threshold
                if self.grid.matrix[ny, nx] >= self.threat_threshold or np.isinf(self.grid.matrix[ny, nx]):
                    continue 
                    
                step_cost = self.grid.calculate_step_cost(nx, ny, dist)
                
                # Hard Constraint: Reject branches that blow past our fuel limits
                if current_fuel - step_cost >= 0:
                    tau = self.pheromones[ny, nx] ** self.alpha
                    eta = self._get_heuristic(nx, ny, dist) ** self.beta
                    probabilities.append(tau * eta)
                    valid_candidates.append((nx, ny, step_cost))
            
            if not valid_candidates:
                return path, total_cost, False 
            
            prob_sum = sum(probabilities)
            if prob_sum > 0:
                probabilities = [p / prob_sum for p in probabilities]
            else:
                probabilities = [1.0 / len(valid_candidates)] * len(valid_candidates)
                
            chosen_idx = random.choices(range(len(valid_candidates)), weights=probabilities, k=1)[0]
            next_x, next_y, step_cost = valid_candidates[chosen_idx]
            
            path.append((next_x, next_y))
            visited.add((next_x, next_y))
            current_fuel -= step_cost
            total_cost += step_cost
            
            if len(path) > self.max_path_length:
                return path, total_cost, False
                
        return path, total_cost, True

    def optimize(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        for iteration in range(self.iterations):
            iteration_paths = []
            iteration_costs = []
            
            for _ in range(self.num_ants):
                path, cost, success = self._construct_ant_path()
                if success:
                    iteration_paths.append(path)
                    iteration_costs.append(cost)
            
            # Pheromone Evaporation
            self.pheromones *= (1.0 - self.rho)
            
            # Pheromone Accumulation Update
            for path, cost in zip(iteration_paths, iteration_costs):
                deposit = self.Q / cost
                for x, y in path:
                    self.pheromones[y, x] += deposit
            
            # Global Best Tracking
            if iteration_costs:
                min_iter_cost = min(iteration_costs)
                if min_iter_cost < self.best_cost:
                    self.best_cost = min_iter_cost
                    self.best_path = iteration_paths[iteration_costs.index(min_iter_cost)]
                    self.best_fuel_consumed = min_iter_cost
            
            self.convergence_history.append(self.best_cost if self.best_cost != float('inf') else None)
            
        runtime = time.perf_counter() - start_time
        
        success = self.best_path is not None
        total_cells_covered = len(self.best_path) if success else 0
        total_fuel_consumed = self.best_fuel_consumed if success else 0.0
        
        return {
            "success": success,
            "path": self.best_path if success else [],
            "total_cost": self.best_cost if success else 0.0,
            "fuel_consumed": total_fuel_consumed,
            "runtime_seconds": runtime,
            "convergence_history": self.convergence_history
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
    battlefield = BattlefieldGrid(cost_matrix)
    
    # Note: ACO uses (x, y) coordinates internally. 
    # Converting row/col parameters to x/y structure -> start_pos[1], start_pos[0]
    start_xy = (start_pos[1], start_pos[0])
    goal_xy = (goal_pos[1], goal_pos[0])
    
    planner = AntColonyRoutePlanner(
        grid=battlefield, 
        start=start_xy, 
        goal=goal_xy,
        num_ants=30, 
        iterations=50, 
        alpha=1.0, 
        beta=2.0, 
        rho=0.1, 
        Q=100.0,
        fuel_capacity=fuel_capacity, 
        max_path_length=400,
        threat_threshold=threat_threshold
    )
    
    # Run Routing Optimization
    metrics = planner.optimize()

    # Mission Summary Logging (Matched with Dijkstra output format)
    print("\n" + "="*45)
    print("              MISSION SUMMARY (ACO)")
    print("="*45)
    print(f"Total Cells Covered (Path Length): {len(metrics['path'])}")
    print(f"Total Fuel Consumed:               {metrics['fuel_consumed']:.2f} units / {fuel_capacity:.2f} max")
    print(f"Mission Success:                   {'SUCCESS' if metrics['success'] else 'FAILED'}")
    print("="*45)
    print(f"Execution Runtime:                 {metrics['runtime_seconds']:.4f} seconds\n")

    # Dynamic Visualization (Identical layout to Dijkstra suite)
    if visualize and metrics['success']:
        path_coords = np.array(metrics['path'])
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Displaying with origin='upper' to stay identical with Dijkstra matrix mapping
        cmap = ax.imshow(cost_matrix, cmap='YlOrRd', origin='upper', vmax=threat_threshold)
        cbar = fig.colorbar(cmap, ax=ax)
        cbar.set_label('Threat Risk Level', rotation=270, labelpad=15)
        
        # ACO path tracks (x, y), map x to plot-X (columns) and y to plot-Y (rows)
        ax.plot(path_coords[:, 0], path_coords[:, 1], color='cyan', linewidth=3, label="Optimal Route")
        ax.scatter(start_pos[1], start_pos[0], color='lime', marker='^', s=150, edgecolors='black', label="Start")
        ax.scatter(goal_pos[1], goal_pos[0], color='magenta', marker='X', s=150, edgecolors='black', label="Goal")
        
        ax.set_title("UAV Threat-Aware Path Planning Optimization (ACO)", fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()
        
    return metrics


# ==============================================================================
# LOCAL TESTING SUITE (Ignored when imported by your teammate)
# ==============================================================================
if __name__ == "__main__":
    print("Running local ACO code verification test...")
    
    # Mocking what your teammate will send you
    mock_cost_matrix = np.ones((100, 100)) 
    mock_cost_matrix[40:60, 40:60] = 45.0  # Put a massive threat block in the center
    mock_fuel_input = 600.0                # Input fuel capacity
    
    # Executing pipeline with identical defaults to Dijkstra's mock run
    execute_pipeline(cost_matrix=mock_cost_matrix, fuel_capacity=mock_fuel_input)