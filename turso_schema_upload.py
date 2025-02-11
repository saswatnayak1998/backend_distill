import os
import libsql_experimental as libsql

# Replace these with your Turso database URL and auth token
LIBSQL_URL = "saswat-sash.turso.io"
LIBSQL_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Mzg4MDg3ODAsImlkIjoiZTc4Y2U4MTAtNDJmMi00ZjJmLThkNGUtMGZmYTc3ZWUwMTZkIn0.Q7PpIx2eqNJI9X9CYOELyCtm87CiNDUGjXZbmsRIlIluVwvdxwgY0hT4LcL6-TiEfakdQzPwUbY8zKqrD0C_AQ"

try:
    # Connect to the database
    conn = libsql.connect("local.db",sync_url=LIBSQL_URL, auth_token=LIBSQL_AUTH_TOKEN)

    # Create schema
    schema_statements = [
            """
            CREATE TABLE IF NOT EXISTS candidate (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                resume TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                test_id INTEGER NOT NULL,
                question TEXT NOT NULL,  -- Long questions can be stored here
                test_cases TEXT NOT NULL,  -- JSON string to store multiple test cases
                reference_solution TEXT,  -- Optional: Reference solution for comparison
                max_score INTEGER NOT NULL,  -- Maximum score for this question
                FOREIGN KEY (test_id) REFERENCES test(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY,
                candidate_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer TEXT NOT NULL,  -- Candidate's answer
                copypastelogs TEXT,  -- Logs for copy-paste detection
                score INTEGER NOT NULL,  -- Score for this question
                feedback TEXT,  -- Feedback for the candidate
                FOREIGN KEY (candidate_id) REFERENCES candidate(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );
            """
        ]

    # Execute schema statements
    for statement in schema_statements:
        conn.execute(statement)
    print("Schema created successfully!")

except Exception as e:
    print("An error occurred:", e)
