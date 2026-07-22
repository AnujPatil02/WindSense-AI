import { useMemo, useRef, useEffect } from "react";
import * as THREE from "three";
import { heightAt, slopeAt } from "./Terrain.jsx";

const COUNT = 3500;
const trunkGeo = new THREE.CylinderGeometry(0.05, 0.08, 0.6, 5);
const pineGeo = new THREE.ConeGeometry(0.4, 1.3, 7);       // tall conifer shape
const roundGeo = new THREE.IcosahedronGeometry(0.5, 1);      // rounded deciduous shape

export default function Forest() {
  const trunkRef = useRef();
  const pineRef = useRef();
  const roundRef = useRef();

  // Split into two groups by type so each gets its own instancedMesh
  const { pinePlacements, roundPlacements } = useMemo(() => {
    const pines = [], rounds = [];
    let attempts = 0;
    while (pines.length + rounds.length < COUNT && attempts < COUNT * 6) {
      attempts++;
      const x = (Math.random() - 0.5) * 300;
      const z = (Math.random() - 0.5) * 300;
      const y = heightAt(x, z);
      const slope = slopeAt(x, z);
      if (y > 11 || slope > 1.4) continue;
      const scale = 0.7 + Math.random() * 0.7;
      const rot = Math.random() * Math.PI * 2;
      const item = { x, y, z, scale, rot };
      if (Math.random() < 0.6) pines.push(item);
      else rounds.push(item);
    }
    return { pinePlacements: pines, roundPlacements: rounds };
  }, []);

  useEffect(() => {
    if (!trunkRef.current || !pineRef.current || !roundRef.current) return;
    const dummy = new THREE.Object3D();
    const all = [...pinePlacements, ...roundPlacements];
    all.forEach((p, i) => {
      dummy.position.set(p.x, p.y + 0.3 * p.scale, p.z);
      dummy.rotation.set(0, p.rot, 0);
      dummy.scale.setScalar(p.scale);
      dummy.updateMatrix();
      trunkRef.current.setMatrixAt(i, dummy.matrix);
    });
    trunkRef.current.instanceMatrix.needsUpdate = true;

    pinePlacements.forEach((p, i) => {
      dummy.position.set(p.x, p.y + 0.95 * p.scale, p.z);
      dummy.rotation.set(0, p.rot, 0);
      dummy.scale.setScalar(p.scale);
      dummy.updateMatrix();
      pineRef.current.setMatrixAt(i, dummy.matrix);
    });
    pineRef.current.instanceMatrix.needsUpdate = true;

    roundPlacements.forEach((p, i) => {
      dummy.position.set(p.x, p.y + 0.85 * p.scale, p.z);
      dummy.rotation.set(0, p.rot, 0);
      dummy.scale.setScalar(p.scale);
      dummy.updateMatrix();
      roundRef.current.setMatrixAt(i, dummy.matrix);
    });
    roundRef.current.instanceMatrix.needsUpdate = true;
  }, [pinePlacements, roundPlacements]);

  const totalCount = pinePlacements.length + roundPlacements.length;

  return (
    <>
      <instancedMesh ref={trunkRef} args={[trunkGeo, undefined, totalCount]} castShadow>
        <meshStandardMaterial color="#5a4632" roughness={0.95} />
      </instancedMesh>
      <instancedMesh ref={pineRef} args={[pineGeo, undefined, pinePlacements.length]} castShadow>
        <meshStandardMaterial color="#355c2a" roughness={0.85} />
      </instancedMesh>
      <instancedMesh ref={roundRef} args={[roundGeo, undefined, roundPlacements.length]} castShadow>
        <meshStandardMaterial color="#4a7a38" roughness={0.85} flatShading />
      </instancedMesh>
    </>
  );
}
