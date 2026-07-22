import { useMemo } from "react";
import * as THREE from "three";
import { heightAt } from "./Terrain.jsx";
import { turbines } from "../data/mockTelemetry.js";

// Trail embedded into terrain: narrower, sits flush with ground, and fades to
// fully transparent at its edges (vertex alpha) so it blends into the
// surrounding terrain color instead of reading as a hard-edged ribbon.
export default function RidgeRoad() {
  const { geometry } = useMemo(() => {
    const waypoints = [];
    for (let i = 0; i < turbines.length; i++) {
      const t = turbines[i];
      waypoints.push(new THREE.Vector3(t.position[0], 0, t.position[2]));
      if (i < turbines.length - 1) {
        const next = turbines[i + 1];
        const midX = (t.position[0] + next.position[0]) / 2 + (Math.random() - 0.5) * 4;
        const midZ = (t.position[2] + next.position[2]) / 2 + (Math.random() - 0.5) * 4;
        waypoints.push(new THREE.Vector3(midX, 0, midZ));
      }
    }
    const curve = new THREE.CatmullRomCurve3(waypoints, false, "catmullrom", 0.1);

    const samples = 220;
    const width = 0.9; // narrower trail, not a wide road
    const crossSlices = 5; // multiple slices across width for the alpha fade
    const points = [];
    for (let i = 0; i <= samples; i++) points.push(curve.getPoint(i / samples));

    const positions = [];
    const alphas = [];
    for (let i = 0; i <= samples; i++) {
      const p = points[i];
      const next = points[Math.min(i + 1, samples)];
      const prev = points[Math.max(i - 1, 0)];
      const tangent = new THREE.Vector3().subVectors(next, prev).normalize();
      if (tangent.lengthSq() < 0.0001) tangent.set(1, 0, 0);
      const normal = new THREE.Vector3(-tangent.z, 0, tangent.x);
      const groundY = heightAt(p.x, p.z) - 0.03;

      for (let s = 0; s <= crossSlices; s++) {
        const u = s / crossSlices; // 0 = left edge, 1 = right edge
        const offset = (u - 0.5) * 2 * width;
        const x = p.x + normal.x * offset;
        const z = p.z + normal.z * offset;
        positions.push(x, groundY, z);
        // fade to 0 alpha at edges, full opacity in center
        const centerDist = Math.abs(u - 0.5) * 2;
        alphas.push(THREE.MathUtils.smoothstep(1 - centerDist, 0, 0.7) * 0.5);
      }
    }

    const stride = crossSlices + 1;
    const indices = [];
    for (let i = 0; i < samples; i++) {
      for (let s = 0; s < crossSlices; s++) {
        const a = i * stride + s, b = i * stride + s + 1;
        const c = (i + 1) * stride + s, d = (i + 1) * stride + s + 1;
        indices.push(a, c, b, b, c, d);
      }
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute("alpha", new THREE.Float32BufferAttribute(alphas, 1));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return { geometry: geo };
  }, []);

  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: { color: { value: new THREE.Color("#8a7a5c") } },
      vertexShader: `
        attribute float alpha;
        varying float vAlpha;
        void main() {
          vAlpha = alpha;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 color;
        varying float vAlpha;
        void main() {
          gl_FragColor = vec4(color, vAlpha);
        }
      `,
      transparent: true,
      depthWrite: false,
    });
  }, []);

  return <mesh geometry={geometry} material={material} renderOrder={2} />;
}
