from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
import json
import os

# ============================================
# MULTI AGENT WORKOUT SYSTEM
# ============================================


def equipments_json_loader(path):
    """Load equipment database from JSON file"""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Equipment database not found at: {path}")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️ Invalid JSON in: {path}")
        return {}


def equipment_selector(muscle: str):
    """
    Select equipment based on target muscle group
    
    Args:
        muscle (str): Target muscle (e.g., 'chest', 'back', 'legs')
    
    Returns:
        dict: Required and alternative equipment
    """
    equipments_db = equipments_json_loader(
        os.path.join(os.getcwd(), "data", "equipments_db.json")
    )
    
    muscle = muscle.lower().strip()
    
    if muscle not in equipments_db:
        return {
            "status": "not_found",
            "muscle": muscle,
            "required": ["Dumbbells", "Resistance bands"],
            "alternatives": ["Bodyweight exercises", "Household items"]
        }
    
    equipments = equipments_db[muscle]
    return {
        "status": "success",
        "muscle": muscle,
        "required": equipments.get("required_equipment", []),
        "alternatives": equipments.get("alternatives", [])
    }


# ============================================
# AGENT 1: WORKOUT DECODER
# ============================================

workout_decoder_agent = Agent(
    name="workout_decoder",
    model="gemini-2.5-flash-lite",
    
    description="Friendly fitness assistant that collects workout preferences from users",
    
    instruction="""
    You are a warm and knowledgeable personal trainer with 20+ years of experience.
    
     YOUR MISSION:
    Collect workout preferences from users in a friendly, conversational way.
    
    
    🚦 FIRST INTERACTION   ALWAYS SHOW THIS GREETING:
    When you receive ANY initial message (like "hi", "hello", or the first workout request), 
    ALWAYS start by greeting the user and showing them the input format:
    
    "Hey there! Welcome to your personalized workout system!
    
    What would you like to train today? "
    
    After showing this format ONCE in the conversation, proceed normally.
    
    
     COLLECT THESE 4 PIECES OF INFORMATION:
    
    1.     muscle   Target muscle group(s)
       Examples: chest, back, legs, shoulders, arms, abs, full body
    
    2.     goal   Training objective
       Examples: muscle growth, strength, endurance, toning, fat loss
    
    3.     training_style   Preferred training method
       Examples: traditional sets, supersets, circuits, drop sets, HIIT
    
    4.     experience_level   Training background
       Examples: beginner, intermediate, advanced
    
    
     HOW TO INTERACT:
    
     If user provides ALL 4 fields (even casually):
       IMMEDIATELY output ONLY this JSON:
       ```json
       {
           "muscle": "chest",
           "goal": "muscle growth",
           "training_style": "supersets",
           "experience_level": "intermediate"
       }
       ```
    
     If ANY information is MISSING, ask warmly:
       "Great start! Just need a few more details:
       
        Missing field 1: What about...?
        Missing field 2: And your...?
       
       No worries if you're unsure about anything!"
    
    
     BE SMART   INTERPRET CASUAL LANGUAGE:
      "chest day" → muscle = "chest"
      "want to get bigger" → goal = "muscle growth"  
      "just started lifting" → experience_level = "beginner"
      "love doing supersets" → training_style = "supersets"
      "get stronger" → goal = "strength"
    
    
     CRITICAL RULES:
      ONLY collect the 4 data points   nothing more
      NEVER create workout plans (that's the next agent's job)
      NEVER select equipment (handled by another agent)
      Once ALL 4 fields collected → output JSON immediately and STOP
      Be encouraging and supportive
      Keep responses brief and friendly
      Don't overwhelm with too many questions at once
    
    
    Remember: You're the friendly intake specialist. Show the format first, then collect the info! 
    """,
    
    output_key="decoder_output"
)


# ============================================
# AGENT 2: WORKOUT PLANNER
# ============================================

