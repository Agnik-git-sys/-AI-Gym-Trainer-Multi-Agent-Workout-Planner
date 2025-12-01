# agents.py
# Full 6-agent workout pipeline with robust logging and developer-friendly debug traces.
# This file logs an external decision trace for debugging (NOT model internals).

from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
import os
import json
import datetime
import pathlib
import logging
from typing import Any, Dict, Optional

# ---------------------------
# Directories & paths
# ---------------------------
BASE_DIR = pathlib.Path.cwd()
MEMORY_DIR = BASE_DIR / "memory"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

WORKOUT_HISTORY_PATH = MEMORY_DIR / "workout_history.json"
DECISION_LOG_PATH = LOG_DIR / f"decision_trace_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LAST_RUN_OUTPUTS_PATH = LOG_DIR / "last_run_outputs.json"

# ---------------------------
# Logging setup (file + console)
# ---------------------------
logger = logging.getLogger("workout_pipeline")
logger.setLevel(logging.DEBUG)

# File handler (detailed debug)
fh = logging.FileHandler(DECISION_LOG_PATH, encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

# Console handler (info-level)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch_formatter = logging.Formatter("[%(levelname)s] %(message)s")
ch.setFormatter(ch_formatter)
logger.addHandler(ch)


def log_trace(message: str, level: str = "info") -> None:
    """
    Central logging helper. Use level 'debug', 'info', 'warning', 'error'.
    """
    if level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)


# ---------------------------
# JSON helpers (safe)
# ---------------------------
def write_json(path: pathlib.Path, data: Any) -> None:
    """Write JSON to file (overwrites)."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log_trace(f"Wrote JSON to {path}", "debug")
    except Exception as e:
        log_trace(f"Failed to write JSON to {path}: {e}", "error")


def append_json_list(path: pathlib.Path, entry: Any) -> None:
    """Append an entry to a JSON list file; create file if missing."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                arr = json.load(f)
                if not isinstance(arr, list):
                    log_trace(f"Existing file {path} is not a list — overwriting with a new list.", "warning")
                    arr = []
        else:
            arr = []
        arr.append(entry)
        write_json(path, arr)
        log_trace(f"Appended entry to {path}", "debug")
    except Exception as e:
        log_trace(f"Error appending to {path}: {e}", "error")


