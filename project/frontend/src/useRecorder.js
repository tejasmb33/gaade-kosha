import {useEffect, useRef, useState} from 'react';

export function microphoneError(error) {
  if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
    return 'Microphone access was blocked. Open this page in Chrome or Safari at http://localhost:5173, allow the microphone in site settings, and check macOS System Settings → Privacy & Security → Microphone for that browser.';
  }
  if (error.name === 'NotFoundError') return 'No microphone was found. Connect or enable a microphone, then try again.';
  if (error.name === 'NotReadableError') return 'The microphone could not start. Check your input device in macOS Sound settings and close other apps using it.';
  return error.message || 'Recording failed. Try again or choose an audio file.';
}

export function useRecorder({onReady, onError, onStart}) {
  const [phase, setPhase] = useState('idle');
  const [seconds, setSeconds] = useState(0);
  const [level, setLevel] = useState(0);
  const [device, setDevice] = useState('');
  const current = useRef(null);
  const alive = useRef(true);
  const callbacks = useRef({onReady, onError, onStart});
  callbacks.current = {onReady, onError, onStart};

  function release(session) {
    clearInterval(session.tick);
    clearTimeout(session.limit);
    session.stream?.getTracks().forEach(track => {track.onended = null; track.stop();});
    session.context?.close().catch(() => {});
    if (current.current === session) current.current = null;
  }
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      const session = current.current;
      if (session) {
        session.cancelled = true;
        if (session.recorder?.state !== 'inactive') session.recorder?.stop();
        release(session);
      }
    };
  }, []);

  function stop() {
    const session = current.current;
    if (session?.recorder?.state === 'recording') {
      setPhase('finishing');
      session.recorder.stop(); // final dataavailable arrives before onstop
    }
  }
  async function start() {
    if (current.current) return;
    const session = {chunks: [], bytes: 0};
    current.current = session;
    setPhase('requesting'); setSeconds(0); setLevel(0);
    callbacks.current.onStart();
    try {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        throw Error('This preview cannot record audio. Open http://localhost:5173 in Chrome or Safari (outside the VS Code preview), then allow microphone access. You can also choose an audio file.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({audio: true});
      session.stream = stream;
      if (!alive.current || session.cancelled) {release(session); return;}
      const track = stream.getAudioTracks()[0];
      if (!track || track.readyState !== 'live') throw Error('The microphone returned no active audio track. Check your input device and try again.');
      setDevice(track.label || 'Default microphone');
      const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm'].find(type => MediaRecorder.isTypeSupported(type));
      const recorder = new MediaRecorder(stream, mimeType ? {mimeType} : undefined);
      session.recorder = recorder;
      recorder.ondataavailable = event => {
        if (event.data.size) {session.chunks.push(event.data); session.bytes += event.data.size;}
        if (session.bytes >= 9 * 1024 * 1024 && recorder.state === 'recording') stop();
      };
      recorder.onerror = event => {
        session.failed = true;
        if (alive.current) {
          callbacks.current.onError(microphoneError(event.error || Error('The browser stopped recording unexpectedly. Please try again.')));
          setPhase('idle'); setLevel(0);
        }
        if (recorder.state !== 'inactive') recorder.stop();
        release(session);
      };
      recorder.onstop = () => {
        const duration = (performance.now() - session.started) / 1000;
        const recording = new Blob(session.chunks, {type: recorder.mimeType || session.chunks[0]?.type || 'audio/webm'});
        release(session);
        if (!alive.current || session.cancelled || session.failed) return;
        setPhase('idle'); setLevel(0);
        if (!recording.size || duration < 0.3) {
          callbacks.current.onError('No usable audio was captured. Record for at least a second, speak into the microphone, then press Stop recording.');
          return;
        }
        callbacks.current.onReady(recording, duration);
      };
      track.onended = () => {
        if (recorder.state === 'recording') {
          callbacks.current.onError('The microphone disconnected. Check the captured playback before uploading.');
          stop();
        }
      };
      // Input activity helps distinguish a silent/muted device from a recorder failure.
      try {
        const Context = window.AudioContext || window.webkitAudioContext;
        const context = new Context(); session.context = context;
        await context.resume();
        const analyser = context.createAnalyser(); analyser.fftSize = 512;
        context.createMediaStreamSource(stream).connect(analyser);
        session.analyser = analyser; session.samples = new Uint8Array(analyser.fftSize);
      } catch { /* Input meter is optional; recording does not depend on Web Audio. */ }
      if (!alive.current || session.cancelled) {release(session); return;}
      session.started = performance.now();
      recorder.start(250);
      setPhase('recording');
      session.tick = setInterval(() => {
        if (!alive.current) return;
        setSeconds(Math.floor((performance.now() - session.started) / 1000));
        if (session.analyser) {
          session.analyser.getByteTimeDomainData(session.samples);
          const rms = Math.sqrt(session.samples.reduce((sum, x) => sum + ((x - 128) / 128) ** 2, 0) / session.samples.length);
          setLevel(Math.min(100, Math.round(rms * 500)));
        }
      }, 100);
      session.limit = setTimeout(stop, 89000);
    } catch (error) {
      release(session);
      if (alive.current) {setPhase('idle'); callbacks.current.onError(microphoneError(error));}
    }
  }
  return {start, stop, phase, seconds, level, device};
}
