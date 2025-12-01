# 🏋️‍♂️ AI Multi‑Agent Workout Pipeline

A fully automated **6‑agent AI workout generation system** built using the **Google Agent Development Kit (ADK)**.  
This pipeline collects user workout intent, generates a workout plan, validates safety, selects equipment, saves memory, and outputs a final aggregated summary.

---

## 🚀 Features

### ✅ **1. Multi‑Agent Architecture (7 Linked Agents)**
- **Decoder Agent** → Extracts: muscle, goal, training style, experience level  
- **Planner Agent** → Builds a personalized 6–8 exercise workout  
- **Equipment Agent** → Suggests required & alternative equipment  
- **Validator Agent** → Checks safety, volume, and difficulty  
- **Memory Agent** → Saves workout history (JSON)  
- **Recommender Agent** → Recovery, nutrition, next‑day tips  
- **Aggregator Agent** → Produces final clean summary for the user  

---

## 🔄 Pipeline Flow

```
User Input
   ↓
Workout Decoder
   ↓
[Planner + Equipment Agents] (Parallel)
   ↓
Validator
   ↓
Memory Agent
   ↓
Recommender
   ↓
Aggregator → Final Output
```

---

## 🧠 Memory‑Aware Workout Creation

The system automatically reads your last **3 workouts** and avoids repeating exercises:

- Prevents overuse injuries  
- Adds variation  
- Feels like a real personal trainer learning your pattern  

---

## 🧰 Equipment Selector (Custom Tool)

The system loads a JSON equipment database:

```
muscle → required_equipment + alternatives
```

If no match is found, fallback options are provided (dumbbells, bands, bodyweight, household items).

---

## 📁 Project Structure

```
project/
│
├── agents.py
├── data/
│   └── equipments_db.json
├── memory/
│   └── workout_history.json
├── logs/
│   └── run_log.txt
└── README.md

Logs and Memory folder are not uploaded!

```

---

## 📝 How to Use

### **1. Install dependencies**
```bash
pip install google-adk
```

### **2. Run the pipeline**
```bash
adk run agents.py
```

The system will first display required input format.

Then you can give ANY casual input like:

```
chest workout, muscle growth, supersets, intermediate
```

---

## 📥 Example Output

```
FINAL WORKOUT SUMMARY
- Muscle: chest
- Goal: muscle growth
- Experience: intermediate

WORKOUT:
- Barbell Bench Press — 4×8 — 90s
- Incline DB Press — 3×10 — 75s
...

EQUIPMENT:
- Primary: bench, dumbbells, barbell
- Alternatives: resistance bands, push‑up variations

RECOMMENDATIONS:
- Increase protein intake post‑workout
- Stretch chest + triceps 10 minutes
...
```

---

## 📌 Why This System Is Special

- Full multi‑agent pipeline  
- Parallel agent execution  
- Memory‑aware plan creation  
- Logging for debugging  
- Clean modular architecture  
- Extensible for mobile apps / web UI / APIs  

---

## 📌 Future Improvements
- Add weekly periodisation agent  
- Add form‑correction agent using computer vision  
- Add strength‑tracking memory  
- Add user profile system  

---

## 🤝 Contributing

Pull requests are welcome!  
---

## 📄 License
MIT License

