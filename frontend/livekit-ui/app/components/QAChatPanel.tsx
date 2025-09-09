import React, { useState } from "react";
import axios from "axios";
import { API_CONFIG } from '@/lib/api-config';

interface QAHistory {
  id: string;
  question: string;
  answer: string;
  timestamp: Date;
}

export default function QAChatPanel({ 
  meetingId, 
  meetingEnded 
}: { 
  meetingId: number;
  meetingEnded: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [qaHistory, setQaHistory] = useState<QAHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async () => {
    if (!question.trim()) return;
    
    const currentQuestion = question.trim();
    setQuestion(""); 
    setLoading(true);
    setError(null);

    try {
      const res = await axios.post(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/ask`, {
        question: currentQuestion,
      });
      
      const newQA: QAHistory = {
        id: Date.now().toString(),
        question: currentQuestion,
        answer: res.data.answer || "No answer received",
        timestamp: new Date()
      };
      
      setQaHistory(prev => [newQA, ...prev]); 
    } catch (err) {
      console.error('Failed to ask question:', err);
      setError("Failed to get answer. Please try again.");
      setQuestion(currentQuestion); 
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={{ 
      backgroundColor: 'white',
      border: '1px solid #dee2e6', 
      borderRadius: '8px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      height: '400px'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '12px 16px',
        borderBottom: '1px solid #dee2e6',
        backgroundColor: '#f8f9fa'
      }}>
        <h3 style={{ 
          fontWeight: 'bold', 
          margin: 0, 
          color: '#333',
          fontSize: '16px'
        }}>
          Q&A Chat (RAG)
        </h3>
        <p style={{ 
          margin: '4px 0 0 0', 
          fontSize: '12px', 
          color: '#6c757d'
        }}>
          {meetingEnded ? 'Ask questions about meeting content' : 'Available after meeting ends'}
        </p>
      </div>

      {/* Chat History */}
      <div style={{ 
        flex: 1,
        padding: '16px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {/* Waiting message */}
        {!meetingEnded && (
          <div style={{ 
            padding: '16px',
            textAlign: 'center',
            color: '#6c757d',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #dee2e6'
          }}>
            <div style={{ marginBottom: '8px', fontSize: '24px' }}>⏳</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold' }}>Chatbot will be available after meeting ends</div>
            <div style={{ fontSize: '12px', marginTop: '4px' }}>
              The AI assistant needs the final meeting summary to answer your questions
            </div>
          </div>
        )}

        {meetingEnded && qaHistory.length === 0 && !loading && (
          <div style={{ 
            textAlign: 'center',
            color: '#6c757d',
            fontSize: '14px',
            marginTop: '20px'
          }}>
            <div style={{ marginBottom: '8px' }}>💬</div>
            <div>No questions asked yet</div>
            <div style={{ fontSize: '12px', marginTop: '4px' }}>
              Start by asking about the meeting content
            </div>
          </div>
        )}

        {/* History */}
        {qaHistory.map((qa) => (
          <div key={qa.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* Question */}
            <div style={{ 
              alignSelf: 'flex-end',
              maxWidth: '80%',
              padding: '8px 12px',
              backgroundColor: '#007bff',
              color: 'white',
              borderRadius: '16px 16px 4px 16px',
              fontSize: '14px',
              wordBreak: 'break-word'
            }}>
              {qa.question}
            </div>
            
            {/* Answer */}
            <div style={{ 
              alignSelf: 'flex-start',
              maxWidth: '90%',
              padding: '8px 12px',
              backgroundColor: '#f8f9fa',
              border: '1px solid #e9ecef',
              borderRadius: '16px 16px 16px 4px',
              fontSize: '14px',
              wordBreak: 'break-word',
              color: '#212529'  
            }}>
              <div style={{ marginBottom: '4px' }}>{qa.answer}</div>
              <div style={{ 
                fontSize: '11px', 
                color: '#6c757d',
                textAlign: 'right'
              }}>
                {formatTime(qa.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Loading */}
        {loading && (
          <div style={{ 
            alignSelf: 'flex-start',
            maxWidth: '90%',
            padding: '8px 12px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #e9ecef',
            borderRadius: '16px 16px 16px 4px',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#212529'
          }}>
            <div style={{ 
              width: '16px', 
              height: '16px', 
              border: '2px solid #f3f3f3',
              borderTop: '2px solid #007bff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            Thinking...
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{ 
          margin: '0 16px',
          padding: '8px 12px',
          backgroundColor: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          color: '#721c24',
          fontSize: '12px'
        }}>
          {error}
        </div>
      )}

      {/* Input Area */}
      <div style={{ 
        padding: '16px',
        borderTop: '1px solid #dee2e6',
        backgroundColor: 'white'
      }}>
        <div style={{ 
          display: 'flex', 
          gap: '8px',
          alignItems: 'flex-end'
        }}>
          <textarea
            placeholder={meetingEnded ? "Ask about meeting discussions, decisions, or action items..." : "Available after meeting ends"}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading || !meetingEnded}
            style={{ 
              flex: 1,
              padding: '8px 12px',
              border: '1px solid #dee2e6',
              borderRadius: '20px',
              fontSize: '14px',
              resize: 'none',
              minHeight: '40px',
              maxHeight: '80px',
              outline: 'none',
              backgroundColor: loading || !meetingEnded ? '#f8f9fa' : 'white',
              color: '#000'   
            }}
            rows={1}
          />
          <button 
            onClick={ask} 
            disabled={loading || !meetingEnded || !question.trim()}
            style={{ 
              padding: '8px 16px',
              backgroundColor: loading || !meetingEnded || !question.trim() ? '#6c757d' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '20px',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: loading || !meetingEnded || !question.trim() ? 'not-allowed' : 'pointer',
              minWidth: '60px',
              height: '40px'
            }}
          >
            {loading ? '...' : 'Ask'}
          </button>
        </div>
        <div style={{ 
          fontSize: '11px', 
          color: '#6c757d', 
          marginTop: '6px',
          textAlign: 'center'
        }}>
          {meetingEnded ? 'Press Enter to send, Shift+Enter for new line' : 'Chat will be enabled after meeting ends'}
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
