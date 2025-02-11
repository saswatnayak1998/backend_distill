import os
import docker
import io
import json
import subprocess
import tarfile
import uvicorn
import tempfile
import requests
from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv

from typing import List, Optional

import libsql_experimental as libsql
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, Request

from typing import List


app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL if necessary
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods, including OPTIONS
    allow_headers=["*"],
)

class CodeExecutionRequest(BaseModel):
    language: str
    code: str

# Function to execute code in the Docker container
REMOTE_PYTHON_EXECUTOR_URL = "https://railway-python-production.up.railway.app/run"

def execute_code_in_container(language: str, code: str):
    try:
        # Prepare the request payload
        payload = {"code": code}

        # Send the code to the remote Python execution service
        response = requests.post(REMOTE_PYTHON_EXECUTOR_URL, json=payload, timeout=10)

        # Check if the request was successful
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Execution error: {response.text}")

        # Return the output from the remote container
        return response.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Endpoint to execute code
@app.post("/run")
async def run_code(request: CodeExecutionRequest):
    """API endpoint to execute code in the running container."""
    return execute_code_in_container(request.language, request.code)

###


class Candidate(BaseModel):
    name: str
    password: str
    resume: str = None  # Base64-encoded resume (optional)


class Score(BaseModel):
    candidate_id: int
    question_id: int
    copypastelogs: str
    score: float
LIBSQL_URL = "libsql://saswat-sash.turso.io"
load_dotenv()
LIBSQL_AUTH_TOKEN = os.getenv("LIBSQL_AUTH_TOKEN") 
conn = libsql.connect("saswat",sync_url=LIBSQL_URL, auth_token=LIBSQL_AUTH_TOKEN)
cursor = conn.cursor()





class Question(BaseModel):
    id: int
    test_id: int
    question: str
    test_cases: str
    reference_solution: Optional[str] = None
    max_score: int



