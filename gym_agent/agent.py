from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search   
import os, json, pathlib, datetime, logging
from typing import Any, Dict, Optional

# ---------------------------------------------------------
# PATHS & DIRECTORIES
# ---------------------------------------------------------
BASE = pathlib.Path.cwd()
DATA = BASE / "data"
LOGS = BASE / "logs"
MEMORY = BASE / "memory"

DATA.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)
MEMORY.mkdir(exist_ok=True)

HISTORY_FILE = MEMORY / "workout_history.json"

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------
logger = logging.getLogger("workout")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOGS / "run_log.txt")
fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(fh)


# ---------------------------------------------------------
# JSON HELPERS
# ---------------------------------------------------------
def load_json(path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def append_history(entry):
    hist = load_json(HISTORY_FILE)
    hist.append(entry)
    save_json(HISTORY_FILE, hist)


# ---------------------------------------------------------
# EQUIPMENT SELECTOR TOOL (callable)
# ---------------------------------------------------------
def equipment_selector(muscle: str):
    db_path = DATA / "equipments_db.json"
    try:
        db = json.load(open(db_path, "r", encoding="utf-8"))
    except:
        db = {}

    m = (muscle or "").lower().strip()

    if m not in db:
        return {
            "status": "not_found",
            "muscle": m,
            "required": ["Dumbbells", "Resistance Bands"],
            "alternatives": ["Bodyweight variations"]
        }

    rec = db[m]
    return {
        "status": "success",
        "muscle": m,
        "required": rec.get("required_equipment", []),
        "alternatives": rec.get("alternatives", [])
    }


# ---------------------------------------------------------
# MEMORY-AWARE EXERCISE FILTER
# Prevent repeating exercises from last 3 workouts
# ---------------------------------------------------------
def get_recent_exercises():
    hist = load_json(HISTORY_FILE)
    recent = hist[-3:]          # last 3 workouts
    exercises = []

    for entry in recent:
        w = entry.get("workout", "")
        for line in w.split("\n"):
            if "Exercise" in line or "-" in line:
                exercises.append(line.lower())

    return exercises


# ---------------------------------------------------------
# AGENTS
# ---------------------------------------------------------

# 1) DECODER
workout_decoder_agent = Agent(
    name="workout_decoder",
    model="gemini-2.5-flash-lite",
    instruction="""
You are WorkoutDecoder. Extract exactly 4 fields:
- muscle
- goal
- training_style
- experience_level

Ask ONLY for missing fields.
When all 4 are available, output ONLY JSON:
{
  "muscle": "...",
  "goal": "...",
  "training_style": "...",
  "experience_level": "..."
}
""",
    output_key="decoder_output"
)

# 2) PLANNER (now memory-aware)
workout_planner_agent = Agent(
    name="workout_planner",
    model="gemini-2.5-flash-lite",
    tools=[google_search],
    instruction=f"""
You are WorkoutPlanner, an elite bodybuilding coach.

IMPORTANT:
- Before generating exercises, READ THIS LIST of exercises to AVOID:
{get_recent_exercises()}

Never repeat these.

TASK:
Create a 6,8 exercise plan using:
- Name
- Sets x Reps
- Rest
- Tip
- Why

No JSON. Only clean workout text.
""",
    output_key="plan_output"
)

# 3) EQUIPMENT AGENT
equipment_agent = Agent(
    name="equipment_agent",
    model="gemini-2.5-flash-lite",
    tools=[equipment_selector],
    instruction="""
Use equipment_selector(muscle) from decoder_output.
Return primary + alternative equipment in bullet points.
""",
    output_key="equipment_output"
)

# 4) VALIDATOR
validator_agent = Agent(
    name="validator",
    model="gemini-2.5-flash-lite",
    instruction="""
Validate the workout:
- Volume reasonable
- Difficulty matches experience level
- Remove unsafe movements

Return corrected workout as text only.
""",
    output_key="validated_workout"
)

# 5) MEMORY AGENT
memory_agent = Agent(
    name="workout_memory",
    model="gemini-2.5-flash-lite",
    instruction="""
Combine decoder_output + validated_workout into this JSON:

{
  "muscle": "...",
  "goal": "...",
  "training_style": "...",
  "experience_level": "...",
  "workout": "validated_workout"
}

Output ONLY this JSON.
""",
    output_key="memory_output"
)

# 6) RECOMMENDER
recommender_agent = Agent(
    name="recommender",
    model="gemini-2.5-flash-lite",
    instruction="""
Provide 4–6 bullet points:
- Recovery
- Nutrition
- Warm-up
- Supplements (optional)
- Next-day plan
""",
    output_key="recommendation_output"
)

# 7) AGGREGATOR
aggregator_agent = Agent(
    name="aggregator",
    model="gemini-2.5-flash-lite",
    instruction="""
Produce ONLY the final combined bullet summary:

FINAL WORKOUT SUMMARY
- Muscle: ...
- Goal: ...
- Experience: ...
WORKOUT:
- ...
EQUIPMENT:
- ...
RECOMMENDATIONS:
- ...

No extra text. No JSON.
""",
    output_key="aggregated_output"
)

# ---------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------
pipeline = SequentialAgent(
    name="WorkoutPipeline",
    sub_agents=[
        workout_decoder_agent,
        ParallelAgent(
            name="parallel_block",
            sub_agents=[workout_planner_agent, equipment_agent]
        ),
        validator_agent,
        memory_agent,
        recommender_agent,
        aggregator_agent
    ]
)

# Export for ADK
root_agent = pipeline

# Show required input format on load
def show_format():
    print("\n================ INPUT FORMAT ================\n")
    print("Give me 4 fields in ANY wording:")
    print("- Muscle group")
    print("- Goal")
    print("- Training style")
    print("- Experience level")
    print("\nExample:")
    print("   chest day, muscle growth, supersets, intermediate\n")
    print("===============================================\n")

show_format()
