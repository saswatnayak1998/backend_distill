import os
import libsql_experimental as libsql
import json


LIBSQL_URL = "libsql://saswat-sash.turso.io"
LIBSQL_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Mzg4MTk5NzAsImlkIjoiZTc4Y2U4MTAtNDJmMi00ZjJmLThkNGUtMGZmYTc3ZWUwMTZkIn0.mM72YjLL_AoOvS3PAASKUQXF1CBxmyerUPYkIcTGdi-Sqq39H1As7rs6N7XOAD9jCp2gLGsUraqYLeC28NWKBg"


conn = libsql.connect("local.db",sync_url=LIBSQL_URL, auth_token=LIBSQL_AUTH_TOKEN)
cursor = conn.cursor()

cursor = conn.execute("SELECT name FROM candidate")
test_id = cursor.fetchone()[0]
print(test_id)