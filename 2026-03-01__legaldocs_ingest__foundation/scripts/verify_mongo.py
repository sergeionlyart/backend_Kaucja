import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
db_name = os.environ.get("MONGO_DB", "legal_rag_iter42_full")

client = MongoClient(uri)
db = client[db_name]

# Get the latest run
latest_run = list(db.ingest_runs.find().sort("started_at", -1).limit(1))[0]
run_id = latest_run["run_id"]

docs = list(db.documents.find({}, {"_id": 0, "doc_uid": 1, "access_status": 1, "title": 1, "doc_type": 1}))
sources = list(db.document_sources.find({}, {"_id": 0, "source_id": 1, "doc_uid": 1}))

# Join
doc_map = {d["doc_uid"]: d for d in docs}
results = []
for s in sources:
    uid = s["doc_uid"]
    d = doc_map.get(uid, {})
    results.append({
        "source_id": s["source_id"],
        "doc_uid": uid,
        "access_status": d.get("access_status", "UNKNOWN"),
        "title": d.get("title", "UNKNOWN"),
        "doc_type": d.get("doc_type", "UNKNOWN")
    })

# filter specifically the base 15 if possible or just dump all
export_data = {
    "latest_run_id": run_id,
    "run_stats": latest_run.get("stats", {}),
    "documents": results
}

os.makedirs("docs/reports", exist_ok=True)
with open("docs/reports/mongo_verification_export.json", "w", encoding="utf-8") as f:
    json.dump(export_data, f, indent=2, ensure_ascii=False)

print("Exported to docs/reports/mongo_verification_export.json")
