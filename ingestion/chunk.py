import json
import os


def load_incidents(path):
    chunks = []
    with open(path) as f:
        for line in f:
            report = json.loads(line)
            text = f"Incident: {report['description']} Outcome: {report['outcome']}"
            metadata = {
                "report_id":    report["report_id"],
                "date":         report["date"],
                "time":         report["time"],
                "zone":         report["zone"],
                "zone_alias":   report["zone_alias"],
                "department":   report["department"],
                "shift":        report["shift"],
                "lp_associate": report["lp_associate"],
                "incident_type":report["incident_type"],
                "source":       "incidents",
            }
            chunks.append({"text": text, "metadata": metadata})
    return chunks


def load_crime_reports(folder_path):
    chunks = []
    for filename in sorted(os.listdir(folder_path)):
        if not filename.endswith(".txt"):
            continue
        quarter = filename.replace("_crime_report.txt", "").upper()
        with open(os.path.join(folder_path, filename)) as f:
            content = f.read()
        text = f"Crime Report: {content}"
        metadata = {
            "source":      "crime_reports",
            "source_file": filename,
            "quarter":     quarter,
        }
        chunks.append({"text": text, "metadata": metadata})
    return chunks


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    incidents = load_incidents(os.path.join(base, "incidents.jsonl"))
    crimes    = load_crime_reports(os.path.join(base, "crime_reports"))
    print(f"Loaded {len(incidents)} incident chunks")
    print(f"Loaded {len(crimes)} crime report chunks")
    print(f"\nSample incident chunk:")
    print(f"  text: {incidents[0]['text'][:80]}...")
    print(f"  metadata: {incidents[0]['metadata']}")
    print(f"\nSample crime chunk:")
    print(f"  text: {crimes[0]['text'][:80]}...")
    print(f"  metadata: {crimes[0]['metadata']}")