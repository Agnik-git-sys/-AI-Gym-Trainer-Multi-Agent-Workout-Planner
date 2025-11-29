🧠 AI Gym Trainer — Multi-Agent Workout Planner

A smart, adaptive multi-agent fitness system that generates personalised workout plans, optimises them using training science, and tracks your long-term progress. Built using LLM-powered agents, MCP tools, A2A communication, and session/state management.

🔥 Key Features

Workout Planner Agent – Generates exercises, sets, reps, RPE, warm-ups.
Optimizer Agent – Fixes exercise conflicts, prevents overtraining, applies fatigue rules.
Chart Agent – Produces volume, intensity, and muscle-distribution graphs.
Reflection Agent – Logs history, updates PRs, saves progress automatically.
A2A Protocol – Agents communicate to refine workouts.
MCP Tools – Exercise DB, volume calculator, training analysis.

Memory System – Session state + long-term memory JSON for personalised plans.

🛠 Tools
exercise_db_tool.py – Validated exercise library
volume_tool.py – Total volume & intensity calculations
analysis_tool.py – Smart workout optimisation engine

💾 Memory

session_state.py – Short-term state per session
long_term_memory.json – Persistent fitness history (PRs, weekly volume, restrictions)
