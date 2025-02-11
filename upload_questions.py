import libsql_experimental as libsql
import json

# Replace these with your Turso database URL and auth token
LIBSQL_URL = "libsql://saswat-sash.turso.io"
LIBSQL_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Mzg4NTgxNDIsImlkIjoiZTc4Y2U4MTAtNDJmMi00ZjJmLThkNGUtMGZmYTc3ZWUwMTZkIn0.3ssoe-JnkLEXmRFSF1nB8ALUN0OS7i3_5JPpkE5YO-wqipH-9EfoplEKvl-J5H_SNpPg0JIl0WeiZA8oSpZ5AQ"

# Connect to Turso DB
conn = libsql.connect("saswat",sync_url=LIBSQL_URL, auth_token=LIBSQL_AUTH_TOKEN)
cursor = conn.cursor()

# Step 1: Insert a new test
test_name = "Python Coding Test"
test_description = "This test evaluates Python programming skills."
insert_test_query = """
    INSERT INTO test (name, description) VALUES (?, ?);
"""

conn.execute(insert_test_query, (test_name, test_description))

# Retrieve the newly created test ID
cursor = conn.execute("SELECT id FROM test WHERE name = ?", (test_name,))
test_row = cursor.fetchone()
if test_row:
    test_id = test_row[0]
    print(f"✅ Created test with ID: {test_id}")
else:
    print("❌ Test creation failed.")
    conn.close()
    exit()

# Step 2: Insert questions associated with this test
questions = [
    {
        "question": "Write a function to find the largest number in an array.",
        "test_cases": json.dumps([
            {"input": "[1, 2, 3, 4, 5]", "expected_output": "5"},
            {"input": "[-1, -2, -3]", "expected_output": "-1"}
        ]),
        "reference_solution": "def find_max(arr): return max(arr)",
        "max_score": 10
    },
    {
        "question": "Implement a function to check if a string is a palindrome.",
        "test_cases": json.dumps([
            {"input": "'racecar'", "expected_output": "True"},
            {"input": "'hello'", "expected_output": "False"}
        ]),
        "reference_solution": "def is_palindrome(s): return s == s[::-1]",
        "max_score": 10
    }
]

# Insert questions into the database
insert_question_query = """
    INSERT INTO questions (test_id, question, test_cases, reference_solution, max_score)
    VALUES (?, ?, ?, ?, ?);
"""

for q in questions:
    conn.execute(insert_question_query, (test_id, q["question"], q["test_cases"], q["reference_solution"], q["max_score"]))

print("✅ Questions uploaded successfully.")

# Verify Data
cursor = conn.execute("SELECT * FROM questions WHERE test_id = ?", (test_id,))
rows = cursor.fetchall()
if rows:
    print("\n📝 Questions inserted:")
    for row in rows:
        print(row)
else:
    print("❌ No questions found for the given test ID.")
