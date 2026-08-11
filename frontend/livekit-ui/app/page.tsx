'use client';

import { useRouter } from 'next/navigation';
import React, { useState } from 'react';
import styles from '../styles/Home.module.css';
import { API_CONFIG } from '@/lib/api-config';
import axios from 'axios';

export default function Page() {
  const router = useRouter();
  const [meetingId, setMeetingId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [hostEmail, setHostEmail] = useState("");
  const [emails, setEmails] = useState("");

  const createMeeting = async () => {
    try {
      const res = await axios.post(`${API_CONFIG.MEETINGS_BASE}`, {
        title,
        host_email: hostEmail,
      });
      setMeetingId(res.data.meeting_id);
      alert("Meeting created");
    } catch (err) {
      console.error(err);
      alert("Failed to create meeting");
    }
  };

  const invite = async () => {
    if (!meetingId) {
      alert("Create a meeting first");
      return;
    }
    try {
      await axios.post(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/invite`, {
        emails: emails.split(",").map((e) => e.trim()).filter(Boolean),
      });
      alert("Invites sent");
    } catch (err) {
      console.error(err);
      alert("Failed to send invites");
    }
  };

  const startMeeting = () => {
    if (!meetingId) {
      alert("Create a meeting first");
      return;
    }
    // The actual /start API call happens once the room connection is
    // confirmed, inside PageClientImpl - not here, to avoid calling
    // /start twice for the same meeting.
    router.push(`/rooms/${meetingId}`);
  };

  return (
    <>
      <main className={styles.main} data-lk-theme="default">
        <div className="header">
          <img src="/images/livekit-meet-home.svg" alt="Meeting Helper" width="360" height="45" />
          <h2>Meeting Helper - Built with LiveKit</h2>
        </div>

        <div className={styles.tabContent}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>Create Meeting & Invite</h2>

          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{ border: '1px solid #ccc', padding: '0.5rem', flex: 1 }}
            />
            <input
              placeholder="Host Email"
              value={hostEmail}
              onChange={(e) => setHostEmail(e.target.value)}
              style={{ border: '1px solid #ccc', padding: '0.5rem', width: '200px' }}
            />
            <button onClick={createMeeting} className="lk-button">
              Create
            </button>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <textarea
              placeholder="Invite emails, comma separated"
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              style={{ border: '1px solid #ccc', padding: '0.5rem', width: '100%', minHeight: '80px' }}
            />
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', alignItems: 'center' }}>
              <button onClick={invite} className="lk-button" disabled={!meetingId}>
                Send Invites
              </button>
              <div style={{ fontSize: '0.875rem' }}>
                {meetingId ? `Meeting ID: ${meetingId}` : "No meeting yet"}
              </div>
            </div>
          </div>

          <button
            onClick={startMeeting}
            className="lk-button"
            disabled={!meetingId}
            style={{ width: '100%' }}
          >
            Start Meeting
          </button>
        </div>
      </main>
      <footer data-lk-theme="default">
        Built with{' '}
        <a href="https://livekit.io/cloud?ref=meet" rel="noopener">
          LiveKit Cloud
        </a>
        .
      </footer>
    </>
  );
}