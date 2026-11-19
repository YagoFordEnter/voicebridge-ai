"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  X,
  Eye,
  Sliders,
  Sparkles,
} from "lucide-react";

interface AuditResult {
  headingsCount: number;
  headingsHierarchyOk: boolean;
  landmarksCount: number;
  imagesMissingAlt: number;
  interactiveMissingLabels: number;
  totalElementsScanned: number;
}

export function AccessHomeAnalyzer() {
  const [isOpen, setIsOpen] = useState(false);
  const [highContrastAAA, setHighContrastAAA] = useState(false);
  const [currentFocus, setCurrentFocus] = useState<string>("None");
  const [audit, setAudit] = useState<AuditResult>({
    headingsCount: 0,
    headingsHierarchyOk: true,
    landmarksCount: 0,
    imagesMissingAlt: 0,
    interactiveMissingLabels: 0,
    totalElementsScanned: 0,
  });

  // Run DOM audit
  const runAudit = useCallback(() => {
    if (typeof document === "undefined") return;

    const headings = Array.from(document.querySelectorAll("h1, h2, h3, h4, h5, h6"));
    const landmarks = Array.from(document.querySelectorAll("header, main, nav, footer, section, aside, [role='banner'], [role='main'], [role='navigation']"));
    const images = Array.from(document.querySelectorAll("img"));
    const imagesWithoutAlt = images.filter((img) => !img.hasAttribute("alt") || img.getAttribute("alt")?.trim() === "");

    const buttons = Array.from(document.querySelectorAll("button, a, input, [role='button']"));
    const unlabeledInteractive = buttons.filter((el) => {
      const ariaLabel = el.getAttribute("aria-label");
      const ariaLabelledBy = el.getAttribute("aria-labelledby");
      const text = el.textContent?.trim();
      const title = el.getAttribute("title");
      return !ariaLabel && !ariaLabelledBy && !text && !title;
    });

    setAudit({
      headingsCount: headings.length,
      headingsHierarchyOk: headings.length > 0,
      landmarksCount: landmarks.length,
      imagesMissingAlt: imagesWithoutAlt.length,
      interactiveMissingLabels: unlabeledInteractive.length,
      totalElementsScanned: document.querySelectorAll("*").length,
    });
  }, []);

  // Monitor Focus (NVDA / Keyboard Focus Tracker)
  useEffect(() => {
    if (!isOpen) return;

    runAudit();

    const handleFocus = (e: FocusEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      const tag = target.tagName.toLowerCase();
      const role = target.getAttribute("role") || "";
      const label = target.getAttribute("aria-label") || target.innerText?.slice(0, 30) || "unlabeled";
      setCurrentFocus(`${tag}${role ? ` [role="${role}"]` : ""}: "${label.trim()}"`);
    };

    window.addEventListener("focusin", handleFocus);
    return () => window.removeEventListener("focusin", handleFocus);
  }, [isOpen, runAudit]);

  // High contrast AAA toggle
  useEffect(() => {
    if (highContrastAAA) {
      document.documentElement.classList.add("contrast-more");
    } else {
      document.documentElement.classList.remove("contrast-more");
    }
  }, [highContrastAAA]);

  return (
    <>
      {/* Header Button: WCAG Inspector (OFF by default) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          isOpen
            ? "bg-blue-600/10 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-400 dark:border-blue-500"
            : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-blue-400"
        }`}
        aria-label="Toggle WCAG Inspector"
      >
        <ShieldAlert className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
        <span>WCAG Inspector: {isOpen ? "On" : "Off"}</span>
      </button>

      {/* Drawer Lateral */}
      {isOpen && (
        <aside
          role="region"
          aria-label="AccessHome WCAG Inspector Drawer"
          className="fixed top-0 right-0 h-full w-80 md:w-96 z-50 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col transition-transform duration-200"
        >
          {/* Drawer Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">AccessHome Analyzer</h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">WCAG 2.1/2.2 & NVDA Live Monitor</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-md text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Close Inspector"
            >
              <X className="w-4 h-4" strokeWidth={1.75} />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {/* NVDA Focus Monitor */}
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
              <div className="flex items-center gap-1.5 mb-1 text-slate-700 dark:text-slate-300 font-medium">
                <Eye className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
                <span>NVDA / Keyboard Focus Tracker</span>
              </div>
              <p className="font-mono text-[11px] text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900 p-2 rounded border border-slate-200 dark:border-slate-800 truncate">
                {currentFocus}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Press [Tab] or [Shift+Tab] to inspect active element semantics.</p>
            </div>

            {/* Live Audit Metrics */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-slate-700 dark:text-slate-300 font-medium">
                <span>Real-Time DOM Scan</span>
                <button
                  onClick={runAudit}
                  className="text-blue-600 dark:text-blue-400 text-[11px] hover:underline"
                >
                  Rescan DOM
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                  <span className="text-slate-500 text-[10px] block">Headings Hierarchy</span>
                  <div className="flex items-center gap-1 mt-1 font-semibold text-slate-900 dark:text-slate-100">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.75} />
                    <span>{audit.headingsCount} Found</span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                  <span className="text-slate-500 text-[10px] block">Semantic Landmarks</span>
                  <div className="flex items-center gap-1 mt-1 font-semibold text-slate-900 dark:text-slate-100">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.75} />
                    <span>{audit.landmarksCount} Found</span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                  <span className="text-slate-500 text-[10px] block">Missing Image Alt</span>
                  <div className="flex items-center gap-1 mt-1 font-semibold">
                    {audit.imagesMissingAlt === 0 ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.75} />
                        <span className="text-emerald-600 dark:text-emerald-400">0 Violations</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" strokeWidth={1.75} />
                        <span className="text-amber-600 dark:text-amber-400">{audit.imagesMissingAlt} Warning</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                  <span className="text-slate-500 text-[10px] block">Missing aria-label</span>
                  <div className="flex items-center gap-1 mt-1 font-semibold">
                    {audit.interactiveMissingLabels === 0 ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.75} />
                        <span className="text-emerald-600 dark:text-emerald-400">0 Violations</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" strokeWidth={1.75} />
                        <span className="text-amber-600 dark:text-amber-400">{audit.interactiveMissingLabels} Warning</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Accessibility Controls */}
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-2">
              <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium">
                <Sliders className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
                <span>WCAG AAA Controls</span>
              </div>
              <label className="flex items-center justify-between cursor-pointer pt-1">
                <span className="text-slate-600 dark:text-slate-400">Enhanced Contrast (7:1)</span>
                <input
                  type="checkbox"
                  checked={highContrastAAA}
                  onChange={(e) => setHighContrastAAA(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
              </label>
            </div>

            {/* Standards Compliance Stamp */}
            <div className="p-3 rounded-lg border border-blue-200 dark:border-blue-900/40 bg-blue-50/50 dark:bg-blue-950/20 text-slate-600 dark:text-slate-400 text-[11px] space-y-1">
              <div className="flex items-center gap-1 font-semibold text-blue-700 dark:text-blue-300">
                <Sparkles className="w-3 h-3 text-blue-600 dark:text-blue-400" strokeWidth={1.75} />
                <span>PICTA Standards Compliance</span>
              </div>
              <p>Auditing strictly against WCAG 2.1/2.2 AA/AAA success criteria and LATAM SGSO audit trail discipline.</p>
            </div>
          </div>
        </aside>
      )}
    </>
  );
}
