import { useEffect, useRef } from "react";
import { useSelector } from "react-redux";

// Hook de sons générés via Web Audio API (aucun fichier .mp3 requis)
// miam : note courte ascendante quand le serpent mange
// level_up : arpège 3 notes tous les 5 points
// boom : son grave descendant en fin de partie

function useSoundEffects() {
  const score = useSelector((state) => state.game.score);
  const gameOver = useSelector((state) => state.game.gameOver);

  const prevScoreRef = useRef(0);
  const prevGameOverRef = useRef(false);
  const audioCtxRef = useRef(null);

  const getCtx = () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  };

  const playTone = (freq, type, startTime, duration, gainStart, gainEnd, ctx) => {
    const osc = ctx.createOscillator();
    const gainNode = ctx.createGain();
    osc.connect(gainNode);
    gainNode.connect(ctx.destination);
    osc.type = type;
    osc.frequency.setValueAtTime(freq, startTime);
    gainNode.gain.setValueAtTime(gainStart, startTime);
    gainNode.gain.exponentialRampToValueAtTime(Math.max(gainEnd, 0.001), startTime + duration);
    osc.start(startTime);
    osc.stop(startTime + duration);
  };

  const playMiam = () => {
    try {
      const ctx = getCtx();
      const now = ctx.currentTime;
      playTone(523, "sine", now, 0.08, 0.25, 0.001, ctx);
      playTone(659, "sine", now + 0.05, 0.1, 0.2, 0.001, ctx);
    } catch (_) { }
  };

  const playLevelUp = () => {
    try {
      const ctx = getCtx();
      const now = ctx.currentTime;
      const notes = [523, 659, 784, 1047];
      notes.forEach((freq, i) => {
        playTone(freq, "sine", now + i * 0.1, 0.12, 0.2, 0.001, ctx);
      });
    } catch (_) { }
  };

  const playBoom = () => {
    try {
      const ctx = getCtx();
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gainNode = ctx.createGain();
      osc.connect(gainNode);
      gainNode.connect(ctx.destination);
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(150, now);
      osc.frequency.exponentialRampToValueAtTime(40, now + 0.4);
      gainNode.gain.setValueAtTime(0.35, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc.start(now);
      osc.stop(now + 0.5);
    } catch (_) { }
  };

  // Réagit aux changements de score
  useEffect(() => {
    if (score > prevScoreRef.current) {
      if (score % 5 === 0) {
        playLevelUp();
      } else {
        playMiam();
      }
    }
    prevScoreRef.current = score;
  }, [score]);

  // Réagit au game over
  useEffect(() => {
    if (gameOver && !prevGameOverRef.current) {
      playBoom();
    }
    prevGameOverRef.current = gameOver;
  }, [gameOver]);
}

export default useSoundEffects;
