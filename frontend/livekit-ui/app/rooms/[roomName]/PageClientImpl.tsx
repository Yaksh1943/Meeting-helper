'use client';

import React from 'react';
import { decodePassphrase } from '@/lib/client-utils';
import { DebugMode } from '@/lib/Debug';
import { KeyboardShortcuts } from '@/lib/KeyboardShortcuts';
import { RecordingIndicator } from '@/lib/RecordingIndicator';
import { SettingsMenu } from '@/lib/SettingsMenu';
import { ConnectionDetails } from '@/lib/types';
import {
  formatChatMessageLinks,
  LocalUserChoices,
  PreJoin,
  RoomContext,
  VideoConference,
} from '@livekit/components-react';
import {
  ExternalE2EEKeyProvider,
  RoomOptions,
  VideoCodec,
  VideoPresets,
  Room,
} from 'livekit-client';
import { useRouter } from 'next/navigation';
import { useSetupE2EE } from '@/lib/useSetupE2EE';
import { useLowCPUOptimizer } from '@/lib/usePerfomanceOptimiser';
import SummaryPanel from '../../components/SummaryPanel';
import QAChatPanel from '../../components/QAChatPanel';
import TranscriptCapture from '../../components/TranscriptCapture';
import axios from 'axios';
import { API_CONFIG } from '@/lib/api-config';

const CONN_DETAILS_ENDPOINT = API_CONFIG.CONNECTION_DETAILS;
const SHOW_SETTINGS_MENU = process.env.NEXT_PUBLIC_SHOW_SETTINGS_MENU == 'true';

export function PageClientImpl(props: {
  roomName: string;
  region?: string;
  hq: boolean;
  codec: VideoCodec;
}) {
  const [preJoinChoices, setPreJoinChoices] = React.useState<LocalUserChoices>();
  const [connectionDetails, setConnectionDetails] = React.useState<ConnectionDetails>();

  const preJoinDefaults = React.useMemo(
    () => ({
      username: '',
      videoEnabled: true,
      audioEnabled: true,
    }),
    [],
  );

  const handlePreJoinSubmit = React.useCallback(async (values: LocalUserChoices) => {
    setPreJoinChoices(values);
    const url = new URL(CONN_DETAILS_ENDPOINT);
    url.searchParams.append('roomName', props.roomName);
    url.searchParams.append('participantName', values.username);
    if (props.region) {
      url.searchParams.append('region', props.region);
    }
    const resp = await fetch(url.toString());
    const data = await resp.json();
    setConnectionDetails(data);
  }, []);

  return (
    <main data-lk-theme="default" style={{ height: '100%' }}>
      {!connectionDetails || !preJoinChoices ? (
        <div style={{ display: 'grid', placeItems: 'center', height: '100%' }}>
          <PreJoin defaults={preJoinDefaults} onSubmit={handlePreJoinSubmit} onError={console.error} />
        </div>
      ) : (
        <VideoConferenceComponent
          connectionDetails={connectionDetails}
          userChoices={preJoinChoices}
          options={{ codec: props.codec, hq: props.hq }}
          roomName={props.roomName}
        />
      )}
    </main>
  );
}

