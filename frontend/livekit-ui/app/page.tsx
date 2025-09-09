'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import React, { Suspense, useState } from 'react';
import { encodePassphrase, generateRoomId, randomString } from '@/lib/client-utils';
import styles from '../styles/Home.module.css';
import { API_CONFIG } from '@/lib/api-config';
import axios from 'axios';

function InvitePanel(props: { label: string }) {
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

  const startMeeting = async () => {
    if (!meetingId) {
      alert("Create a meeting first");
      return;
    }
    try {
      // Start meeting on backend
      await axios.post(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/start`);
      
      // Navigate to room
      router.push(`/rooms/${meetingId}`);
    } catch (err) {
      console.error(err);
      alert("Failed to start meeting");
    }
  };

  return (
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
  );
}

function Tabs(props: React.PropsWithChildren<{}>) {
  const searchParams = useSearchParams();
  const tabIndex = searchParams?.get('tab') === 'custom' ? 1 : 0;

  const router = useRouter();
  function onTabSelected(index: number) {
    const tab = index === 1 ? 'custom' : 'meetings';
    router.push(`/?tab=${tab}`);
  }

  let tabs = React.Children.map(props.children, (child, index) => {
    return (
      <button
        className="lk-button"
        onClick={() => {
          if (onTabSelected) {
            onTabSelected(index);
          }
        }}
        aria-pressed={tabIndex === index}
      >
        {/* @ts-ignore */}
        {child?.props.label}
      </button>
    );
  });

  return (
    <div className={styles.tabContainer}>
      <div className={styles.tabSelect}>{tabs}</div>
      {/* @ts-ignore */}
      {props.children[tabIndex]}
    </div>
  );
}

function CustomConnectionTab(props: { label: string }) {
  const router = useRouter();

  const [e2ee, setE2ee] = useState(false);
  const [sharedPassphrase, setSharedPassphrase] = useState(randomString(64));

  const onSubmit: React.FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    const formData = new FormData(event.target as HTMLFormElement);
    const serverUrl = formData.get('serverUrl');
    const token = formData.get('token');
    if (e2ee) {
      router.push(
        `/custom/?liveKitUrl=${serverUrl}&token=${token}#${encodePassphrase(sharedPassphrase)}`,
      );
    } else {
      router.push(`/custom/?liveKitUrl=${serverUrl}&token=${token}`);
    }
  };
  return (
    <form className={styles.tabContent} onSubmit={onSubmit}>
      <p style={{ marginTop: 0 }}>
        Connect LiveKit Meet with a custom server using LiveKit Cloud or LiveKit Server.
      </p>
      <input
        id="serverUrl"
        name="serverUrl"
        type="url"
        placeholder="LiveKit Server URL: wss://*.livekit.cloud"
        required
      />
      <textarea
        id="token"
        name="token"
        placeholder="Token"
        required
        rows={5}
        style={{ padding: '1px 2px', fontSize: 'inherit', lineHeight: 'inherit' }}
      />
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', flexDirection: 'row', gap: '1rem' }}>
          <input
            id="use-e2ee"
            type="checkbox"
            checked={e2ee}
            onChange={(ev) => setE2ee(ev.target.checked)}
          ></input>
          <label htmlFor="use-e2ee">Enable end-to-end encryption</label>
        </div>
        {e2ee && (
          <div style={{ display: 'flex', flexDirection: 'row', gap: '1rem' }}>
            <label htmlFor="passphrase">Passphrase</label>
            <input
              id="passphrase"
              type="password"
              value={sharedPassphrase}
              onChange={(ev) => setSharedPassphrase(ev.target.value)}
            />
          </div>
        )}
      </div>

      <hr
        style={{ width: '100%', borderColor: 'rgba(255, 255, 255, 0.15)', marginBlock: '1rem' }}
      />
      <button
        style={{ paddingInline: '1.25rem', width: '100%' }}
        className="lk-button"
        type="submit"
      >
        Connect
      </button>
    </form>
  );
}

export default function Page() {
  return (
    <>
      <main className={styles.main} data-lk-theme="default">
        <div className="header">
          <img src="/images/livekit-meet-home.svg" alt="LiveKit Meet" width="360" height="45" />
          <h2>
            Meeting Helper - Built with LiveKit
          </h2>
        </div>
        <Suspense fallback="Loading">
          <Tabs>
            <InvitePanel label="Meetings" />
            <CustomConnectionTab label="Custom" />
          </Tabs>
        </Suspense>
      </main>
      <footer data-lk-theme="default">
        Hosted on{' '}
        <a href="https://livekit.io/cloud?ref=meet" rel="noopener">
          LiveKit Cloud
        </a>
        . Source code on{' '}
        <a href="https://github.com/livekit/meet?ref=meet" rel="noopener">
          GitHub
        </a>
        .
      </footer>
    </>
  );
}