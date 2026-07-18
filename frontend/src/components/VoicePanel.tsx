"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  VocalBridgeProvider,
  useAgentActions,
  useAIAgent,
  useTranscript,
  useVocalBridge,
} from "@vocalbridgeai/react";
import { ConnectionState } from "@vocalbridgeai/sdk";
import { queryAgent } from "@/lib/api";
import TripSearchIndicator from "@/components/TripSearchIndicator";
import type { Recommendations, TripOption } from "@/types/trip";

function MicOffIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="14"
      height="14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <line x1="2" y1="2" x2="22" y2="22" />
      <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
      <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23" />
      <line x1="12" y1="19" x2="12" y2="22" />
    </svg>
  );
}

type VoicePanelProps = {
  sessionId: string;
  onTripOptions: (options: TripOption[]) => void;
  onTripSelected: (option: TripOption, recommendations: Recommendations) => void;
  onConnectionChange?: (connected: boolean) => void;
  onSearchingChange?: (searching: boolean) => void;
};

function VoiceControls({
  sessionId,
  onTripOptions,
  onTripSelected,
  onConnectionChange,
  onSearchingChange,
}: VoicePanelProps) {
  const { state, connect, disconnect, isMicrophoneEnabled, toggleMicrophone, error } =
    useVocalBridge();
  const { transcript } = useTranscript();
  const { onAction } = useAgentActions();
  const { pendingQuery, respond } = useAIAgent();
  const [status, setStatus] = useState("Ready when you are.");
  const [isSearching, setIsSearching] = useState(false);
  const handlingTurn = useRef<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [typed, setTyped] = useState("");

  const lastEntry = transcript[transcript.length - 1];
  const lastKey = lastEntry ? `${lastEntry.timestamp}-${transcript.length}-${lastEntry.role}` : "";

  // Stream the newest agent reply in with a typewriter effect; user lines snap in.
  useEffect(() => {
    if (!lastEntry) return;
    if (lastEntry.role !== "agent") {
      setTyped(lastEntry.text);
      return;
    }
    const full = lastEntry.text;
    setTyped("");
    let i = 0;
    const id = setInterval(() => {
      i += 2;
      setTyped(full.slice(0, i));
      if (i >= full.length) {
        setTyped(full);
        clearInterval(id);
      }
    }, 18);
    return () => clearInterval(id);
  }, [lastKey]);

  // Keep the conversation pinned to the latest message as it streams.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [transcript, typed, isSearching]);

  useEffect(() => {
    if (!pendingQuery || handlingTurn.current === pendingQuery.turnId) return;

    handlingTurn.current = pendingQuery.turnId;
    const { query, turnId } = pendingQuery;

    (async () => {
      try {
        setIsSearching(true);
        setStatus("Searching travel inventory...");
        const result = await queryAgent(query, sessionId);

        if (result.action === "show_trip_options" && result.payload?.options) {
          onTripOptions(result.payload.options);
          setStatus("Trip options loaded.");
        }
        if (result.action === "select_trip" && result.payload?.option) {
          onTripSelected(result.payload.option, result.payload.recommendations);
          setStatus("Trip selected.");
        }

        respond(turnId, result.response);
      } catch {
        respond(turnId, "Sorry, I had trouble searching for trips. Could you try again?");
        setStatus("Search failed.");
      } finally {
        setIsSearching(false);
        handlingTurn.current = null;
      }
    })();
  }, [pendingQuery, onTripOptions, onTripSelected, respond, sessionId]);

  useEffect(() => {
    onSearchingChange?.(isSearching);
  }, [isSearching, onSearchingChange]);

  useEffect(() => {
    return onAction("show_trip_options", (payload) => {
      if (payload?.options) {
        onTripOptions(payload.options as TripOption[]);
      }
    });
  }, [onAction, onTripOptions]);

  useEffect(() => {
    return onAction("select_trip", (payload) => {
      if (payload?.option && payload?.recommendations) {
        onTripSelected(payload.option as TripOption, payload.recommendations as Recommendations);
      }
    });
  }, [onAction, onTripSelected]);

  const isReady = state === ConnectionState.Connected;
  const listening = isReady && isMicrophoneEnabled;
  const isConnecting =
    state === ConnectionState.Connecting ||
    state === ConnectionState.WaitingForAgent ||
    state === ConnectionState.Reconnecting;
  const isSessionActive = isReady || isConnecting || state === ConnectionState.Disconnecting;

  useEffect(() => {
    onConnectionChange?.(isSessionActive);
  }, [isSessionActive, onConnectionChange]);

  const handleConnect = async () => {
    try {
      setStatus("Connecting to Roam...");
      await connect();
      setStatus("Connected. Start speaking anytime.");
    } catch {
      setStatus("Could not connect. Try again.");
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnect();
      setStatus("Ready when you are.");
    } catch {
      setStatus("Disconnected.");
    }
  };

  const handleToggleMicrophone = async () => {
    if (!isReady) return;
    try {
      await toggleMicrophone();
    } catch {
      setStatus("Microphone unavailable right now.");
    }
  };

  return (
    <div className="border-b border-white/8 px-5 py-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">Voice</p>
          <h2 className="text-sm font-semibold text-white">Talk to Roam</h2>
        </div>
        <span
          className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] ${
            listening
              ? "bg-emerald-500/15 text-emerald-300"
              : isReady
                ? "bg-zinc-700/60 text-zinc-300"
                : isConnecting
                  ? "bg-amber-500/15 text-amber-200"
                  : "bg-zinc-800 text-zinc-400"
          }`}
        >
          {listening ? (
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/70" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
          ) : null}
          {listening ? "Listening" : isReady ? "Muted" : isConnecting ? "Connecting" : "Idle"}
        </span>
      </div>

      <div className="flex gap-2">
        {!isSessionActive ? (
          <button
            type="button"
            onClick={() => void handleConnect()}
            className="flex-1 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200"
          >
            Start planning
          </button>
        ) : (
          <>
            <button
              type="button"
              onClick={() => void handleToggleMicrophone()}
              disabled={!isReady}
              aria-pressed={listening}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                !isReady
                  ? "bg-zinc-800 text-zinc-400"
                  : listening
                    ? "bg-emerald-500 text-black hover:bg-emerald-400"
                    : "bg-zinc-800 text-zinc-200 hover:bg-zinc-700"
              }`}
            >
              {!isReady ? (
                "Connecting..."
              ) : listening ? (
                <>
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-black/50" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-black" />
                  </span>
                  Listening · Tap to mute
                </>
              ) : (
                <>
                  <MicOffIcon />
                  Muted · Tap to speak
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => void handleDisconnect()}
              className="rounded-xl bg-zinc-900 px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800"
            >
              End
            </button>
          </>
        )}
      </div>

      <p className="mt-2 text-[11px] text-zinc-500">{status}</p>
      <button
        type="button"
        onClick={() => void navigator.clipboard?.writeText(sessionId)}
        title="Click to copy the Vocal Bridge session ID"
        className="mt-1 block max-w-full truncate text-left font-mono text-[10px] text-zinc-600 transition hover:text-zinc-400"
      >
        Session: {sessionId}
      </button>
      {isSearching ? (
        <div className="mt-3">
          <TripSearchIndicator compact />
        </div>
      ) : null}
      {error ? <p className="mt-1 text-xs text-red-300">{error.message}</p> : null}

      <div
        ref={scrollRef}
        className="mt-3 max-h-56 space-y-2 overflow-y-auto scroll-smooth rounded-xl bg-black/30 p-3"
      >
        {transcript.length === 0 ? (
          <p className="text-xs leading-relaxed text-zinc-500">
            Try: &quot;I&apos;m flying from LA with a $500 budget for an outdoor weekend.&quot;
          </p>
        ) : (
          transcript.map((entry, index) => {
            const isUser = entry.role === "user";
            const isLast = index === transcript.length - 1;
            const text = isLast ? typed : entry.text;
            const streaming = isLast && !isUser && typed.length < entry.text.length;
            return (
              <div
                key={`${entry.timestamp}-${index}`}
                className={`flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 text-xs leading-relaxed ${
                    isUser
                      ? "rounded-br-sm bg-white text-black"
                      : "rounded-bl-sm bg-zinc-800 text-zinc-100"
                  }`}
                >
                  <span className="mb-0.5 block text-[10px] font-medium uppercase tracking-wide opacity-60">
                    {isUser ? "You" : "Roam"}
                  </span>
                  {text}
                  {streaming ? (
                    <span className="ml-0.5 inline-block h-3 w-1 animate-pulse bg-current align-middle" />
                  ) : null}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default function VoicePanel(props: VoicePanelProps) {
  const options = useMemo(
    () => ({
      auth: { tokenUrl: "/api/voice-token" },
      participantName: "Roam User",
      sessionId: props.sessionId,
      debug: false,
    }),
    [props.sessionId],
  );

  return (
    <VocalBridgeProvider options={options}>
      <VoiceControls {...props} />
    </VocalBridgeProvider>
  );
}
