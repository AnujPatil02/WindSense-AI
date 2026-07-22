import { useRef } from "react";
import { useFrame } from "@react-three/fiber";

const COLORS = {
  HEALTHY: "#22d3a8",
  WARNING: "#f5a623",
  CRITICAL: "#ff3b3b",
};

export default function HealthRing({ status = "HEALTHY" }) {
  const ringRef = useRef();
  const color = COLORS[status] || COLORS.HEALTHY;

  useFrame(({ clock }) => {
    if (ringRef.current && status === "CRITICAL") {
      const pulse = 0.7 + Math.sin(clock.elapsedTime * 4) * 0.3;
      ringRef.current.material.emissiveIntensity = pulse * 2;
    }
  });

  return (
    <mesh ref={ringRef} position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[1.3, 1.6, 32]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={status === "CRITICAL" ? 2 : status === "WARNING" ? 1 : 0.6}
        toneMapped={false}
      />
    </mesh>
  );
}
