import { useMemo } from "react";
import * as THREE from "three";
import { Cloud } from "@react-three/drei";

function SkyDome({ isNight }) {
  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        topColor: { value: new THREE.Color(isNight ? "#1a2860" : "#3a7fd0") },
        midColor: { value: new THREE.Color(isNight ? "#283878" : "#bcd8e8") },
        bottomColor: { value: new THREE.Color(isNight ? "#384888" : "#f7d9a0") },
      },
      vertexShader: `
        varying vec3 vWorldPosition;
        void main() {
          vec4 worldPosition = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPosition.xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 topColor;
        uniform vec3 midColor;
        uniform vec3 bottomColor;
        varying vec3 vWorldPosition;
        void main() {
          float h = normalize(vWorldPosition).y;
          float midMix = smoothstep(-0.1, 0.45, h);
          float topMix = smoothstep(0.2, 1.0, h);
          vec3 col = mix(bottomColor, midColor, midMix);
          col = mix(col, topColor, topMix);
          gl_FragColor = vec4(col, 1.0);
        }
      `,
      side: THREE.BackSide,
      depthWrite: false,
    });
  }, [isNight]);

  // Much larger radius (1200, was 400) so the dome's edge never intersects the
  // camera's far clip / fog range - this is what caused the hard horizon line bug.
  return (
    <mesh material={material} renderOrder={-10}>
      <sphereGeometry args={[400, 32, 32]} />
    </mesh>
  );
}

function SunDisc({ isNight }) {
  if (isNight) return null;
  return (
    <mesh position={[150, 90, -900]}>
      <sphereGeometry args={[14, 24, 24]} />
      <meshBasicMaterial color="#fff3d6" toneMapped={false} />
    </mesh>
  );
}

function MoonAndStars({ isNight }) {
  const starPositions = useMemo(() => {
    const pts = [];
    for (let i = 0; i < 500; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI * 0.5;
      const r = 1000;
      pts.push(r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi) + 20, r * Math.sin(phi) * Math.sin(theta));
    }
    return new Float32Array(pts);
  }, []);

  if (!isNight) return null;
  return (
    <>
      <mesh position={[-120, 110, -500]}>
        <sphereGeometry args={[12, 24, 24]} />
        <meshBasicMaterial color="#dfe6ff" toneMapped={false} />
      </mesh>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[starPositions, 3]} />
        </bufferGeometry>
        <pointsMaterial color="#ffffff" size={1.5} sizeAttenuation={false} transparent opacity={0.8} />
      </points>
    </>
  );
}

// Clouds generated on a wide radial grid around the full scene (360°, varying
// distance/height) instead of a hand-placed row - genuinely spreads "all over".
function CloudField({ isNight }) {
  const clouds = useMemo(() => {
    const items = [];
    const ringCount = 3;
    for (let ring = 0; ring < ringCount; ring++) {
      const radius = 140 + ring * 110;
      const count = 6 + ring * 3;
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + ring * 0.4;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius - 40;
        const y = 30 + Math.random() * 18 - ring * 2;
        items.push({
          pos: [x, y, z],
          opacity: 0.55 + Math.random() * 0.3,
          scale: 0.8 + Math.random() * 0.6,
          seg: 30 + Math.floor(Math.random() * 20),
        });
      }
    }
    return items;
  }, []);

  return (
    <>
      {clouds.map((c, i) => (
        <Cloud
          key={i}
          position={c.pos}
          speed={0.03 + Math.random() * 0.03}
          opacity={isNight ? c.opacity * 0.5 : c.opacity}
          segments={c.seg}
          bounds={[26 * c.scale, 7 * c.scale, 9]}
          color={isNight ? "#3a4a78" : "#ffffff"}
        />
      ))}
    </>
  );
}

export default function Sky({ isNight = false }) {
  return (
    <>
      <SkyDome isNight={isNight} />
      <SunDisc isNight={isNight} />
      <MoonAndStars isNight={isNight} />
      <fog attach="fog" args={[isNight ? "#1c2a52" : "#d8e6ee", 70, 320]} />
      <CloudField isNight={isNight} />
    </>
  );
}
