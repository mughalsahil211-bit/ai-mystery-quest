import os, json, random, uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()
BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
CASES_FILE = DATA / "cases.json"
HISTORY_FILE = DATA / "history.json"
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")

DEMO_CASES = [
 {
  "id":"demo-library","title":"The Midnight Manuscript","category":"Theft","difficulty":"Easy",
  "story":"At 9:15 PM, a rare handwritten manuscript vanished from the locked reading room of Bellweather Library. The room's alarm was briefly disabled, but the door shows no damage. Four people were still inside the building.",
  "victim":"The library's collection",
  "suspects":[
   {"id":"s1","name":"Evelyn Hart","role":"Head Librarian","background":"Has managed the archive for twelve years and knows its security system.","motive":"Wanted to sell the manuscript to cover a large personal debt.","alibi":"Says she was cataloguing returns in the west office."},
   {"id":"s2","name":"Marcus Reed","role":"Night Guard","background":"Former locksmith who patrols the building after closing.","motive":"Was recently reprimanded and feared losing his job.","alibi":"Claims he was checking the front entrance at 9:15 PM."},
   {"id":"s3","name":"Dr. Nina Cole","role":"Visiting Historian","background":"An expert on the manuscript's author who had requested private access.","motive":"Wanted the manuscript for an unpublished research project.","alibi":"Says she was in the staff kitchen making tea."},
   {"id":"s4","name":"Owen Price","role":"Restoration Assistant","background":"Works in the basement conservation lab.","motive":"Believed the library ignored his restoration work.","alibi":"Says he was cleaning brushes in the lab."}
  ],
  "evidence":[
   {"id":"e1","title":"Disabled alarm log","detail":"The alarm was disabled using a staff override code at 9:08 PM.","connects":"Evelyn Hart","hint":"Only senior staff have access to the override code."},
   {"id":"e2","title":"Dust-free service key","detail":"A service key was found in Evelyn's cardigan pocket. It fits the reading-room side cabinet.","connects":"Evelyn Hart","hint":"Consider who had access to the service key."},
   {"id":"e3","title":"Guard's patrol sheet","detail":"The sheet shows Marcus signed the front entrance check at 9:14 PM.","connects":"Marcus Reed","hint":"The timing supports Marcus's stated location."},
   {"id":"e4","title":"Tea-room receipt","detail":"The kettle timer recorded Nina's tea cycle at 9:13 PM.","connects":"Dr. Nina Cole","hint":"This independently supports Nina's alibi."},
   {"id":"e5","title":"Restoration solvent","detail":"Solvent on Owen's gloves matches the lab's cleaning station, not the reading room.","connects":"Owen Price","hint":"This clue is consistent with Owen's account."}
  ],
  "puzzles":[
   {"id":"p1","question":"The alarm override was used at 9:08 PM. The manuscript disappeared at 9:15 PM. Which suspect's role gives them routine access to the override code?","answer":"evelyn","accepted":["evelyn","evelyn hart","librarian"],"explanation":"Evelyn is the head librarian and the evidence log identifies a staff override. The service key found in her pocket provides a second connection.","points":100}
  ],
  "solution":"Evelyn Hart","solution_explanation":"Evelyn had both the access and opportunity. The alarm log shows a staff override shortly before the theft, and the service key found in her cardigan links her to the reading-room cabinet. The other suspects have independently supported alibis or evidence consistent with their accounts."
 },
 {
  "id":"demo-greenhouse","title":"Whispers in the Greenhouse","category":"Suspicious Incident","difficulty":"Medium",
  "story":"A rare blue orchid was found destroyed at the university greenhouse just before its judging. The greenhouse was locked overnight. A muddy footprint, a broken timer, and a contradictory watering log may reveal what happened.",
  "victim":"The university's blue orchid",
  "suspects":[
   {"id":"s1","name":"Leo Grant","role":"Greenhouse Technician","background":"Maintains irrigation and climate controls.","motive":"His own entry was rejected from the competition.","alibi":"Says he left at 7:00 PM."},
   {"id":"s2","name":"Priya Shah","role":"Botany Student","background":"Has studied the orchid for two semesters.","motive":"Wanted the judging postponed after her rival's entry became the favourite.","alibi":"Says she was studying in the library."},
   {"id":"s3","name":"Arthur Wells","role":"Competition Judge","background":"A retired horticulturist with access to the greenhouse.","motive":"Had publicly criticised the orchid's breeding method.","alibi":"Says he inspected the greenhouse at 8:30 PM."}
  ],
  "evidence":[
   {"id":"e1","title":"Timer override","detail":"The irrigation timer was manually stopped at 8:42 PM using the technician maintenance panel.","connects":"Leo Grant","hint":"The panel is not available to ordinary visitors."},
   {"id":"e2","title":"Library entry record","detail":"Priya's student card was scanned at the library at 8:39 PM and 9:06 PM.","connects":"Priya Shah","hint":"The record supports Priya's stated location."},
   {"id":"e3","title":"Judge's inspection note","detail":"Arthur's signed inspection sheet places him at the greenhouse at 8:30 PM, before the timer override.","connects":"Arthur Wells","hint":"Being present earlier is not proof of causing the damage."}
  ],
  "puzzles":[
   {"id":"p1","question":"Which piece of evidence most directly identifies who could stop the irrigation timer? Enter the suspect's first name.","answer":"leo","accepted":["leo","leo grant"],"explanation":"The maintenance panel requires technician access, pointing to Leo. The timing and his motive strengthen the case, though the clue is not proof by itself.","points":100}
  ],
  "solution":"Leo Grant","solution_explanation":"Leo's technician access allowed the manual timer override at 8:42 PM. Priya's library scans support her alibi, while Arthur's inspection occurred before the timer was stopped."
 }
]

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

