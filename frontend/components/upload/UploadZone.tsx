"use client";

import { useRef, useState } from "react";
import { FileUp, FileText } from "lucide-react";

export function UploadZone({
  onFile,
  disabled,
}: {
  onFile: (file: File) => void;
  disabled?: boolean;
}) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload CSV file"
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) onFile(file);
      }}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition-all ${
        dragging
          ? "border-accent-cyan bg-accent-cyan/5 shadow-glow"
          : "border-white/10 bg-white/[0.03] hover:border-white/25"
      } ${disabled ? "pointer-events-none opacity-50" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = "";
        }}
      />
      <div className="mb-3 rounded-2xl bg-accent-blue/10 p-4 text-accent-cyan">
        <FileUp size={26} />
      </div>
      <p className="font-medium text-slate-200">Drag &amp; drop your CSV here</p>
      <p className="mt-1 text-xs text-slate-500">or click to browse — .csv up to 25 MB</p>
      <p className="mt-3 inline-flex items-center gap-1 text-[11px] text-slate-600">
        <FileText size={11} /> Review columns auto-detected: review, review_text, comment, feedback, text…
      </p>
    </div>
  );
}
