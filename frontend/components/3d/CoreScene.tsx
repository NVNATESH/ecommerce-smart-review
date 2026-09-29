"use client";

/** Design 3 — NEURAL CORE: a glowing AI core with counter-rotating rings,
 * a particle shell, and an orbiting sentiment constellation. */
import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";

function Core() {
  const wire = useRef<THREE.Mesh>(null);
  const inner = useRef<THREE.Mesh>(null);
  useFrame(({ clock }, delta) => {
    const t = clock.elapsedTime;
    if (wire.current) {
      wire.current.rotation.y += delta * 0.25;
      wire.current.rotation.x = Math.sin(t * 0.4) * 0.2;
    }
    inner.current?.scale.setScalar(1 + Math.sin(t * 2.2) * 0.07);
  });
  return (
    <group>
      <mesh ref={wire}>
        <icosahedronGeometry args={[1.55, 1]} />
        <meshBasicMaterial color="#38BDF8" wireframe transparent opacity={0.55} />
      </mesh>
      <mesh ref={inner}>
        <icosahedronGeometry args={[0.85, 2]} />
        <meshStandardMaterial color="#1E3A8A" emissive="#60A5FA" emissiveIntensity={2.4} roughness={0.2} />
      </mesh>
    </group>
  );
}

function Ring({ radius, color, tilt, speed }: { radius: number; color: string; tilt: number; speed: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    ref.current?.rotateZ(delta * speed);
  });
  return (
    <mesh ref={ref} rotation={[Math.PI / 2 + tilt, 0, 0]}>
      <torusGeometry args={[radius, 0.018, 8, 128]} />
      <meshBasicMaterial color={color} transparent opacity={0.85} />
    </mesh>
  );
}

function Shell({ count = 1400 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = 2.6 + Math.random() * 2.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.cos(phi) * 0.5;
      arr[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    }
    return arr;
  }, [count]);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.1;
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.028}
        color="#7DD3FC"
        transparent
        opacity={0.8}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

const SATS = [
  { color: "#34D399", r: 3.4, speed: 0.5, tilt: 0.5 },
  { color: "#FB7185", r: 3.4, speed: 0.5, tilt: 0.5, phase: Math.PI },
  { color: "#FBBF24", r: 2.6, speed: -0.7, tilt: -0.9, phase: 1.2 },
];

function Satellites() {
  const refs = useRef<(THREE.Mesh | null)[]>([]);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    SATS.forEach((s, i) => {
      const m = refs.current[i];
      if (!m) return;
      const a = t * s.speed + (s.phase ?? 0);
      m.position.set(Math.cos(a) * s.r, Math.sin(a * 0.9) * 0.7 + Math.sin(s.tilt) * 0.4, Math.sin(a) * s.r);
    });
  });
  return (
    <group>
      {SATS.map((s, i) => (
        <mesh key={i} ref={(el) => { refs.current[i] = el; }}>
          <sphereGeometry args={[0.16, 24, 24]} />
          <meshStandardMaterial color={s.color} emissive={s.color} emissiveIntensity={2.2} />
        </mesh>
      ))}
    </group>
  );
}

export default function CoreScene() {
  return (
    <Canvas camera={{ position: [0, 1.4, 7], fov: 50 }} dpr={[1, 1.6]} gl={{ antialias: true, alpha: true }}>
      <color attach="background" args={["#030712"]} />
      <fog attach="fog" args={["#030712", 8, 20]} />
      <Core />
      <Ring radius={2.3} color="#8B5CF6" tilt={0.35} speed={0.5} />
      <Ring radius={2.8} color="#22D3EE" tilt={-0.6} speed={-0.35} />
      <Ring radius={4.2} color="#334155" tilt={0.9} speed={0.15} />
      <Shell />
      <Satellites />
      <OrbitControls enablePan={false} autoRotate autoRotateSpeed={0.5} minDistance={5} maxDistance={14} />
      <EffectComposer>
        <Bloom intensity={1.3} luminanceThreshold={0.15} luminanceSmoothing={0.6} mipmapBlur radius={0.75} />
      </EffectComposer>
    </Canvas>
  );
}