@app.get("/get-question/{question_id}")
async def get_question(question_id: int):
    """
    Fetch a single question by its ID from the database.
    """
    try:
        query = """
        SELECT id, test_id, question, test_cases, reference_solution, max_score
        FROM questions
        WHERE id = ?;
        """
        cursor = conn.execute(query, (question_id,))
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Question not found")

        return {
            "id": row[0],
            "test_id": row[1],
            "question": row[2],
            "test_cases": row[3],  # This will return `[]` if empty
            "reference_solution": row[4],
            "max_score": row[5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    
@app.get("/get-questions", response_model=List[Question])
async def get_questions(test_id: Optional[int] = Query(None, description="Filter questions by test ID")):
    """
    Fetch all questions from the database. If `test_id` is provided, return only questions for that test.
    """
    try:
        # Query logic: Filter by test_id if provided, otherwise fetch all questions
        if test_id is not None:
            query = "SELECT id, test_id, question, test_cases, reference_solution, max_score FROM questions WHERE test_id = ?;"
            cursor = conn.execute(query, (test_id,))
        else:
            query = "SELECT id, test_id, question, test_cases, reference_solution, max_score FROM questions;"
            cursor = conn.execute(query)

        rows = cursor.fetchall()

        if not rows:
            return []  # ✅ Return empty list instead of None

        # Format data as a list of dictionaries
        return [
            {
                "id": row[0],
                "test_id": row[1],
                "question": row[2],
                "test_cases": row[3],
                "reference_solution": row[4],
                "max_score": row[5]
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Request model for logs
class LogEntry(BaseModel):
    action: str
    text: str
    timestamp: str

class LogRequest(BaseModel):
    logs: List[LogEntry]

# Directory to save logs
LOGS_DIR = "/Users/saswatnayak/startup1/logs"

@app.post("/save-logs")
async def save_logs(request: LogRequest):
    """API endpoint to save logs to a file."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)  # Create the logs directory if it doesn't exist

    filename = os.path.join(LOGS_DIR, f"copy-paste-logs-{tempfile.NamedTemporaryFile().name}.json")

    try:
        with open(filename, "w") as log_file:
            log_file.write(request.json())
        return {"message": "Logs saved successfully", "file": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save logs: {str(e)}")


@app.post("/check-user")
async def check_user(candidate: Candidate):
    
    print(candidate.name)

    # Fetch candidate_id and password from the database
    cursor.execute(
        "SELECT id, password FROM candidate WHERE name=?;",
        (candidate.name,)
    )

    result = cursor.fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail="Candidate does not exist.")

    # Extract candidate_id and stored_password from the result
    candidate_id, stored_password = result

    if stored_password != candidate.password:
        raise HTTPException(status_code=401, detail="Invalid password.")

    # Return success message along with candidate_id
    return {
        "message": "Login successful",
        "candidate_id": candidate_id,  # Include candidate_id in the response
    }

@app.get("/get-tests")
async def get_tests():
    try:
        cursor = conn.execute("SELECT id, name, description FROM test;")
        tests = [
            {"id": row[0], "name": row[1], "description": row[2]}
            for row in cursor.fetchall()
        ]
        return tests
    except Exception as e:
        return {"error": str(e)}, 500
    

# Request Model
class TestCreate(BaseModel):
    name: str
    description: str

@app.post("/create-test")
async def create_test(test: TestCreate):
    try:
        print("📌 Received Request:", test.model_dump())  # ✅ Debugging log

        # Insert into the database
        cursor = conn.execute(
            "INSERT INTO test (name, description) VALUES (?, ?) RETURNING id;",
            (test.name, test.description)
        )

        test_id = cursor.fetchone()[0]
        conn.commit()  # ✅ Ensure data is persisted

        print(f"✅ Test Created: ID {test_id}, Name: {test.name}")  # ✅ Confirm insertion
        return {"test_id": test_id, "status": "success"}

    except Exception as e:
        print("❌ Error inserting test:", str(e))  # ✅ Debugging log
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/upload-question")
async def upload_question(request: Request):
    try:
        data = await request.json()

        # Validate required fields
        if "test_id" not in data or "question" not in data or "test_cases" not in data:
            raise HTTPException(status_code=400, detail="Missing required fields: test_id, question, test_cases")

        # Ensure test_cases is a JSON array
        if not isinstance(data["test_cases"], list):
            raise HTTPException(status_code=400, detail="Test cases must be a JSON array")

        # Insert the question into the database
        conn.execute(
            """
            INSERT INTO questions (test_id, question, test_cases, reference_solution, max_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["test_id"],
                data["question"],
                json.dumps(data["test_cases"]),  # Convert test_cases to JSON string
                data.get("reference_solution", None),
                data.get("max_score", 10),  # Default max_score to 10 if not provided
            ),
        )

        # Commit the transaction to ensure the data persists
        conn.commit()

        return {"status": "success"}
    except Exception as e:
        return {"error": f"Failed to upload question: {str(e)}"}, 500
@app.post("/save-score")
async def save_score(request: Request):
    try:
        data = await request.json()
        conn.execute(
            """
            INSERT INTO scores (candidate_id, question_id, copypastelogs, score)
            VALUES (?, ?, ?, ?)
            """,
            (
                data["candidate_id"],
                data["question_id"],
                json.dumps(data["copypastelogs"]),  # Save logs as JSON
                data["score"],
            ),
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save score: {str(e)}")


# Endpoint to create a new user
@app.post("/create-user")
async def create_user(candidate: Candidate):
    cursor.execute("SELECT id FROM candidate WHERE name = ?", (candidate.name,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="User already exists.")
    cursor.execute(
        "INSERT INTO candidate (name, password, resume) VALUES (?, ?, ?)",
        (candidate.name, candidate.password, candidate.resume),
    )
    conn.commit()
    return {"message": "Candidate created successfully."}


# Endpoint to upload questions


# Endpoint to upload scores
@app.post("/upload-score")
async def upload_score(score: Score):
    cursor.execute(
        """
        INSERT INTO scores (candidate_id, question_id, copypastelogs, score)
        VALUES (?, ?, ?, ?)
        """,
        (score.candidate_id, score.question_id, score.copypastelogs, score.score),
    )
    conn.commit()
    return {"message": "Score uploaded successfully."}



class TestRequest(BaseModel):
    code: str
    question_id: int



# @app.post("/run-tests")
# async def run_tests(request: Request):
#     data = await request.json()
#     language = data["language"]
#     code = data["code"]
#     question_id = data["question_id"]

#     # Fetch test cases for the given question_id
#     question = conn.execute(
#         "SELECT test_cases FROM questions WHERE id = ?",
#         (question_id,)
#     ).fetchone()

#     if not question:
#         raise HTTPException(status_code=404, detail="Question not found")

#     test_cases = json.loads(question["test_cases"])

#     # Execute tests (pseudo-code)
#     results = execute_tests(language, code, test_cases)

#     return {"results": results}


def get_test_cases(question_id):
    # Dummy function to simulate fetching test cases for a question
    return [
        {"input": "5\n", "expected_output": "120"},
        {"input": "3\n", "expected_output": "6"}
    ]

@app.post("/run-tests")
async def run_tests(request: Request):
    """
    Run candidate's code inside the Docker container, count passed/failed tests,
    store results in `scores`, and adjust score based on copy-paste behavior.
    """
    try:
        # Parse request body
        data = await request.json()
        language = data.get("language")
        code = data.get("code")
        answer = data.get("answer")
        question_id = data.get("question_id")
        candidate_id = data.get("candidate_id")  # ✅ Extract candidate_id
        copy_paste_logs = data.get("copy_paste_logs", [])

        if not all([language, code, question_id, candidate_id]):
            raise HTTPException(status_code=400, detail="Missing required fields: language, code, question_id, candidate_id")

        # Run the code inside the Docker container
        execution_result = execute_code_in_container(language, code)
        output = execution_result.get("output", "")

        # Count PASSED and FAILED occurrences
        passed = sum(1 for line in output.splitlines() if "PASSED" in line)
        failed = sum(1 for line in output.splitlines() if "FAILED" in line)

        # Calculate the base score
        total_tests = passed + failed
        score = max(0, int((passed / total_tests) * 10)) if total_tests > 0 else 0

        # Identify unmatched copy-paste operations
        copy_paste_pairs = {"Copy": 0, "Paste": 0}
        for log in copy_paste_logs:
            if log["action"] in copy_paste_pairs:
                copy_paste_pairs[log["action"]] += 1

        unmatched_operations = abs(copy_paste_pairs["Copy"] - copy_paste_pairs["Paste"])

        # Deduct points for excessive unmatched copy-paste actions
        final_score = score - (unmatched_operations * 5)

        # ✅ Fix: Include `candidate_id` in INSERT query
        cursor.execute(
            """
            INSERT INTO scores (candidate_id, question_id, copypastelogs, score, answer)
            VALUES (?, ?, ?, ?, ?);
            """,
            (candidate_id, question_id, json.dumps(copy_paste_logs), final_score, answer),
        )
        conn.commit()

        return {
            "status": "success",
            "output": output,
            "passed": passed,
            "failed": failed,
            "score": final_score,
            "copy_paste_issues": unmatched_operations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_code_in_sandbox(language, code, input_data):
    """
    Runs the user's code in a sandboxed environment.
    """
    if language == "python":
        exec_script = f"""
import sys
sys.stdin = open(0)
{code}
print(main({input_data}))  # Ensure function is called properly
"""
        try:
            process = subprocess.run(
                ["python3", "-c", exec_script],
                input="",
                capture_output=True,
                text=True,
                timeout=3  # Prevent infinite loops
            )
            return process.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Timeout Error"
    else:
        return "Language not supported"


# # Start the application when the script is run
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 8081))  # Use PORT env variable
#     uvicorn.run(app, host="0.0.0.0", port=port)