# ---------------------------
# Equipment DB loader & selector (tool)
# ---------------------------
def equipments_json_loader(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            log_trace(f"Loaded equipments DB from {path}", "debug")
            return data
    except FileNotFoundError:
        log_trace(f"Equipment DB not found at {path}. Returning empty DB.", "warning")
        return {}
    except json.JSONDecodeError as e:
        log_trace(f"Equipment DB JSON decode error at {path}: {e}", "error")
        return {}
    except Exception as e:
        log_trace(f"Unexpected error loading equipment DB: {e}", "error")
        return {}


def equipment_selector(muscle: Optional[str]) -> Dict[str, Any]:
    """
    Tool: Return equipment recommendations for a muscle.
    Returns dict with keys: status, muscle, required, alternatives
    """
    muscle_norm = (muscle or "").lower().strip()
    db = equipments_json_loader(str(DATA_DIR / "equipments_db.json"))
    log_trace(f"equipment_selector called for muscle='{muscle_norm}'", "debug")

    if not db or muscle_norm not in db:
        return {
            "status": "not_found",
            "muscle": muscle_norm,
            "required": ["Dumbbells", "Resistance Bands"],
            "alternatives": ["Bodyweight variations", "Household objects (water jugs)"]
        }

    record = db.get(muscle_norm, {})
    return {
        "status": "success",
        "muscle": muscle_norm,
        "required": record.get("required_equipment", []),
        "alternatives": record.get("alternatives", [])
    }


# ---------------------------
# Save workout history helper
# ---------------------------
def save_workout_history_record(record: Dict[str, Any]) -> None:
    """
    Save a workout history record to WORKOUT_HISTORY_PATH as a list.
    """
    if not isinstance(record, dict):
        log_trace("save_workout_history_record called with non-dict; skipping.", "warning")
        return
    append_json_list(WORKOUT_HISTORY_PATH, record)
    log_trace(f"Saved workout history for muscle='{record.get('muscle')}'", "info")


# ---------------------------
# Agent Definitions
# ---------------------------

# 1) Workout Decoder: collects 4 fields and outputs JSON (decoder_output)
workout_decoder_agent = Agent(
    name="workout_decoder",
    model="gemini-2.5-flash-lite",
    description="Collects 4 fields (muscle, goal, training_style, experience_level) and outputs JSON.",
    instruction="""
ROLE:
You are WorkoutDecoder. Collect EXACTLY these 4 fields from the user:
- muscle
- goal
- training_style
- experience_level

RULES:
- Ask ONLY for missing fields.
- Never repeat a field already provided.
- Once all fields are present, output ONLY the JSON with these keys and STOP.
- Do NOT produce workout plans or ask for equipment.
""",
    output_key="decoder_output"
)

# 2) Workout Planner: generates plan text from decoder_output (plan_output)
workout_planner_agent = Agent(
    name="workout_planner",
    model="gemini-2.5-flash-lite",
    description="Creates a 6-8 exercise workout plan based on decoder_output.",
    instruction="""
EXECUTION GATE:
Run only if decoder_output exists and contains all required fields:
- muscle, goal, training_style, experience_level

TASK:
Use the provided fields to create a workout containing 6-8 exercises.
For each exercise include:
- Name
- Sets x Reps (appropriate for goal)
- Rest
- Form tip (one cue)
- Why (brief)
OUTPUT:
Return only the workout plan as plain text (no JSON).
""",
    tools=[google_search],
    output_key="plan_output"
)

# 3) Equipment Agent: calls equipment_selector tool and returns equipment_output
equipment_agent = Agent(
    name="equipment_agent",
    model="gemini-2.5-flash-lite",
    description="Selects primary and alternative equipment for the target muscle.",
    instruction="""
EXECUTION GATE:
Run only if decoder_output exists with a 'muscle' value.

TASK:
Call the equipment_selector tool with decoder_output.muscle.
Return a short, bullet-style equipment recommendation (primary and alternatives).
Do not ask user questions.
""",
    tools=[equipment_selector],
    output_key="equipment_output"
)

# 4) Validator Agent: checks safety and volume, returns validated_workout
validator_agent = Agent(
    name="workout_validator",
    model="gemini-2.5-flash-lite",
    description="Validates and adjusts workout for safety/volume/experience level.",
    instruction="""
EXECUTION GATE:
Run only if plan_output exists (a workout plan from planner).

TASK:
- Verify the plan matches the user's experience level and goal.
- Flag or adjust exercises that seem unsafe for the declared experience level.
- Ensure total volume is reasonable (no excessive sets/reps).
- Output the corrected/validated workout plan as plain text.
""",
    output_key="validated_workout"
)

# 5) Memory Agent: prepares memory_output JSON (then Python saves it)
memory_agent = Agent(
    name="workout_memory",
    model="gemini-2.5-flash-lite",
    description="Prepares a JSON record of the workout for persistence.",
    instruction="""
EXECUTION GATE:
Run only if decoder_output and validated_workout both exist.

TASK:
Produce the following JSON object (exact keys):
{
  "muscle": decoder_output.muscle,
  "goal": decoder_output.goal,
  "training_style": decoder_output.training_style,
  "experience_level": decoder_output.experience_level,
  "workout": validated_workout
}
Output only the JSON (no extra text). Python will persist this.
""",
    output_key="memory_output"
)

# 6) Recommender Agent: gives recovery/nutrition/next-day suggestions
recommender_agent = Agent(
    name="workout_recommender",
    model="gemini-2.5-flash-lite",
    description="Gives nutrition, recovery and next-session recommendations based on validated workout.",
    instruction="""
EXECUTION GATE:
Run only if validated_workout exists.

TASK:
Provide 4-6 concise bullet points:
- Recovery advice
- Post-workout nutrition
- Warm-up & cool-down
- Supplement suggestions (optional)
- Next-day training suggestion
Output as short bullets (plain text).
""",
    output_key="recommendation_output"
)

# 7) Aggregator Agent: collects all outputs and emits a short bullet-point summary
aggregator_agent = Agent(
    name="workout_aggregator",
    model="gemini-2.5-flash-lite",
    description="Aggregates decoder_output, validated_workout, equipment_output, memory_output, recommendation_output into a concise bullet summary.",
    instruction="""
EXECUTION GATE:
Run only if all exist:
- decoder_output
- validated_workout
- equipment_output
- memory_output
- recommendation_output

TASK:
Produce a compact bullet-list summary exactly in this structure:

FINAL WORKOUT SUMMARY
- Muscle: {decoder_output.muscle}
- Goal: {decoder_output.goal}
- Style: {decoder_output.training_style}
- Level: {decoder_output.experience_level}

WORKOUT (validated):
- [each exercise as: Name — sets×reps — rest]

EQUIPMENT:
- Primary: ...
- Alternatives: ...

RECOMMENDATIONS:
- bullet 1
- bullet 2
- bullet 3

MEMORY:
- "Workout saved."

Output only bullet points, no JSON, no long paragraphs.
""",
    output_key="aggregated_output"
)

# ---------------------------
# Pipeline orchestration (strict)
# ---------------------------
parallel_processor = ParallelAgent(
    name="planner_equipment_parallel",
    sub_agents=[workout_planner_agent, equipment_agent]
)

root_agent = SequentialAgent(
    name="FullWorkoutPipeline",
    sub_agents=[
        workout_decoder_agent,       # 1. accept user input
        parallel_processor,          # 2. plan & equipment in parallel (require decoder_output)
        validator_agent,             # 3. validate (require plan_output)
        memory_agent,                # 4. prepare memory JSON (require validated_workout + decoder_output)
        recommender_agent,           # 5. recommendations (require validated_workout)
        aggregator_agent             # 6. final aggregated bullet summary (require all)
    ]
)


