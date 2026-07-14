# Swarm Monte Carlo simulation

This independent Python module compares drone-swarm route strategies under variable air-defence conditions. It does not require third-party packages or change the existing project pipeline.

Run from the repository root:

```powershell
python swarm_monte_carlo/swarm_simulator.py --sizes 10,20,40,80 --runs 5000
```

To change initial threat variables, copy `scenario.example.json` to a new file, adjust its values, then run:

```powershell
python swarm_monte_carlo/swarm_simulator.py --config my_scenario.json
```

The command writes `swarm_simulation_results.csv` and `swarm_simulation_results.json` to `swarm_monte_carlo/output` by default.

