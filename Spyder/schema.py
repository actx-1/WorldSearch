import psycopg2
import json

# This script only creates the database components which are necessary for the spyder to function
# In future, this script will probably be superseded by a global script.

# Beware that this script is potentially vulnerable to string injection.
# As implemented, only strings defined in this file are executed, so this is not a problem assuming the user does not unknowingly modify this file.
commands = [
        "CREATE TABLE IF NOT EXISTS robotstxt(reversed_hostname TEXT PRIMARY KEY,mtime INTEGER,last_mtime_check INTEGER,content_size INTEGER,content TEXT);",
    
        "CREATE TABLE IF NOT EXISTS websources(id BIGSERIAL PRIMARY KEY,reversed_hostname TEXT,link TEXT,mtime INTEGER,content_hash BYTEA,last_indexed_ts INTEGER,last_checked_ts INTEGER,indexer_version INTEGER,resource_content TEXT,FOREIGN KEY(reversed_hostname) REFERENCES robotstxt(reversed_hostname));",
        "CREATE UNIQUE INDEX IF NOT EXISTS websources_links ON websources(link);",
        "CREATE INDEX IF NOT EXISTS websources_timecheck ON websources(last_checked_ts);",

        # last_claim_ts for newly created spyders is current time -- its purpose is just to eventually GC older spyders
        "CREATE TABLE IF NOT EXISTS spyders(id SERIAL PRIMARY KEY,created_ts INTEGER,last_claim_ts INTEGER);",
        "CREATE INDEX IF NOT EXISTS spyder_batchtimes ON spyders(last_claim_ts);",
        
        "CREATE TABLE IF NOT EXISTS link_queue(id BIGSERIAL PRIMARY KEY,last_indexed_ts INTEGER,added_ts INTEGER,link TEXT,claimant_id INTEGER,claim_ts INTEGER,FOREIGN KEY(claimant_id) REFERENCES spyders(id))",
        "CREATE UNIQUE INDEX IF NOT EXISTS link_queue_link_uniqueness ON link_queue(link);", # Should use the foreign key index
        "CREATE INDEX IF NOT EXISTS link_queue_added_ts ON link_queue(added_ts);",
        "CREATE INDEX IF NOT EXISTS link_queue_claims ON link_queue(claimant_id);",
        "CREATE INDEX IF NOT EXISTS link_queue_claim_ts ON link_queue(claim_ts) WHERE claim_ts is not null;",

        "CREATE TABLE IF NOT EXISTS websource_search(websource_id BIGINT,part INTEGER,text_search TSVECTOR,PRIMARY KEY(websource_id,part),FOREIGN KEY(websource_id) REFERENCES websources(id));",
        "CREATE INDEX IF NOT EXISTS websource_search_text_index ON websource_search USING GIN(text_search);"
    ]

with open("pg_creds.txt",'r') as f:
    creds = json.loads(f.read())
db = psycopg2.connect("dbname='"+str(creds["dbname"])+"' user='"+str(creds["user"])+"' password='"+str(creds["password"])+"' host='"+str(creds["host"])+"' port='"+str(creds["port"])+"'")

cursor = db.cursor()
for command in commands:
    print(command)
    cursor.execute(command)

# First row to get everything started
try:
    cursor.execute("INSERT INTO link_queue(last_indexed_ts,added_ts,link) VALUES(0,0,'https://en.wikipedia.org/wiki/Main_Page');")
    cursor.execute("INSERT INTO link_queue(last_indexed_ts,added_ts,link) VALUES(0,0,'https://chat.cereogii.net');")
    cursor.execute("INSERT INTO link_queue(last_indexed_ts,added_ts,link) VALUES(0,0,'https://www.youtube.com');")
except psycopg2.errors.UniqueViolation:
    pass
db.commit()
db.close()
