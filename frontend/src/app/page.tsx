"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Mic,
  FileText,
  Sliders,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Smartphone,
  Eye,
  Plus,
} from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AccessHomeAnalyzer } from "@/components/AccessHomeAnalyzer";

export default function WorkspacePage() {
  const [sessions, setSessions] = useState([
    {
      id: "live-interview-01",
      title: "Senior Accessibility & QA Interview",
      role: "Accessibility Engineer",
      company: "Global Tech",
      date: "Today",
      duration: "45m",
      mode: "INTERVIEW",
    },
    {
      id: "pitch-recording-02",
      title: "VoiceBridge AI Video Pitch",
      role: "Creator",
      company: "Portfolio Showcase",
      date: "Yesterday",
      duration: "5m",
      mode: "SCRIPT",
    },
  ]);

  const [newTitle, setNewTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    const newId = `session-${Date.now().toString().slice(-6)}`;
    setSessions([
      {
        id: newId,
        title: newTitle.trim(),
        role: "Technical Candidate",
        company: "Live Practice",
        date: "Just now",
        duration: "30m",
        mode: "INTERVIEW",
      },
      ...sessions,
    ]);
    setNewTitle("");
    setIsCreating(false);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-page)] text-[var(--text-primary)]">
      {/* Top Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 dark:bg-blue-500 flex items-center justify-center text-white shadow-sm">
            <Mic className="w-4 h-4" strokeWidth={1.75} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-tight">VoiceBridge AI</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                Studio v1.2
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Real-Time Interview Co-Pilot & Web Teleprompter</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <AccessHomeAnalyzer />
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-8 space-y-8">
        {/* Welcome Hero Card */}
        <section className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden">
          <div className="max-w-2xl space-y-2.5">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Technical Interview Studio & Teleprompter
            </h1>
            <p className="text-xs md:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Maintain natural eye contact with your webcam while receiving low-latency spoken English bullet points or teleprompter guidance. Compatible with iPhone 13 via QR Code wireless companion.
            </p>
            <div className="pt-2 flex flex-wrap gap-2.5">
              <button
                onClick={() => setIsCreating(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                <Plus className="w-3.5 h-3.5" strokeWidth={1.75} />
                <span>New Session</span>
              </button>
              <Link
                href="/session/live-interview-01"
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 text-xs font-medium hover:border-blue-400 transition-colors"
              >
                <Mic className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
                <span>Launch Quick Co-Pilot</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Modal / Inline Create Session */}
        {isCreating && (
          <form
            onSubmit={handleCreate}
            className="p-4 rounded-xl border border-blue-300 dark:border-blue-800 bg-blue-50/40 dark:bg-blue-950/20 space-y-3"
          >
            <h2 className="text-xs font-semibold text-blue-950 dark:text-blue-200 uppercase tracking-wider">
              Create New Interview Session
            </h2>
            <div className="flex gap-2">
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Session Name (e.g. Accessibility Lead Interview - Tech Corp)"
                className="flex-1 px-3 py-2 rounded-lg text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-blue-600 dark:bg-blue-500 text-white text-xs font-semibold hover:bg-blue-700"
              >
                Create & Start
              </button>
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Feature Highlights Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="w-7 h-7 rounded-md bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Eye className="w-4 h-4" strokeWidth={1.75} />
            </div>
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-100">Natural Eye Contact</h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Mirror mode and top-center layout aligned directly under your webcam bezel to prevent gaze drift.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="w-7 h-7 rounded-md bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <Smartphone className="w-4 h-4" strokeWidth={1.75} />
            </div>
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-100">iPhone 13 Companion</h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Scan the QR Code to mount your iPhone 13 beneath the monitor for dedicated wireless teleprompter reading.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="w-7 h-7 rounded-md bg-purple-50 dark:bg-purple-950/50 flex items-center justify-center text-purple-600 dark:text-purple-400">
              <ShieldCheck className="w-4 h-4" strokeWidth={1.75} />
            </div>
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-100">WCAG 2.1/2.2 AA/AAA</h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Built-in live accessibility drawer testing headings, landmarks, image alts and NVDA focus states.
            </p>
          </div>
        </section>

        {/* Sessions List */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Saved Sessions & Workspaces
            </h2>
            <span className="text-[11px] text-slate-500">{sessions.length} sessions available</span>
          </div>

          <div className="space-y-2">
            {sessions.map((session) => (
              <Link
                key={session.id}
                href={`/session/${session.id}`}
                className="group flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 dark:hover:border-blue-500 transition-all shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {session.mode === "INTERVIEW" ? (
                      <Mic className="w-4 h-4" strokeWidth={1.75} />
                    ) : (
                      <FileText className="w-4 h-4" strokeWidth={1.75} />
                    )}
                  </div>
                  <div>
                    <h3 className="text-xs md:text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {session.title}
                    </h3>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      <span>{session.company}</span>
                      <span>•</span>
                      <span>{session.role}</span>
                      <span>•</span>
                      <span>{session.date}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                      session.mode === "INTERVIEW"
                        ? "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                        : "bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800"
                    }`}
                  >
                    {session.mode}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" strokeWidth={1.75} />
                </div>
              </Link>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 p-4 text-center text-xs text-slate-500 dark:text-slate-400">
        VoiceBridge AI Web Studio • Designed for Yago Santos Silva • Next.js App Router & Tailwind CSS
      </footer>
    </div>
  );
}