function VideoConferenceComponent(props: {
  userChoices: LocalUserChoices;
  connectionDetails: ConnectionDetails;
  options: { hq: boolean; codec: VideoCodec };
  roomName: string;
}) {
  const keyProvider = new ExternalE2EEKeyProvider();
  const { worker, e2eePassphrase } = useSetupE2EE();
  const e2eeEnabled = !!(e2eePassphrase && worker);

  const [meetingStarted, setMeetingStarted] = React.useState(false);
  const [meetingEnded, setMeetingEnded] = React.useState(false);
  const [finalSummary, setFinalSummary] = React.useState<any>(null);
  const [e2eeSetupComplete, setE2eeSetupComplete] = React.useState(false);

  const meetingId = React.useMemo(() => parseInt(props.roomName), [props.roomName]);

  const roomOptions = React.useMemo((): RoomOptions => {
    let codec: VideoCodec | undefined = props.options.codec ?? 'vp9';
    if (e2eeEnabled && (codec === 'av1' || codec === 'vp9')) {
      codec = undefined;
    }
    return {
      videoCaptureDefaults: {
        deviceId: props.userChoices.videoDeviceId ?? undefined,
        resolution: props.options.hq ? VideoPresets.h2160 : VideoPresets.h720,
      },
      publishDefaults: {
        dtx: false,
        videoSimulcastLayers: props.options.hq
          ? [VideoPresets.h1080, VideoPresets.h720]
          : [VideoPresets.h540, VideoPresets.h216],
        red: !e2eeEnabled,
        videoCodec: codec,
      },
      audioCaptureDefaults: { deviceId: props.userChoices.audioDeviceId ?? undefined },
      adaptiveStream: true,
      dynacast: true,
      e2ee: e2eeEnabled ? { keyProvider, worker } : undefined,
    };
  }, [props.userChoices, props.options, e2eeEnabled]);

  const room = React.useMemo(() => new Room(roomOptions), []);
  const router = useRouter();

  React.useEffect(() => {
    if (e2eeEnabled) {
      keyProvider.setKey(decodePassphrase(e2eePassphrase)).then(() => {
        room.setE2EEEnabled(true).catch(console.error);
        setE2eeSetupComplete(true);
      });
    } else {
      setE2eeSetupComplete(true);
    }
  }, [e2eeEnabled, e2eePassphrase, room]);

  React.useEffect(() => {
    if (!e2eeSetupComplete) return;

    room
      .connect(props.connectionDetails.serverUrl, props.connectionDetails.participantToken, {
        autoSubscribe: true,
      })
      .then(async () => {
        console.log('=== ROOM CONNECTED ===');
        try {
          const res = await axios.post(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/start`);
          console.log('Meeting start response:', res.data);
          setMeetingStarted(true);
        } catch (err) {
          console.error('Failed to start meeting:', err);
        }
      });

    if (props.userChoices.videoEnabled) {
      room.localParticipant.setCameraEnabled(true).catch(console.error);
    }
    if (props.userChoices.audioEnabled) {
      room.localParticipant.setMicrophoneEnabled(true).catch(console.error);
    }
  }, [e2eeSetupComplete, room, props.connectionDetails, props.userChoices, meetingId]);

  const handleLeave = async () => {
    console.log('=== LEAVE BUTTON CLICKED ===');
    if (meetingStarted && !meetingEnded) {
      try {
        setMeetingEnded(true);
        const res = await axios.post(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/end`);
        console.log('Meeting end response:', res.data);
        setFinalSummary(res.data.summary);
      } catch (err) {
        console.error('Failed to end meeting:', err);
      }
    }
    room.disconnect();
    router.push(`/rooms/${props.roomName}/summary`);
  };

  useLowCPUOptimizer(room);

  return (
    <div className="lk-room-container" style={{ display: 'flex', height: '100vh' }}>
      <RoomContext.Provider value={room}>
        <KeyboardShortcuts />

        {/* Main video area */}
        <div style={{ flex: 1 }}>
          <VideoConference
            chatMessageFormatter={formatChatMessageLinks}
            SettingsComponent={SHOW_SETTINGS_MENU ? SettingsMenu : undefined}
          />
          {/* Custom Leave button */}
          <div style={{ position: 'absolute', bottom: 20, left: 20 }}>
            <button
              onClick={handleLeave}
              style={{
                background: '#dc3545',
                color: 'white',
                padding: '10px 16px',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
              }}
            >
              Leave Meeting
            </button>
          </div>
        </div>

        {/* Side panel with live transcript + live summaries */}
        <div
          style={{
            width: '400px',
            backgroundColor: '#f8f9fa',
            padding: '1rem',
            overflowY: 'auto',
            borderLeft: '1px solid #dee2e6',
          }}
        >
          <div style={{ marginBottom: '1rem' }}>
            <TranscriptCapture
              meetingId={meetingId}
              participantName={props.userChoices.username}
              isActive={meetingStarted && !meetingEnded}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <SummaryPanel
              meetingId={meetingId}
              meetingEnded={meetingEnded}
              finalSummary={finalSummary}
            />
          </div>
        </div>

        <DebugMode />
        <RecordingIndicator />
      </RoomContext.Provider>
    </div>
  );
}
