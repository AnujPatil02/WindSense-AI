import { useMemo, useRef, useEffect } from "react";
import * as THREE from "three";
import { heightAt, slopeAt } from "./Terrain.jsx";

const COUNT = 1800;
const bushGeo = new THREE.IcosahedronGeometry(0.3, 0);

export default function Bushes() {
  const ref = useRef();

  const placements = useMemo(() => {
    const arr = [];
    let attempts = 0;
    while (arr.length < COUNT && attempts < COUNT * 6) {
      attempts++;
      const x = (Math.random() - 0.5) * 300;
      const z = (Math.random() - 0.5) * 300;
      const y = heightAt(x, z);
      const slope = slopeAt(x, z);
      if (y > 13 || slope > 1.6) continue;
      arr.push({ x, y, z, scale: 0.5 + Math.random() * 0.6, rot: Math.random() * Math.PI * 2 });
    }
    return arr;
  }, []);

  useEffect(() => {
    if (!ref.current) return;
    const dummy = new THREE.Object3D();
    placements.forEach((p, i) => {
      dummy.position.set(p.x, p.y + 0.2, p.z);
      dummy.rotation.set(p.rot * 0.3, p.rot, 0);
      dummy.scale.setScalar(p.scale);
      dummy.updateMatrix();
      ref.current.setMatrixAt(i, dummy.matrix);
    });
    ref.current.instanceMatrix.needsUpdate = true;
  }, [placements]);

  return (
    <instancedMesh ref={ref} args={[bushGeo, undefined, placements.length]} castShadow>
      <meshStandardMaterial color="#3a5e2e" roughness={1} flatShading />
    </instancedMesh>
  );
}
