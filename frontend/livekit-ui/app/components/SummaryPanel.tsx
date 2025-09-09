import React, { useEffect, useState } from "react";
import axios from "axios";
import { API_CONFIG } from '@/lib/api-config';

interface Summary {
  id: number;
  meeting_id: number;
  start_min: number;
  end_min: number;
  type: string;
  text: string;
}

export default function SummaryPanel({ 
  meetingId, 
  meetingEnded, 
  finalSummary 
}: { 
  meetingId: number;
  meetingEnded: boolean;
  finalSummary: any;
}) {
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!meetingId) return;
    fetchSummaries();
    const id = setInterval(fetchSummaries, 10000);
    return () => clearInterval(id);
  }, [meetingId]);

  const fetchSummaries = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/summaries`);
      setSummaries(res.data || []);
    } catch (err) {
      console.error('Failed to fetch summaries:', err);
      setError('Failed to load summaries');
    } finally {
      setLoading(false);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'final': return '#28a745';
      case 'timeline': return '#007bff';
      case 'action': return '#28a745';
      case 'decision': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const formatTimestamp = (unix: number) => {
  if (!unix) return "";
  const date = new Date(unix * 1000);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

  const liveSummaries = summaries.filter(s => s.type !== 'final');

  return (
    <div style={{ 
      backgroundColor: 'white',
      border: '1px solid #dee2e6', 
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '12px 16px',
        borderBottom: '1px solid #dee2e6',
        backgroundColor: '#f8f9fa',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ 
          fontWeight: 'bold', 
          margin: 0, 
          color: '#333',
          fontSize: '16px'
        }}>
          Meeting Summaries
        </h3>
        {loading && (
          <div style={{ 
            fontSize: '12px', 
            color: '#6c757d',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <div style={{ 
              width: '12px', 
              height: '12px', 
              border: '2px solid #f3f3f3',
              borderTop: '2px solid #007bff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            Loading...
          </div>
        )}
      </div>

      {/* Content */}
      <div style={{ 
        padding: '16px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        {meetingEnded && finalSummary && (
          <div style={{ 
            padding: '16px',
            backgroundColor: '#e8f5e8',
            border: '2px solid #28a745',
            borderRadius: '8px',
            marginBottom: '16px'
          }}>
            <h4 style={{ 
              color: '#155724', 
              margin: '0 0 8px 0',
              fontSize: '16px',
              fontWeight: 'bold'
            }}>
              Final Meeting Summary
            </h4>
            <p style={{ 
              margin: '0 0 8px 0', 
              color: '#333',
              fontSize: '14px',
              lineHeight: '1.4'
            }}>
              {finalSummary.summary}
            </p>
            
            {finalSummary.action_items && finalSummary.action_items.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <h5 style={{ 
                  color: '#155724', 
                  margin: '0 0 6px 0',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}>
                  Action Items:
                </h5>
                <ul style={{ 
                  margin: '0', 
                  paddingLeft: '20px',
                  color: '#333'
                }}>
                  {finalSummary.action_items.map((item: string, i: number) => (
                    <li key={i} style={{ 
                      fontSize: '13px',
                      marginBottom: '4px'
                    }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {finalSummary.decisions && finalSummary.decisions.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <h5 style={{ 
                  color: '#155724', 
                  margin: '0 0 6px 0',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}>
                  Key Decisions:
                </h5>
                <ul style={{ 
                  margin: '0', 
                  paddingLeft: '20px',
                  color: '#333'
                }}>
                  {finalSummary.decisions.map((decision: string, i: number) => (
                    <li key={i} style={{ 
                      fontSize: '13px',
                      marginBottom: '4px'
                    }}>
                      {decision}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {error && (
          <div style={{ 
            padding: '12px',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            color: '#721c24',
            fontSize: '14px',
            marginBottom: '12px'
          }}>
            {error}
            <button 
              onClick={fetchSummaries}
              style={{ 
                marginLeft: '8px',
                padding: '2px 8px',
                fontSize: '12px',
                border: '1px solid #721c24',
                borderRadius: '3px',
                backgroundColor: 'transparent',
                color: '#721c24',
                cursor: 'pointer'
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Live Summaries Section */}
        {!meetingEnded && (
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ 
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#333',
              margin: '0 0 8px 0'
            }}>
              Live Updates
            </h4>
            {liveSummaries.length === 0 && !loading && !error && (
              <div style={{ 
                textAlign: 'center',
                padding: '24px',
                color: '#6c757d',
                fontSize: '14px'
              }}>
                <div style={{ marginBottom: '8px' }}>📝</div>
                <div>No summaries generated yet</div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  Summaries will appear as the meeting progresses
                </div>
              </div>
            )}
          </div>
        )}

        {liveSummaries.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {liveSummaries.map((summary) => (
              <div key={summary.id} style={{ 
                padding: '12px', 
                border: '1px solid #e9ecef', 
                borderRadius: '6px',
                backgroundColor: '#fff',
                borderLeft: `4px solid ${getTypeColor(summary.type)}`
              }}>
                <div style={{ 
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <span style={{ 
                    fontSize: '12px', 
                    fontWeight: 'bold',
                    color: getTypeColor(summary.type),
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {summary.type}
                  </span>
                  <span style={{ 
                    fontSize: '11px', 
                    color: '#6c757d',
                    backgroundColor: '#f8f9fa',
                    padding: '2px 6px',
                    borderRadius: '12px'
                  }}>
                    {formatTimestamp(summary.start_min)} - {formatTimestamp(summary.end_min)}
                  </span>
                </div>
                <div style={{ 
                  color: '#333',
                  fontSize: '14px',
                  lineHeight: '1.4'
                }}>
                  {summary.text}
                </div>
              </div>
            ))}
          </div>
        )}
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