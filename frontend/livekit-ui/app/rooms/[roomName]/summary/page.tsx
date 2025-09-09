'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import axios from 'axios';
import SummaryPanel from '../../../components/SummaryPanel';
import QAChatPanel from '../../../components/QAChatPanel';
import { API_CONFIG } from '@/lib/api-config';

interface FinalSummaryResponse {
  summary: string;
  action_items: string[];
  decisions: string[];
}

export default function SummaryPage() {
  const params = useParams();
  const meetingId = parseInt(params.roomName as string, 10);

  const [finalSummary, setFinalSummary] = useState<FinalSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const fetchFinalSummary = async () => {
      try {
        const res = await axios.get<FinalSummaryResponse>(
          `${API_CONFIG.MEETINGS_BASE}/${meetingId}/final-summary`
        );
        setFinalSummary(res.data);
      } catch (err) {
        console.error('Failed to fetch final summary:', err);
        setError('Could not load final summary');
      } finally {
        setLoading(false);
      }
    };

    if (meetingId) {
      fetchFinalSummary();
    }
  }, [meetingId]);

  const sendSummary = async () => {
    setSending(true);
    setStatus(null);
    try {
      const res = await axios.post(
        `${API_CONFIG.MEETINGS_BASE}/${meetingId}/send-summary`
      );      
      setStatus(`✅ Sent to ${res.data.recipients.length} participants`);
    } catch (err) {
      console.error("Failed to send summary:", err);
      setStatus("❌ Failed to send summary");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', height: '100vh' }}>
        <p>Loading summary...</p>
      </div>
    );
  }

  if (error || !finalSummary) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', height: '100vh' }}>
        <p>{error || 'No summary available'}</p>
      </div>
    );
  }

  return (
    <main
      style={{
        display: 'flex',
        height: '100vh',
        backgroundColor: '#f8f9fa',
        padding: '2rem',
        gap: '2rem',
      }}
    >
      {/* Left: Summary + Send button */}
      <div style={{ flex: 1 }}>
        <button
          onClick={sendSummary}
          disabled={sending}
          style={{
            marginBottom: '1rem',
            padding: '8px 16px',
            backgroundColor: sending ? '#6c757d' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: sending ? 'not-allowed' : 'pointer',
          }}
        >
          {sending ? 'Sending...' : 'Send Summary to Participants'}
        </button>
        {status && (
          <p style={{ fontSize: '14px', marginTop: '4px' }}>{status}</p>
        )}

        <SummaryPanel
          meetingId={meetingId}
          meetingEnded={true}
          finalSummary={finalSummary}
        />
      </div>

      {/* Right: Q&A */}
      <div style={{ width: '400px' }}>
        <QAChatPanel meetingId={meetingId} meetingEnded={true} />
      </div>
    </main>
  );
}
