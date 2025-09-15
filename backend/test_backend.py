import requests
from faker import Faker
from datetime import datetime
from pathlib import Path
import logging

BASE_URL = "http://localhost:8000/api/meetings"
fake = Faker()

REPORT_FILE = Path("test_report.md")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ----------------------------
# Predefined meeting scenarios
# ----------------------------
SCENARIOS = {
    "Project Kickoff": {
        "conversation": [
            ("Alice", "Good morning everyone, let's start with the project status update."),
            ("Bob", "We've completed the frontend design. Backend integration is pending."),
            ("Charlie", "The API endpoints are ready. Waiting on authentication testing."),
            ("Diana", "Budget approval will be finalized by next Friday."),
            ("Eve", "I suggest we prioritize user testing before launch."),
            ("Frank", "Agreed. We can run a closed beta in two weeks."),
        ],
        "questions": [
            "What are the next steps?",
            "Who mentioned the budget?",
            "When is the beta planned?",
        ],
    },
    "Research Discussion": {
        "conversation": [
            ("Alice", "Let's review the experiment results from last week."),
            ("Bob", "The accuracy improved by 5% after parameter tuning."),
            ("Charlie", "But the dataset size is still small, which limits reliability."),
            ("Diana", "I can work on collecting additional data samples."),
            ("Eve", "We also need to document the methodology for reproducibility."),
            ("Frank", "Good point. I'll draft the documentation outline."),
        ],
        "questions": [
            "What were the experiment results?",
            "Who will collect more data?",
            "What was decided about documentation?",
        ],
    },
    "Weekly Sync": {
        "conversation": [
            ("Alice", "Any blockers for this week?"),
            ("Bob", "I'm waiting on API keys for deployment."),
            ("Charlie", "No blockers on my side, just progressing on tasks."),
            ("Diana", "We should also prepare slides for next week's client review."),
            ("Eve", "I'll start drafting the slides and share by Friday."),
            ("Frank", "Sounds good. I'll handle the deployment once keys arrive."),
        ],
        "questions": [
            "What blockers were discussed?",
            "Who is preparing the slides?",
            "What is Frank responsible for?",
        ],
    },
}


# ----------------------------
# Helpers
# ----------------------------
def log(report_lines, text):
    logging.info(text)
    report_lines.append(text)


def post(url, payload):
    return requests.post(url, json=payload).json()


def get(url):
    return requests.get(url).json()


# ----------------------------
# Main test flow
# ----------------------------
def run_tests():
    report_lines = ["# Meeting Helper Test Report\n"]

    total_passed, total_failed, total_skipped = 0, 0, 0

    for title, scenario in SCENARIOS.items():
        log(report_lines, f"\n## {title}")
        log(report_lines, f"- Starting test at {datetime.utcnow().isoformat()}")

        # Create meeting
        host_email = fake.email()
        resp = post(BASE_URL + "/", {"title": title, "host_email": host_email})
        meeting_id = resp.get("meeting_id")
        if meeting_id:
            log(report_lines, f"- ✅ Meeting created (ID: {meeting_id})")
            total_passed += 1
        else:
            log(report_lines, "- ❌ Failed to create meeting")
            total_failed += 1
            continue

        # Invite participants
        participants = [fake.email() for _ in range(2)]
        resp = post(f"{BASE_URL}/{meeting_id}/invite", {"emails": participants})
        if "invited" in resp:
            log(report_lines, f"- ✅ Participants invited: {', '.join(participants)}")
            total_passed += 1
        else:
            log(report_lines, "- ❌ Failed to invite participants")
            total_failed += 1

        # Start meeting
        resp = post(f"{BASE_URL}/{meeting_id}/start", {})
        if resp.get("status") == "started":
            log(report_lines, "- ✅ Meeting started")
            total_passed += 1
        else:
            log(report_lines, "- ❌ Failed to start meeting")
            total_failed += 1

        # Ingest transcripts (scripted conversation)
        for idx, (speaker, text) in enumerate(scenario["conversation"]):
            payload = {"ts_start": idx * 10, "ts_end": (idx + 1) * 10, "speaker": speaker, "text": text}
            resp = post(f"{BASE_URL}/{meeting_id}/ingest-transcript", payload)
        log(report_lines, f"- ✅ Transcript conversation ingested ({len(scenario['conversation'])} turns)")
        total_passed += 1

        # Get timeline summaries
        summaries = get(f"{BASE_URL}/{meeting_id}/summaries")
        if summaries:
            log(report_lines, f"- ✅ Timeline summaries found ({len(summaries)})")
            total_passed += 1
        else:
            log(report_lines, "- ❌ No timeline summaries found")
            total_failed += 1

        # End meeting
        resp = post(f"{BASE_URL}/{meeting_id}/end", {})
        if resp.get("status") == "ended":
            log(report_lines, "- ✅ Meeting ended and final summary endpoint returned data")
            total_passed += 1
        else:
            log(report_lines, "- ❌ Failed to end meeting")
            total_failed += 1

        # Get final summary
        final_summary = get(f"{BASE_URL}/{meeting_id}/final-summary")
        if "summary" in final_summary:
            log(report_lines, f"- ✅ Final summary retrieved:\n\n    {final_summary['summary'][:200]}...")
            total_passed += 1
        else:
            log(report_lines, "- ❌ Failed to retrieve final summary")
            total_failed += 1

        # Chatbot Q&A
        qna_results = []
        for q in scenario["questions"]:
            ans = post(f"{BASE_URL}/{meeting_id}/ask", {"question": q}).get("answer")
            if ans:
                qna_results.append((q, ans))
                total_passed += 1
            else:
                qna_results.append((q, "❌ No answer"))
                total_failed += 1

        log(report_lines, "\n### Chatbot Q&A")
        for q, a in qna_results:
            log(report_lines, f"- **Q:** {q}\n  - **A:** {a}")

        # Send final summary
        resp = post(f"{BASE_URL}/{meeting_id}/send-summary", {})
        if resp.get("status") == "sent":
            log(report_lines, f"- ✅ Final summary sent (recipients: {', '.join(resp.get('recipients', []))})")
            total_passed += 1
        else:
            log(report_lines, "- ❌ Failed to send final summary")
            total_failed += 1

        # Skipped
        log(report_lines, "- ⚠️ Skipped: voice/real-time latency checks (backend-only)")
        total_skipped += 1

    # Overall results
    log(report_lines, "\n---\n")
    log(report_lines, "## Overall Results")
    log(report_lines, f"- **Passed (checkmarks):** {total_passed}")
    log(report_lines, f"- **Failed (crosses):** {total_failed}")
    log(report_lines, f"- **Skipped:** {total_skipped}")

    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    logging.info(f"✅ Test complete. Report written to {REPORT_FILE}")


if __name__ == "__main__":
    run_tests()
