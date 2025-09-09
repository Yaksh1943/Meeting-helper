import os 
import re
from typing import Dict, List
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_window(transcript: str) -> str:
    if not transcript.strip():
        return "No content to summarize"
        
    if os.getenv("OPENAI_API_KEY"):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a meeting assistant. Summarize the following meeting transcript segment in 2-3 sentences, focusing on key points and decisions."
                    },
                    {
                        "role": "user", 
                        "content": transcript
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return fallback_summary(transcript)
    
    return fallback_summary(transcript)

def final_summary(transcript: str) -> Dict:
    if not transcript.strip():
        return {
            "summary": "No content available for summary",
            "action_items": [],
            "decisions": []
        }
        
    if os.getenv("OPENAI_API_KEY"):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a meeting assistant. Analyze the meeting transcript and provide:
                                        1. A comprehensive summary (3-4 sentences)
                                        2. Action items (specific tasks mentioned)
                                        3. Key decisions made

                                        Return a JSON object with keys: summary, action_items, decisions"""
                    },
                    {
                        "role": "user", 
                        "content": transcript
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the response
            import json
            result = json.loads(response.choices[0].message.content)
            return {
                "summary": result.get("summary", ""),
                "action_items": result.get("action_items", []),
                "decisions": result.get("decisions", [])
            }
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return fallback_final_summary(transcript)
    
    return fallback_final_summary(transcript)

def rag_answer(question: str, context: str) -> str:
    if not context.strip():
        return "No meeting summary available to answer questions"
        
    if os.getenv("OPENAI_API_KEY"):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a meeting assistant. Answer questions based ONLY on the provided meeting summary. If the information is not in the summary, say so."
                    },
                    {
                        "role": "user", 
                        "content": f"Meeting Summary: {context}\n\nQuestion: {question}"
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"Error processing question. Context available: {context[:100]}..."
    
    return f"Based on meeting summary: {context[:100]}..."

# Fallback functions for when OpenAI fails
def fallback_summary(transcript: str) -> str:
    sentences = re.split(r'[.!?]', transcript)
    return "Summary: " + " ".join(sentences[:2]).strip()

def fallback_final_summary(transcript: str) -> Dict:
    sentences = re.split(r'[.!?]', transcript)
    nouns = re.findall(r'\b[A-Z][a-z]*\b', transcript)[:3]
    return {
        "summary": " ".join(sentences[:2]).strip(),
        "action_items": nouns,
        "decisions": []
    }