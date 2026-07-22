import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

const STATUS_COLOR = {
  HEALTHY: "#10D97A",
  WARNING: "#F5A623",
  CRITICAL: "#FF3B3B",
};

// Curved airfoil blade: built from a swept cross-section with a slight forward
// curve and pitch twist toward the tip, matching real turbine blade silhouettes
// (wide elegant curve, not a flat angular extrusion).
function buildBladeGeometry() {
  const length = 6.2;
  const segments = 14;

  const curvePoints = [];
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const x = t * length;
    const y = Math.sin(t * Math.PI * 0.5) * 0.6; // slight forward sweep curve
    curvePoints.push(new THREE.Vector3(x, y, 0));
  }
  const spine = new THREE.CatmullRomCurve3(curvePoints);

  const positions = [];
  const indices = [];
  const widthStart = 0.55;
  const widthEnd = 0.04;
  const thickStart = 0.08;
  const thickEnd = 0.015;

  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const center = spine.getPoint(t);
    const w = THREE.MathUtils.lerp(widthStart, widthEnd, Math.pow(t, 0.7));
    const th = THREE.MathUtils.lerp(thickStart, thickEnd, t);
    positions.push(
      center.x, center.y - w * 0.3, center.z - th / 2,
      center.x, center.y + w * 0.7, center.z - th / 2,
      center.x, center.y + w * 0.7, center.z + th / 2,
      center.x, center.y - w * 0.3, center.z + th / 2
    );
  }
  for (let i = 0; i < segments; i++) {
    const a = i * 4;
    const b = (i + 1) * 4;
    for (let k = 0; k < 4; k++) {
      const k2 = (k + 1) % 4;
      indices.push(a + k, b + k, a + k2, b + k, b + k2, a + k2);
    }
  }

  const lofted = new THREE.BufferGeometry();
  lofted.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  lofted.setIndex(indices);
  lofted.computeVertexNormals();
  return lofted;
}

function Blade({ rotationOffset, geometry }) {
  return (
    <group rotation={[0, 0, rotationOffset]}>
      <mesh geometry={geometry} castShadow>
        <meshStandardMaterial color="#f5f7fa" roughness={0.3} metalness={0.1} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

const bladeGeo = buildBladeGeometry();

export default function Turbine({
  position = [0, 0, 0],
  id = "WT-001",
  status = "HEALTHY",
  rotorSpeed = 1.2,
  isNight = false,
  onHover,
  onClick,
}) {
  const rotorRef = useRef();
  const ringRef = useRef();
  const color = STATUS_COLOR[status] || STATUS_COLOR.HEALTHY;
  const TOWER_HEIGHT = 13;

  useFrame((_, delta) => {
    if (rotorRef.current) rotorRef.current.rotation.z += delta * rotorSpeed;
    if (ringRef.current && status === "CRITICAL") {
      const pulse = 1 + Math.sin(Date.now() * 0.005) * 0.15;
      ringRef.current.scale.set(pulse, pulse, pulse);
    }
  });

  return (
    <group
      position={position}
      onPointerOver={(e) => { e.stopPropagation(); onHover?.(id, true); }}
      onPointerOut={(e) => { e.stopPropagation(); onHover?.(id, false); }}
      onClick={(e) => { e.stopPropagation(); onClick?.(id); }}
    >
      <mesh position={[0, TOWER_HEIGHT / 2, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.22, 0.5, TOWER_HEIGHT, 16]} />
        <meshStandardMaterial color="#e8eaed" roughness={0.45} metalness={0.35} />
      </mesh>

      <mesh position={[0, TOWER_HEIGHT, 0.5]} castShadow>
        <boxGeometry args={[0.55, 0.55, 2.0]} />
        <meshStandardMaterial color="#dfe2e6" roughness={0.4} metalness={0.4} />
      </mesh>

      <mesh position={[0, TOWER_HEIGHT + 0.4, 0.5]}>
        <sphereGeometry args={[0.12, 8, 8]} />
        <meshStandardMaterial color="#ff2020" emissive="#ff2020" emissiveIntensity={isNight ? 2.5 : 0.2} />
      </mesh>

      <group ref={rotorRef} position={[0, TOWER_HEIGHT, 1.5]}>
        <mesh castShadow>
          <sphereGeometry args={[0.32, 16, 16]} />
          <meshStandardMaterial color="#d4d7db" roughness={0.4} metalness={0.5} />
        </mesh>
        <Blade rotationOffset={0} geometry={bladeGeo} />
        <Blade rotationOffset={(2 * Math.PI) / 3} geometry={bladeGeo} />
        <Blade rotationOffset={(4 * Math.PI) / 3} geometry={bladeGeo} />
      </group>

      {/* Health ring - raised well above local terrain noise so it never gets
          half-clipped by uneven ground, depthTest disabled so it always draws fully. */}
      <mesh ref={ringRef} position={[0, 0.6, 0]} rotation={[-Math.PI / 2, 0, 0]} renderOrder={1}>
        <ringGeometry args={[1.1, 1.3, 48]} />
        <meshBasicMaterial color={color} transparent opacity={0.85} depthTest={false} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}