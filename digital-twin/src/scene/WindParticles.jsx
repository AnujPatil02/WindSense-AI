import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

const COUNT = 400;
const BOUNDS = { x: 60, y: 12, z: 60 };
const WIND_DIR = new THREE.Vector3(1, 0.05, 0.3).normalize();
const SPEED = 6;

export default function WindParticles() {
  const meshRef = useRef();

  // Per-particle position + phase, generated once
  const particles = useMemo(() => {
    const arr = [];
    for (let i = 0; i < COUNT; i++) {
      arr.push({
        pos: new THREE.Vector3(
          (Math.random() - 0.5) * BOUNDS.x * 2,
          Math.random() * BOUNDS.y + 1,
          (Math.random() - 0.5) * BOUNDS.z * 2
        ),
      });
    }
    return arr;
  }, []);

  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame((_, delta) => {
    if (!meshRef.current) return;
    particles.forEach((p, i) => {
      p.pos.addScaledVector(WIND_DIR, SPEED * delta);
      // wrap around when drifting out of bounds
      if (p.pos.x > BOUNDS.x) p.pos.x = -BOUNDS.x;
      if (p.pos.z > BOUNDS.z) p.pos.z = -BOUNDS.z;
      dummy.position.copy(p.pos);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, COUNT]} frustumCulled={false}>
      <sphereGeometry args={[0.04, 4, 4]} />
      <meshBasicMaterial color="#00D4FF" transparent opacity={0.35} />
    </instancedMesh>
  );
}
