"use client";

import React, { useState, useEffect, useRef, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Mic,
  MicOff,
  QrCode,
  FlipHorizontal,
  Minus,
  Plus,
  Send,
  Sparkles,
  Smartphone,
  X,
  Copy,
  Check,
  RotateCcw,
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AccessHomeAnalyzer } from "@/components/AccessHomeAnalyzer";

// SpeechRecognition Types
interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

export default function SessionStudioPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.id;

  // Mode and view states
  const [isCompanion, setIsCompanion] = useState(false);
  const [isMirror, setIsMirror] = useState(false);
  const [fontSize, setFontSize] = useState(24);
  const [showQrModal, setShowQrModal] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  // Script & Teleprompter
  const [scriptText, setScriptText] = useState(
    "In my accessibility research project at PICTA, I audited 12 government websites using WCAG 2.1 success criteria. | I conducted hands-on testing with NVDA screen reader, keyboard navigation, and Axe DevTools. | I identified and fixed focus trapping and heading hierarchy issues, improving accessibility compliance across all audited flows."
  );

  // Speech Recognition & Co-Pilot States
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [customQuestion, setCustomQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState("");
  const [isLoadingCopilot, setIsLoadingCopilot] = useState(false);
  const [activeTab, setActiveTab] = useState<"PROMPTER" | "COPILOT">("PROMPTER");

  // Recognition ref
  const recognitionRef = useRef<any>(null);

  // Check URL params for ?role=companion
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get("role") === "companion") {
        setIsCompanion(true);
        setFontSize(32); // Larger text for mobile iPhone 13
      }
    }
  }, []);

  // Web Speech API Initialization
  useEffect(() => {
    if (typeof window === "undefined") return;

    const win = window as IWindow;
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: any) => {
        let interim = "";
        let final = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        const currentText = final || interim;
        if (currentText.trim()) {
          setLiveTranscript(currentText);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Web Speech API is not supported in this browser. You can still type questions directly.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.error(err);
      }
    }
  };

  // Trigger Co-Pilot Answer via /api/copilot
  const handleAskCopilot = async (questionToAsk: string) => {
    const q = questionToAsk.trim();
    if (!q) return;

    setIsLoadingCopilot(true);
    setActiveTab("COPILOT");

    try {
      const res = await fetch("/api/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      const data = await res.json();
      if (res.ok && data.answer) {
        setCopilotAnswer(data.answer);
      } else {
        setCopilotAnswer(`Error: ${data.error || "Failed to generate answer"}`);
      }
    } catch (err) {
      setCopilotAnswer(`Network error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsLoadingCopilot(false);
    }
  };

  const getCompanionUrl = () => {
    if (typeof window === "undefined") return "";
    return `${window.location.origin}/session/${sessionId}?role=companion`;
  };

  const copyCompanionUrl = () => {
    const url = getCompanionUrl();
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  // If in iPhone 13 Companion Fullscreen Mode
  if (isCompanion) {
    return (
      <div className="min-h-screen bg-black text-slate-100 flex flex-col p-4 select-none">
        <header className="flex items-center justify-between pb-3 border-b border-slate-900 text-xs">
          <div className="flex items-center gap-1.5 text-blue-400 font-mono">
            <Smartphone className="w-3.5 h-3.5" strokeWidth={1.75} />
            <span>iPhone 13 Companion</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFontSize((s) => Math.max(18, s - 2))}
              className="px-2 py-1 bg-slate-900 rounded border border-slate-800"
            >
              A-
            </button>
            <button
              onClick={() => setFontSize((s) => Math.min(48, s + 2))}
              className="px-2 py-1 bg-slate-900 rounded border border-slate-800"
            >
              A+
            </button>
            <button
              onClick={() => setIsMirror(!isMirror)}
              className={`p-1 rounded border border-slate-800 ${isMirror ? "text-blue-400" : "text-slate-400"}`}
            >
              <FlipHorizontal className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
          </div>
        </header>

        <main
          className={`flex-1 overflow-y-auto py-6 leading-relaxed ${isMirror ? "-scale-x-100" : ""}`}
          style={{ fontSize: `${fontSize}px` }}
        >
          {copilotAnswer ? (
            <div className="space-y-3">
              <span className="text-xs uppercase font-mono tracking-wider text-emerald-400 block">
                Co-Pilot Answer:
              </span>
              <p className="text-white font-medium">
                {copilotAnswer.split("|").map((clause, idx) => (
                  <span key={idx} className="block mb-2">
                    {clause.trim()}
                  </span>
                ))}
              </p>
            </div>
          ) : (
            <p className="text-slate-200">
              {scriptText.split("|").map((clause, idx) => (
                <span key={idx} className="block mb-2.5">
                  {clause.trim()}
                </span>
              ))}
            </p>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-page)] text-[var(--text-primary)]">
      {/* Top Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-30 px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-blue-500 text-slate-600 dark:text-slate-400"
            aria-label="Back to Sessions"
          >
            <ArrowLeft className="w-4 h-4" strokeWidth={1.75} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xs md:text-sm font-semibold truncate max-w-xs md:max-w-md">
                Co-Pilot Studio: {sessionId}
              </h1>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                Live
              </span>
            </div>
            <p className="text-[11px] text-slate-500">Dual-Mode Teleprompter & Groq LLM Assistant</p>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2">
          {/* Font Controls */}
          <div className="flex items-center border border-slate-200 dark:border-slate-800 rounded-lg p-0.5 bg-white dark:bg-slate-900">
            <button
              onClick={() => setFontSize((s) => Math.max(16, s - 2))}
              className="p-1 text-slate-600 dark:text-slate-400 hover:text-blue-600"
              title="Decrease Font Size"
            >
              <Minus className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
            <span className="text-[11px] font-mono px-1.5 text-slate-500">{fontSize}px</span>
            <button
              onClick={() => setFontSize((s) => Math.min(44, s + 2))}
              className="p-1 text-slate-600 dark:text-slate-400 hover:text-blue-600"
              title="Increase Font Size"
            >
              <Plus className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
          </div>

          {/* Mirror Toggle */}
          <button
            onClick={() => setIsMirror(!isMirror)}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors ${
              isMirror
                ? "bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border-blue-400"
                : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-blue-400"
            }`}
            title="Mirror for Bezel Teleprompter Glass"
          >
            <FlipHorizontal className="w-4 h-4" strokeWidth={1.75} />
            <span className="hidden md:inline text-[11px]">Mirror</span>
          </button>

          {/* QR Code Share for iPhone 13 */}
          <button
            onClick={() => setShowQrModal(true)}
            className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-blue-500 flex items-center gap-1.5 text-xs font-medium"
            title="Pair with iPhone 13 via QR Code"
          >
            <QrCode className="w-4 h-4 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
            <span className="hidden sm:inline text-[11px]">iPhone Companion</span>
          </button>

          <AccessHomeAnalyzer />
          <ThemeToggle />
        </div>
      </header>

      {/* Studio Grid Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Teleprompter / Co-Pilot Display (8 cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-3">
          {/* Tabs: Teleprompter Script vs Co-Pilot Answer */}
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("PROMPTER")}
                className={`text-xs font-semibold px-3 py-1.5 rounded-md transition-colors ${
                  activeTab === "PROMPTER"
                    ? "bg-blue-600 text-white"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                Teleprompter Script
              </button>
              <button
                onClick={() => setActiveTab("COPILOT")}
                className={`text-xs font-semibold px-3 py-1.5 rounded-md transition-colors ${
                  activeTab === "COPILOT"
                    ? "bg-blue-600 text-white"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                Co-Pilot AI Response
              </button>
            </div>

            <div className="text-[11px] text-slate-500">
              {isMirror ? "Mirror Mode Active" : "Direct View"}
            </div>
          </div>

          {/* Prompter Canvas (Black OLED Background for High Contrast) */}
          <div
            className={`flex-1 min-h-[380px] p-6 rounded-xl border border-slate-800 bg-black text-slate-100 shadow-inner overflow-y-auto leading-relaxed select-text transition-transform ${
              isMirror ? "-scale-x-100" : ""
            }`}
            style={{ fontSize: `${fontSize}px` }}
          >
            {activeTab === "PROMPTER" ? (
              <div>
                {scriptText.split("|").map((chunk, idx) => (
                  <p key={idx} className="mb-4 text-slate-100 font-medium">
                    {chunk.trim()}
                  </p>
                ))}
              </div>
            ) : (
              <div>
                {isLoadingCopilot ? (
                  <div className="flex items-center gap-2 text-blue-400 text-base font-mono py-12 justify-center">
                    <Sparkles className="w-5 h-5 animate-pulse" strokeWidth={1.75} />
                    <span>Streaming response from Groq gpt-oss-120b...</span>
                  </div>
                ) : copilotAnswer ? (
                  <div className="space-y-4">
                    <span className="text-xs uppercase font-mono tracking-wider text-emerald-400 block border-b border-slate-800 pb-1">
                      Ready to Speak:
                    </span>
                    {copilotAnswer.split("|").map((chunk, idx) => (
                      <p key={idx} className="mb-3 text-slate-100 font-medium">
                        • {chunk.trim()}
                      </p>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-600 text-base">
                    No answer generated yet. Speak or type an interview question on the right.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Script Editor Area */}
          <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
            <label className="text-[11px] font-semibold uppercase text-slate-500 flex items-center justify-between">
              <span>Edit Teleprompter Script (Use &quot;|&quot; for natural breath pauses)</span>
              <button
                onClick={() => setScriptText("")}
                className="text-slate-400 hover:text-rose-500 text-[10px]"
              >
                Clear Script
              </button>
            </label>
            <textarea
              value={scriptText}
              onChange={(e) => setScriptText(e.target.value)}
              rows={3}
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono resize-none"
            />
          </div>
        </div>

        {/* Right Column: Live Audio & Question Assistant (4 cols) */}
        <div className="lg:col-span-4 flex flex-col space-y-4">
          {/* Live Speech Recognition Panel */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Mic className="w-4 h-4 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
                <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-100">Live Speech Listener</h2>
              </div>
              <button
                onClick={toggleListening}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold flex items-center gap-1 transition-colors ${
                  isListening
                    ? "bg-rose-600 text-white animate-pulse"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-blue-600 hover:text-white"
                }`}
              >
                {isListening ? (
                  <>
                    <MicOff className="w-3 h-3" strokeWidth={1.75} />
                    <span>Stop</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-3 h-3" strokeWidth={1.75} />
                    <span>Start Mic</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 min-h-[90px] text-xs font-mono text-slate-700 dark:text-slate-300">
              {liveTranscript || (
                <span className="text-slate-400 italic">
                  {isListening ? "Listening to interviewer speech..." : "Microphone idle. Click Start Mic."}
                </span>
              )}
            </div>

            {liveTranscript && (
              <button
                onClick={() => handleAskCopilot(liveTranscript)}
                disabled={isLoadingCopilot}
                className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" strokeWidth={1.75} />
                <span>Ask Co-Pilot About This Question</span>
              </button>
            )}
          </div>

          {/* Manual Question Input */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2.5">
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-100">Direct Question Prompt</h2>
            <textarea
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
              placeholder="e.g. Tell me about a time you audited web accessibility with NVDA..."
              rows={3}
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={() => handleAskCopilot(customQuestion)}
              disabled={isLoadingCopilot || !customQuestion.trim()}
              className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" strokeWidth={1.75} />
              <span>Generate Spoken Answer</span>
            </button>
          </div>

          {/* Quick Interview Starters */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
            <span className="text-[11px] font-semibold uppercase text-slate-500">Quick Interview Starters</span>
            <div className="space-y-1.5">
              {[
                "Tell me about your experience with WCAG 2.2 and NVDA.",
                "How do you optimize faster-whisper on NVIDIA RTX 2050 CUDA?",
                "How did your 2 years in LATAM Airlines SGSO influence your QA mindset?",
              ].map((starter, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setCustomQuestion(starter);
                    handleAskCopilot(starter);
                  }}
                  className="w-full text-left p-2 rounded border border-slate-200 dark:border-slate-800 hover:border-blue-400 text-[11px] text-slate-700 dark:text-slate-300 transition-colors"
                >
                  {starter}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* QR Code Sharing Modal */}
      {showQrModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <QrCode className="w-4 h-4 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  Scan on iPhone 13
                </h2>
              </div>
              <button
                onClick={() => setShowQrModal(false)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" strokeWidth={1.75} />
              </button>
            </div>

            <div className="flex justify-center p-4 bg-white rounded-xl border border-slate-200">
              <QRCodeSVG value={getCompanionUrl()} size={200} level="M" />
            </div>

            <p className="text-center text-xs text-slate-500 dark:text-slate-400">
              Open Camera on your iPhone 13 to launch the full-screen OLED teleprompter companion.
            </p>

            <button
              onClick={copyCompanionUrl}
              className="w-full py-2 px-3 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-blue-400 text-xs font-semibold flex items-center justify-center gap-1.5"
            >
              {copiedLink ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.75} />
                  <span>Link Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" strokeWidth={1.75} />
                  <span>Copy Companion URL</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
