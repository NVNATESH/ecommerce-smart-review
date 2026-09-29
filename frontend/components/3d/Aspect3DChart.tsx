"use client";

/**
 * Meaningful 3D visualization (spec section 39):
 *   X = aspect (grid layout, sorted by sentiment score)
 *   Y = sentiment score = positive% − negative% (−100 .. +100)
 *   Sphere size = mention count; color = dominant aspect sentiment.
 * Aspects with more negative than positive sentiment sit BELOW the amber
 * zero-line, so complaints are as visible as praise. Hover shows the exact
 * split; drag rotates, scroll zooms. Lazy-loaded from the aspects page.
 */
import { Canvas, useFrame, ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { AspectSummary } from "@/lib/types";

const COLOR: Record<string, string> = {
  Positive: "#34D399",
  Negative: "#FB7185",
  Neutral: "#94A3B8",
  Mixed: "#FBBF24",
};

const GROUND_Y = -1.8;
const Y_SCALE = 1.5; // score ±100 → ±1.5 world units

function scoreOf(a: AspectSummary): number {
  return a.positive_percentage - a.negative_percentage;
}

function Points({
  aspects,
  onHover,
}: {
  aspects: AspectSummary[];
  onHover: (a: AspectSummary | null) => void;
}) {
  const group = useRef<THREE.Group>(null);
  useFrame((state) => {
    if (group.current) group.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.15) * 0.1;
  });

  const maxMentions = Math.max(...aspects.map((a) => a.mention_count), 1);
  const cols = Math.ceil(Math.sqrt(aspects.length));

  return (
    <group ref={group}>
      {/* ground grid */}
      <group position={[0, GROUND_Y, 0]}>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[8.4, 5]} />
          <meshBasicMaterial color="#0B1020" transparent opacity={0.5} side={THREE.DoubleSide} />
        </mesh>
        <gridHelper args={[8.4, 8, "#334155", "#1E293B"]} />
      </group>

      {/* zero-line: the positive/negative boundary */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[new Float32Array([-3.6, 0, -2.2, 3.6, 0, -2.2, -3.6, 0, 2.2, 3.6, 0, 2.2]), 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#FBBF24" transparent opacity={0.7} />
      </lineSegments>

      {aspects.map((a, i) => {
        const x = ((i % cols) - (cols - 1) / 2) * 1.9;
        const z = (Math.floor(i / cols) - 0.5) * 1.9 + 0.2;
        const y = (scoreOf(a) / 100) * Y_SCALE;
        const size = 0.09 + (a.mention_count / maxMentions) * 0.2;
        return (
          <group key={a.aspect} position={[x, y, z]}>
            <mesh
              onPointerOver={(e: ThreeEvent<PointerEvent>) => {
                e.stopPropagation();
                onHover(a);
              }}
              onPointerOut={() => onHover(null)}
            >
              <sphereGeometry args={[size, 24, 24]} />
              <meshStandardMaterial
                color={COLOR[a.overall] ?? "#64748B"}
                roughness={0.25}
                metalness={0.5}
                emissive={COLOR[a.overall] ?? "#64748B"}
                emissiveIntensity={0.25}
              />
            </mesh>
            {/* drop-line to the ground so the height reads clearly */}
            {y > GROUND_Y + size + 0.05 && (
              <lineSegments>
                <bufferGeometry>
                  <bufferAttribute
                    attach="attributes-position"
                    args={[new Float32Array([0, -size, 0, 0, GROUND_Y - y, 0]), 3]}
                  />
                </bufferGeometry>
                <lineBasicMaterial color="#475569" transparent opacity={0.5} />
              </lineSegments>
            )}
          </group>
        );
      })}
    </group>
  );
}

export default function Aspect3DChart({ aspects }: { aspects: AspectSummary[] }) {
  const [hovered, setHovered] = useState<AspectSummary | null>(null);
  const sorted = useMemo(
    () => [...aspects].sort((a, b) => scoreOf(b) - scoreOf(a)),
    [aspects],
  );

  if (!aspects.length) return null;
  return (
    <div className="relative h-[420px] w-full overflow-hidden rounded-xl border border-white/5 bg-black/20">
      <Canvas camera={{ position: [0, 1.2, 7], fov: 50 }} dpr={[1, 1.5]}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[3, 6, 3]} intensity={0.9} />
        <Points aspects={sorted} onHover={setHovered} />
        <OrbitControls enablePan={false} minDistance={3.5} maxDistance={13} />
        {hovered && (
          <Html position={[0, 2.1, 0]} center style={{ pointerEvents: "none" }}>
            <div className="glass px-3 py-2 text-xs">
              <p className="font-medium text-slate-100">{hovered.aspect}</p>
              <p className="text-emerald-400">{hovered.positive_percentage}% positive</p>
              <p className="text-rose-400">{hovered.negative_percentage}% negative</p>
              <p className="text-slate-400">{hovered.mention_count} mentions · score {scoreOf(hovered) > 0 ? "+" : ""}{scoreOf(hovered)}</p>
            </div>
          </Html>
        )}
      </Canvas>
      <div className="absolute left-3 top-2 text-[10px] leading-4 text-slate-600">
        X: aspect · Y: sentiment score (positive% − negative%) · size: mentions
        <br />
        above the amber line = loved, below = complained about · drag to rotate, scroll to zoom
      </div>
      <div className="absolute right-3 top-2 flex flex-col gap-1 text-[10px] text-slate-500">
        {sorted.slice(0, 8).map((a) => (
          <span key={a.aspect} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: COLOR[a.overall] ?? "#64748B" }} />
            {a.aspect} ({scoreOf(a) > 0 ? "+" : ""}{scoreOf(a)})
          </span>
        ))}
      </div>
    </div>
  );
}
