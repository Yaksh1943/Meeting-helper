import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { API_CONFIG } from '@/lib/api-config';

interface TranscriptCaptureProps {
  meetingId: number;
  participantName: string;
  isActive: boolean;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function TranscriptCapture({ meetingId, participantName, isActive }: TranscriptCaptureProps) {
  const [isSupported, setIsSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const recognitionRef = useRef<any>(null);
  const meetingStartTimeRef = useRef<number | null>(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setIsSupported(true);
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';
      
      recognitionRef.current.onresult = handleSpeechResult;
      recognitionRef.current.onerror = handleSpeechError;
      recognitionRef.current.onend = handleSpeechEnd;
    }
  }, []);

  useEffect(() => {
    if (isSupported && !permissionGranted) {
      requestMicrophonePermission();
    }
  }, [isSupported]);

  useEffect(() => {
    if (isActive && isSupported && !isListening && permissionGranted) {
      if (!meetingStartTimeRef.current) {
        meetingStartTimeRef.current = Date.now();
      }
      startListening();
    } else if (!isActive && isListening) {
      stopListening();
    }
  }, [isActive, isSupported, permissionGranted]);

  useEffect(() => {
    if (isActive && isSupported && !isListening && permissionGranted) {
      if (!meetingStartTimeRef.current) {
        meetingStartTimeRef.current = Date.now();
      }
      startListening();
    } else if (!isActive && isListening) {
      stopListening();
    }
  }, [isActive, isSupported, permissionGranted]);

  const requestMicrophonePermission = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setPermissionGranted(true);
    } catch (error) {
      console.error('Microphone permission denied:', error);
    }
  };

  const handleSpeechResult = async (event: any) => {
    const transcript = event.results[event.results.length - 1][0].transcript;
    const currentTime = Date.now();
    
    if (!meetingStartTimeRef.current) {
      meetingStartTimeRef.current = currentTime;
    }
    
    const tsStart = Math.floor(meetingStartTimeRef.current / 1000);
    const tsEnd = Math.floor(currentTime / 1000);

    if (transcript.trim()) {
      try {
        await axios.post(`${API_CONFIG.MEETINGS_BASE}/${meetingId}/ingest-transcript`, {
          ts_start: tsStart,
          ts_end: tsEnd,
          speaker: participantName,
          text: transcript.trim(),
        });
        console.log('Transcript sent:', transcript.trim());
      } catch (error) {
        console.error('Failed to send transcript:', error);
      }
    }
  };

  const handleSpeechError = (event: any) => {
    console.error('Speech recognition error:', event.error);
    if (event.error === 'not-allowed') {
      setPermissionGranted(false);
      return;
    }
    if (event.error === 'no-speech' || event.error === 'audio-capture') {
      return;
    }
    setIsListening(false);
  };

  const handleSpeechEnd = () => {
    if (isActive && isSupported && permissionGranted) {
      setTimeout(() => {
        if (isActive) {
          startListening();
        }
      }, 100);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  if (!isSupported) {
    return (
      <div style={{ 
        padding: '12px', 
        backgroundColor: '#fff3cd', 
        border: '1px solid #ffeaa7',
        borderRadius: '8px',
        fontSize: '14px',
        color: '#856404'
      }}>
        Speech recognition not supported in this browser
      </div>
    );
  }

  if (!permissionGranted) {
    return (
      <div style={{ 
        padding: '12px', 
        backgroundColor: '#fff3cd', 
        border: '1px solid #ffeaa7',
        borderRadius: '8px',
        fontSize: '14px',
        color: '#856404'
      }}>
        <div style={{ marginBottom: '8px' }}>Microphone access required for transcription</div>
        <button 
          onClick={requestMicrophonePermission}
          style={{
            padding: '6px 12px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          Grant Permission
        </button>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '12px', 
      backgroundColor: isListening ? '#d4edda' : '#f8f9fa',
      border: `1px solid ${isListening ? '#c3e6cb' : '#dee2e6'}`,
      borderRadius: '8px',
      fontSize: '14px'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px'
      }}>
        <div 
          style={{ 
            width: '10px', 
            height: '10px', 
            borderRadius: '50%', 
            backgroundColor: isListening ? '#28a745' : '#6c757d'
          }}
        />
        <span style={{ 
          color: '#333',
          fontWeight: '500'
        }}>
          Transcript: {isListening ? 'Recording...' : 'Stopped'}
        </span>
        {isListening && (
          <div style={{
            fontSize: '12px',
            color: '#155724',
            marginLeft: 'auto'
          }}>
            Speaking detected
          </div>
        )}
      </div>
    </div>
  );
}