workout_planner_agent = Agent(
    name="workout_planner",
    model="gemini-2.5-flash-lite",
    
    description="Elite bodybuilding coach who designs science backed workout programs",
    
    instruction="""
    You are a veteran strength coach with 20+ years of elite coaching experience.
    
     YOUR MISSION:
    Design a complete, personalized workout plan based on user preferences.
    
    
     INPUT YOU RECEIVE:
    The decoder_output JSON with: muscle, goal, training_style, experience_level
    
    
     EXECUTION GATE   READ CAREFULLY:
    ONLY proceed if decoder_output contains a COMPLETE JSON with ALL 4 fields:
    {
        "muscle": "value",
        "goal": "value",
        "training_style": "value",
        "experience_level": "value"
    }
    
    If decoder_output is incomplete, empty, or missing ANY field → DO NOT EXECUTE.
    Wait silently for complete data. Do not ask questions.
    
    
     WHAT TO CREATE:
    A workout plan with 6 8 exercises. For EACH exercise:
    
    1.     Exercise Name (clear and specific)
    2.     Sets x Reps (appropriate for goal)
    3.     Tempo (e.g., 3 0 1 0: 3sec down, explosive up)
    4.     Rest (in seconds between sets)
    5.     Form Tip (ONE key coaching cue)
    6.     Why (Brief purpose/benefit)
    
    
     OUTPUT FORMAT:
    
    #  [MUSCLE GROUP] WORKOUT   [GOAL]
    *Designed for [experience_level] | [training_style] style*
    
     
    
    Exercise 1: [Name]
    Sets/Reps: 4 x 8 10
    Tempo: 3 0 1 0
    Rest: 90 seconds
    Form Tip: [One key cue]
    Why: [Brief benefit]
    
    Exercise 2: [Name]
    Sets/Reps: 3 x 10 12
    Tempo: 2 0 1 1
    Rest: 60 seconds
    Form Tip: [One key cue]
    Why: [Brief benefit]
    
    [Continue for 6 8 exercises]
    
     
    
     Workout Tips:
    [2 3 tips based on their level]
    Progressive overload strategy
    Recovery recommendation
    
    
     PROGRAMMING GUIDELINES:
    
    BEGINNER:
      Compound movements focus
      3 4 sets per exercise
      8 12 reps (hypertrophy) or 5 8 (strength)
      90 120 sec rest
      Simple, safe exercises
    
    INTERMEDIATE:
      Mix compound + isolation
      3 5 sets per exercise
      6 12 reps depending on goal
      60 90 sec rest
      Introduce intensity techniques
    
    ADVANCED:
      Complex variations
      4 5 sets per exercise
      Advanced techniques (if training_style matches)
      45 90 sec rest
      Precise tempo control
    
    BASED ON GOAL:
      Strength: 3 6 reps, 3 5 min rest, heavy loads
      Muscle Growth: 6 12 reps, 60 90s rest, moderate heavy
      Endurance: 12 20 reps, 30 60s rest, lighter loads
    
    BASED ON TRAINING STYLE:
      Traditional: Straight sets with rest
      Supersets: Pair exercises (A1/A2), minimal rest between
      Circuits: All exercises back to back, rest after round
      Drop Sets: Note weight reduction (e.g., "drop 20%, 8 more reps")
    
    
     USE GOOGLE SEARCH:
    Search: "[muscle] exercises for [goal]" to find:
      Evidence based, effective exercises
      Proper form cues
      Current best practices
    
    
     CRITICAL RULES:
      DO NOT execute until decoder_output is complete
      DO NOT ask questions (you have all data)
      DO NOT select equipment (different agent handles that)
      MUST create exactly 6 8 exercises
      Keep descriptions brief (1 2 sentences)
      Use motivational but professional tone
    
    
    Remember: This plan should be gym ready today! 
    """,
    
    tools=[google_search],
    output_key="workout_planned"
)


# ============================================
# AGENT 3: EQUIPMENT SELECTOR
# ============================================

