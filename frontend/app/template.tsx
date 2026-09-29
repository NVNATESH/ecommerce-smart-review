"use client";

import { motion } from "framer-motion";

/**
 * Route transition (template.tsx re-mounts on every navigation):
 * each page fades in and rises slightly with a soft glow settle.
 * Subtle by design — ~0.4s, and disabled under prefers-reduced-motion
 * (globals.css zeroes animation durations for that media query).
 */
export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14, scale: 0.995, filter: "blur(4px)" }}
      animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
      transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
