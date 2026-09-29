"use client";

/**
 * Iris Reveal page transition (user's chosen style, from the Transition Lab):
 * clicking any internal link dips the screen to dark and the NEW page is
 * revealed through a glowing circular lens that expands from the click point.
 *
 * Mechanics: a dark veil overlays the app; an animated CSS mask cuts a
 * growing circular hole in it (the lens), with a glowing ring tracking the
 * lens edge. Navigation happens mid-expansion, so the hole reveals the real
 * new page as it mounts underneath. A global click interceptor gives every
 * internal <Link> the transition without touching call sites; skipped when
 * the user prefers reduced motion.
 */
import { motion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

type Phase = "idle" | "iris";

const NAVIGATE_MS = 220; // veil dips, then the route changes while the lens opens
const IRIS_MS = 0.95; // lens expansion duration

export function TransitionProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [phase, setPhase] = useState<Phase>("idle");
  const [origin, setOrigin] = useState({ x: 50, y: 50 }); // percent of viewport
  const [maxRadius, setMaxRadius] = useState(1200); // px, computed at click
  const phaseRef = useRef<Phase>("idle");
  const prevPath = useRef(pathname);
  const reducedMotion = useRef(false);

  const setPhaseSafe = (p: Phase) => {
    phaseRef.current = p;
    setPhase(p);
  };

  useEffect(() => {
    reducedMotion.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  // Safety: never leave the veil up (it's fully see-through once the lens
  // reaches full radius, so unmounting a bit later is invisible)
  useEffect(() => {
    if (phase !== "iris") return;
    const t = setTimeout(() => setPhaseSafe("idle"), IRIS_MS * 1000 + 350);
    return () => clearTimeout(t);
  }, [phase]);

  // Global click interception for internal links
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (reducedMotion.current || phaseRef.current !== "idle") return;
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as HTMLElement).closest("a");
      if (!a) return;
      const href = a.getAttribute("href");
      if (!href || !href.startsWith("/") || href.startsWith("//") || a.target === "_blank" || a.hasAttribute("download")) return;
      if (href === pathname) return;
      e.preventDefault();
      e.stopPropagation();

      const rect = a.getBoundingClientRect();
      const ox = ((rect.left + rect.width / 2) / window.innerWidth) * 100;
      const oy = ((rect.top + rect.height / 2) / window.innerHeight) * 100;
      setOrigin({ x: ox, y: oy });
      setMaxRadius(Math.hypot(window.innerWidth, window.innerHeight) * 0.62);
      setPhaseSafe("iris");
      window.setTimeout(() => router.push(href), NAVIGATE_MS);
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, [pathname, router]);

  if (phase !== "iris") return <>{children}</>;

  return (
    <>
      {children}
      {/* dark veil with a growing lens hole (mask reveals the new page beneath) */}
      <motion.div
        className="fixed inset-0 z-[200] pointer-events-none"
        initial={{ opacity: 0, "--hole": "0px" }}
        animate={{ opacity: 1, "--hole": `${maxRadius}px` }}
        transition={{
          opacity: { duration: 0.14, ease: "easeOut" },
          "--hole": { duration: IRIS_MS, ease: [0.3, 0, 0.2, 1] },
        }}
        style={
          {
            background: "#030712",
            WebkitMaskImage:
              "radial-gradient(circle var(--hole) at var(--ox) var(--oy), transparent 0px, black var(--hole))",
            maskImage:
              "radial-gradient(circle var(--hole) at var(--ox) var(--oy), transparent 0px, black var(--hole))",
            "--ox": `${origin.x}%`,
            "--oy": `${origin.y}%`,
          } as React.CSSProperties
        }
      />
      {/* glowing ring tracking the lens edge */}
      <motion.span
        className="fixed z-[201] pointer-events-none rounded-full border-2 border-sky-300"
        style={{
          left: `${origin.x}%`,
          top: `${origin.y}%`,
          translateX: "-50%",
          translateY: "-50%",
          boxShadow: "0 0 26px rgba(125,211,252,0.85), inset 0 0 18px rgba(125,211,252,0.5)",
        }}
        initial={{ width: 0, height: 0, opacity: 1 }}
        animate={{ width: maxRadius * 2, height: maxRadius * 2, opacity: 0 }}
        transition={{ duration: IRIS_MS, ease: [0.3, 0, 0.2, 1] }}
      />
    </>
  );
}