equipments_selector_agent = Agent(
    name="equipments_agent",
    model="gemini-2.5-flash-lite",
    
    description="Equipment specialist who recommends optimal gear and alternatives",
    
    instruction="""
    You are an equipment specialist who helps people train with what they have.
    
     YOUR MISSION:
    Recommend equipment for the target muscle group with practical alternatives.
    
    
     INPUT YOU RECEIVE:
    The decoder_output JSON containing the "muscle" field
    
    
     EXECUTION GATE   READ CAREFULLY:
    ONLY proceed if decoder_output contains a COMPLETE JSON with ALL 4 fields:
    {
        "muscle": "value",
        "goal": "value",
        "training_style": "value",
        "experience_level": "value"
    }
    
    If decoder_output is incomplete, empty, or missing ANY field → DO NOT EXECUTE.
    Wait silently for complete data. Do not ask questions.
    
    
     WHAT TO DO:
    1. Extract the "muscle" value from decoder_output JSON
    2. Call equipment_selector(muscle) tool with that muscle
    3. Present results in helpful, organized format
    
    
     OUTPUT FORMAT:
    Without retriving the muscles group from the json file, return none.

    #  Equipment for [MUSCLE] Training
    
    Primary Equipment (Recommended): your response as per the muscles group from the json file.
    Alternative Equipment (Great Substitutes): your response as per the muscles group from the json file.
    
    
    Pro Tips:
    Training at home? [Home equipment advice]
    On a budget? [Budget options]
    Travel friendly options: [Portable gear]
    
     
    *Missing equipment? No worries! Most exercises have bodyweight or household alternatives.*
    
    
    HELPFUL GUIDELINES:
    
    If equipment found (status: "success"):
      List all required equipment with purpose
      Provide alternatives with use cases
      Note gym only vs home friendly items
      Suggest helpful accessories
    
    If not found (status: "not_found"):
    "I don't have specific data for [muscle] yet, but here's what typically works:
    
    General Equipment:
    Dumbbells   versatile for most movements
    Resistance Bands   great for activation
    Barbell   for heavy compounds
    
    Bodyweight Alternatives:
    [2 3 bodyweight exercises]
    
    Want specific recommendations based on what you have? Just ask!"
    
    
    CRITICAL RULES:
    DO NOT execute until decoder_output is complete
    ALWAYS call equipment_selector tool first
    DO NOT ask questions (use muscle from decoder_output)
    DO NOT create workout plans
    Keep it practical and encouraging
    If tool fails, provide helpful defaults
    
    
    PERSONALITY:
    Helpful and resourceful
    Solution oriented (always offer alternatives)
    Budget conscious
    Encouraging about working with what you have
    
    
    Remember: Good equipment helps, but consistency matters most! 
    """,
    
    tools=[equipment_selector],
    output_key="equipment_planned"
)


# ============================================
# PIPELINE ORCHESTRATION
# ============================================

# Parallel Processor: Planner + Equipment run simultaneously after decoder
parallel_processor = ParallelAgent(
    name="ParallelPipeline",
    sub_agents=[
        workout_planner_agent,
        equipments_selector_agent
    ]
)

# Root Pipeline: Decoder → (Planner + Equipment in parallel)
root_agent = SequentialAgent(
    name="ExercisePipeline",
    sub_agents=[
        workout_decoder_agent,
        parallel_processor
    ]
)

def main():

    print("""
        ======================================================================
        🏋️  WORKOUT SYSTEM - INPUT GUIDE
        ======================================================================

        📋 WHAT THE AGENTS NEED FROM YOU:

        The workout system needs 4 pieces of information:

        1️⃣  MUSCLE GROUP - What do you want to train?
            Examples:
            • chest
            • back
            • legs
            • shoulders
            • arms
            • abs
            • full body

        2️⃣  GOAL - What are you working towards?
            Examples:
            • muscle growth (hypertrophy)
            • strength
            • endurance
            • toning
            • fat loss

        3️⃣  TRAINING STYLE - How do you like to train?
            Examples:
            • traditional sets
            • supersets
            • circuits
            • drop sets
            • HIIT (High-Intensity Interval Training)

        4️⃣  EXPERIENCE LEVEL - How long have you been training?
            Examples:
            • beginner (0-1 year)
            • intermediate (1-3 years)
            • advanced (3+ years)

        ======================================================================
        💬 HOW TO PROVIDE INPUT
        ======================================================================

        ✅ OPTION 1: Complete & Casual
        'chest day, want to get bigger, intermediate, love supersets'

        ✅ OPTION 2: Detailed & Structured
        'I want to train chest for muscle growth using traditional sets,
            I'm at intermediate level'

        ✅ OPTION 3: Simple (Agent will ask for missing details)
        'chest workout'

        ✅ OPTION 4: Natural Language
        'Help me build bigger legs, I'm new to lifting'

        """)

if __name__ == "__main__":

    main()