def get_cases():
    return read_json(CASES_FILE, DEMO_CASES)

def get_history():
    return read_json(HISTORY_FILE, [])

def ai_client():
    key = os.getenv("GROQ_API_KEY")
    if key and Groq:
        return Groq(api_key=key)
    return None

def ask_groq(system_prompt, user_prompt, temperature=0.6):
    client = ai_client()
    if not client:
        return None
    try:
        result = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
            temperature=temperature,
            response_format={"type":"json_object"} if "JSON" in system_prompt else None
        )
        return result.choices[0].message.content
    except Exception as exc:
        app.logger.warning("Groq request failed; using demo fallback: %s", exc)
        return None

@app.route("/")
def index():
    return render_template("index.html", demo=(ai_client() is None))

@app.get("/api/cases")
def cases():
    return jsonify({"cases":get_cases(), "demo":ai_client() is None})

@app.post("/api/new-case")
def new_case():
    payload = request.get_json(silent=True) or {}
    difficulty = payload.get("difficulty", "Easy")
    category = payload.get("category", "Any")
    prompt = f"""Create one original detective mystery as valid JSON with keys title, category, difficulty, story, victim, suspects, evidence, puzzles, solution, solution_explanation.
Use 3-4 suspects. Each suspect: id,name,role,background,motive,alibi. Each evidence item: id,title,detail,connects,hint. Include 1-2 puzzles with id,question,answer,accepted (array),explanation,points. solution must exactly match one suspect name. Make the case solvable and internally consistent. Do not include real-world graphic details."""
    generated = ask_groq("You are a mystery-game designer. Return ONLY valid JSON.", f"{prompt}\nDifficulty: {difficulty}. Category: {category}.")
    if generated:
        try:
            case = json.loads(generated)
            case["id"] = "ai-" + uuid.uuid4().hex[:8]
            case.setdefault("difficulty", difficulty)
            case.setdefault("category", category if category != "Any" else "Mystery")
            return jsonify({"case":case, "mode":"AI"})
        except (ValueError, TypeError):
            pass
    pool = [c for c in DEMO_CASES if difficulty == "Any" or c["difficulty"] == difficulty]
    case = random.choice(pool or DEMO_CASES)
    return jsonify({"case":case, "mode":"DEMO"})

@app.post("/api/hint")
def hint():
    data = request.get_json(silent=True) or {}
    case = data.get("case", {})
    level = int(data.get("level", 1))
    evidence = case.get("evidence", [])
    hints = [
      "Start with the timeline. Which event happened immediately before the incident?",
      "Compare each suspect's access with the physical or digital evidence. An opportunity matters more than a dramatic motive.",
      f"Pay close attention to evidence connected to {case.get('solution','the culprit')}, but verify it against the other suspects' alibis."
    ]
    prompt = f"Give one progressive, non-spoiler hint (level {level}/3) for this mystery. Do not reveal the culprit. Case: {json.dumps(case)[:7000]}"
    generated = ask_groq("You are a fair detective-game hint coach. Never reveal the final answer in a hint.", prompt)
    return jsonify({"hint":generated.strip() if generated else hints[min(max(level-1,0),2)], "mode":"AI" if generated else "DEMO"})

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("message") or "").strip()
    case = data.get("case", {})
    if not question:
        return jsonify({"error":"Please enter a question."}), 400
    prompt = f"""Current case data: {json.dumps(case)[:10000]}
Player question: {question}
Answer as a concise detective assistant. Only use facts in this case. You may suggest what evidence to compare, but do not reveal the solution unless the case is completed. If asked unrelated questions, politely steer back to the investigation."""
    answer = ask_groq("You are Detective AI, an observant and encouraging investigation partner.", prompt)
    if not answer:
        answer = "Let's work from the facts. Compare the timeline, access, and each suspect's alibi. Which piece of evidence independently confirms a suspect's story? (Demo Mode uses a simple fallback assistant.)"
    return jsonify({"answer":answer, "mode":"AI" if ai_client() else "DEMO"})

@app.post("/api/solve-puzzle")
def solve_puzzle():
    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip().lower()
    puzzle = data.get("puzzle", {})
    accepted = [str(x).strip().lower() for x in puzzle.get("accepted", [])]
    correct = answer in accepted or answer == str(puzzle.get("answer","")).lower()
    return jsonify({"correct":correct, "explanation":puzzle.get("explanation","Review the evidence and try again."), "points":int(puzzle.get("points",100)) if correct else 0})

@app.post("/api/complete")
def complete():
    data = request.get_json(silent=True) or {}
    case = data.get("case", {})
    accusation = data.get("suspect", "")
    score = max(0, int(data.get("score", 0)))
    correct = accusation.strip().lower() == str(case.get("solution","")).strip().lower()
    if correct:
        score += 250
    else:
        score = max(0, score - 50)
    entry = {"id":uuid.uuid4().hex[:10],"case_id":case.get("id"),"title":case.get("title","Mystery"),
             "date":datetime.now().strftime("%Y-%m-%d %H:%M"),"suspect":accusation,"correct":correct,
             "score":score,"solution":case.get("solution"),"explanation":case.get("solution_explanation","")}
    history = get_history()
    history.insert(0, entry)
    write_json(HISTORY_FILE, history[:100])
    return jsonify({"result":entry,"total_score":sum(x.get("score",0) for x in history)})

@app.get("/api/history")
def history():
    items = get_history()
    return jsonify({"history":items,"total_score":sum(x.get("score",0) for x in items),
                    "completed":sum(1 for x in items if x.get("correct"))})

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG","false").lower()=="true", port=int(os.getenv("PORT",5000)))
