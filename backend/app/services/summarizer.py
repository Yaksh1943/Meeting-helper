import json
import os
import re
from typing import Dict, List

from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

# Below this many words, there isn't enough real content for an LLM to
# meaningfully summarize - asking it to anyway produces confused
# "please provide the transcript" style output.
MIN_WORDS_FOR_SUMMARY = 8

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
) if GROQ_API_KEY else None


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


def summarize_window(transcript: str) -> str:
    if not transcript.strip():
        return "No content to summarize"

    if len(transcript.split()) < MIN_WORDS_FOR_SUMMARY:
        return transcript.strip()

    if client:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meeting assistant. Summarize the following meeting transcript segment in 2-3 sentences, focusing on key points and decisions.",
                    },
                    {"role": "user", "content": transcript},
                ],
                max_tokens=150,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            return fallback_summary(transcript)

    return fallback_summary(transcript)


def final_summary(transcript: str) -> Dict:
    if not transcript.strip():
        return {
            "summary": "No content available for summary",
            "action_items": [],
            "decisions": [],
        }

    if len(transcript.split()) < MIN_WORDS_FOR_SUMMARY:
        return {
            "summary": transcript.strip(),
            "action_items": [],
            "decisions": [],
        }

    if client:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meeting assistant. Analyze the meeting transcript and provide: 1. A comprehensive summary (3-4 sentences) 2. Action items (specific tasks mentioned) 3. Key decisions made. Respond with ONLY a JSON object, no other text, with keys: summary, action_items, decisions",
                    },
                    {"role": "user", "content": transcript},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            result = _extract_json(response.choices[0].message.content)
            return {
                "summary": result.get("summary", ""),
                "action_items": result.get("action_items", []),
                "decisions": result.get("decisions", []),
            }
        except Exception as e:
            print(f"Groq API error: {e}")
            return fallback_final_summary(transcript)

    return fallback_final_summary(transcript)


def rag_answer(question: str, context: str) -> str:
    if not context.strip():
        return "No meeting content available to answer questions"

    if client:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meeting assistant. Answer questions based ONLY on the provided meeting excerpts. If the information isn't in the excerpts, say so.",
                    },
                    {
                        "role": "user",
                        "content": f"Meeting excerpts:\n{context}\n\nQuestion: {question}",
                    },
                ],
                max_tokens=200,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            return f"Error processing question. Context available: {context[:100]}..."

    return f"Based on meeting content: {context[:100]}..."


def fallback_summary(transcript: str) -> str:
    sentences = re.split(r"[.!?]", transcript)
    return "Summary: " + " ".join(sentences[:2]).strip()


def fallback_final_summary(transcript: str) -> Dict:
    sentences = re.split(r"[.!?]", transcript)
    nouns = re.findall(r"\b[A-Z][a-z]*\b", transcript)[:3]
    return {
        "summary": " ".join(sentences[:2]).strip(),
        "action_items": nouns,
        "decisions": [],
    }