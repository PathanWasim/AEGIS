# AEGIS Compiler IDE
**Adaptive Execution Guarded Interpreter System**

## Project Overview
AEGIS is a production-grade compiler and execution environment built for academic and cybersecurity research. It implements a security-first architecture where code evaluation defaults to a strictly monitored sandbox. The system features a custom programming language, dedicated intermediate representations, and a comprehensive React-based IDE frontend.

![AEGIS Architecture Block](./frontend/public/favicon.ico)

## Features
- **Dual-Mode Evaluation**: Sandboxed Interpreter (safe, default) and an Optimized VM (fast, privilege-based).
- **Dynamic Trust Metric**: Algorithms incrementally build trust across discrete runs. Unlocking optimizations demands consistent structural integrity.
- **Static Analysis**: Pre-execution scans identify memory, looping, and logic defects before variable mutation.
- **Runtime Integrity Hooks**: Active instruction enumeration limits operations, preventing algorithmic halting problems from degrading server posture.
- **Integrated IDE**: Monaco-driven web interface featuring stage-by-stage pipeline observation and real-time structured AST mapping.

## Architecture
The system employs a strict 7-stage evaluation pipeline to ensure operational determinism:
`Lexed → Parsed → AST Built → Analyzed → Interpreted → Trust Verified → Optimized`

## Execution Model
AEGIS reverses classic compiler theory:
1. **Pessimistic Default**: Every execution starts in the restricted Interpreter environment.
2. **Telemetry Aggregation**: Running operations log cycle counts, computational bounds, and states.
3. **Privilege Application**: If the static profile is benign and previous telemetry yields `Trust >= 1.0`, subsequent runs promote to the Cached VM.
4. **Algorithmic Rollback**: Should the Cached VM branch into a violation, execution terminates, Trust resets to `0.0`, and code reverts to the Sandbox.

## Tech Stack
* **Frontend**: React 19, Vite, Zustand, Monaco Editor, Recharts.
* **Backend**: Python 3.11+, Flask.

## Setup Instructions

### Backend (Python/Flask)
```bash
cd backend
pip install -r ../requirements.txt 
python app.py
```
*Served on `http://127.0.0.1:5000/`*

### Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
*Served on `http://localhost:3000/`*

## Example Usage
Input syntax in the left panel. Press `Ctrl+Enter` or click `Run`.

```text
count = 0
while count < 5
  print count
  count = count + 1
end
```

Executing this code demonstrates the trust growth cycle. Invoking iterations consecutively transitions the top status indicator from the restricted `INTERPRETER` mode to the accelerated `OPTIMIZED` mode once telemetry vectors are validated.