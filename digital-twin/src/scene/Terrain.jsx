import { useMemo } from "react";
import * as THREE from "three";

function hash(x, z) {
  const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453;
  return s - Math.floor(s);
}
function smoothNoise(x, z) {
  const x0 = Math.floor(x), z0 = Math.floor(z);
  const fx = x - x0, fz = z - z0;
  const a = hash(x0, z0), b = hash(x0 + 1, z0);
  const c = hash(x0, z0 + 1), d = hash(x0 + 1, z0 + 1);
  const ux = fx * fx * (3 - 2 * fx), uz = fz * fz * (3 - 2 * fz);
  return THREE.MathUtils.lerp(THREE.MathUtils.lerp(a, b, ux), THREE.MathUtils.lerp(c, d, ux), uz) * 2 - 1;
}
// Ridged noise: 1 - |noise|, sharpened. Produces sharp ridge crests and carved
// valleys (like real mountain heightmaps) instead of smooth rolling fbm hills.
function ridgedNoise(x, z) {
  return 1 - Math.abs(smoothNoise(x, z));
}
function ridgedFbm(x, z, octaves = 6) {
  let total = 0, amp = 0.6, freq = 1, maxAmp = 0;
  let xx = x, zz = z;
  for (let i = 0; i < octaves; i++) {
    const n = ridgedNoise(xx * freq, zz * freq);
    total += n * n * amp; // square sharpens peaks further
    maxAmp += amp;
    amp *= 0.5;
    freq *= 2.2;
    const a = 0.8;
    const nx = xx * Math.cos(a) - zz * Math.sin(a);
    const nz = xx * Math.sin(a) + zz * Math.cos(a);
    xx = nx; zz = nz;
  }
  return total / maxAmp;
}
function fbm(x, z, octaves = 4) {
  let total = 0, amp = 1, freq = 1, maxAmp = 0;
  let xx = x, zz = z;
  for (let i = 0; i < octaves; i++) {
    total += smoothNoise(xx * freq, zz * freq) * amp;
    maxAmp += amp;
    amp *= 0.48;
    freq *= 2.3;
    const a = 0.7;
    const nx = xx * Math.cos(a) - zz * Math.sin(a);
    const nz = xx * Math.sin(a) + zz * Math.cos(a);
    xx = nx; zz = nz;
  }
  return total / maxAmp;
}

function heightAt(x, z) {
  const macroMask = Math.exp(-Math.pow((x + z * 0.4) / 70, 2)); // overall mountain mass envelope
  const ridges = ridgedFbm(x * 0.02, z * 0.02, 6) * 26;           // sharp peaks/valleys
  const detail = fbm(x * 0.08, z * 0.08, 5) * 2.2;                 // surface roughness
  const micro = fbm(x * 0.35, z * 0.35, 3) * 0.3;
  const base = (ridges * macroMask) + detail + micro;
  const dist = Math.sqrt(x * x + z * z);
  const edge = THREE.MathUtils.smoothstep(dist, 260, 420);
  return base * (1 - edge) - edge * 8;
}

function slopeAt(x, z, step = 1) {
  const hL = heightAt(x - step, z), hR = heightAt(x + step, z);
  const hD = heightAt(x, z - step), hU = heightAt(x, z + step);
  return (Math.abs(hR - hL) + Math.abs(hU - hD)) / (2 * step);
}

function colorAt(y, maxY, x, z, slope) {
  const t = THREE.MathUtils.clamp(y / maxY, 0, 1);
  const low = new THREE.Color("#2a4a26");
  const mid = new THREE.Color("#3f6f31");
  const high = new THREE.Color("#7a6242"); // brownish peak color, was grey-white
  const rock = new THREE.Color("#6b5a3f"); // brown rock, was grey
  const patch = (fbm(x * 0.25, z * 0.25, 2) + 1) * 0.5;
  let base = t < 0.45 ? low.clone().lerp(mid, t / 0.45) : mid.clone().lerp(high, (t - 0.45) / 0.55);
  base = base.lerp(base.clone().multiplyScalar(0.88), patch * 0.2);
  const rockMix = THREE.MathUtils.smoothstep(slope, 0.6, 1.5);
  base = base.lerp(rock, rockMix * 0.75);
  return base;
}

export default function Terrain() {
  const { geometry } = useMemo(() => {
    const size = 900;
    const segments = 240;
    const geo = new THREE.PlaneGeometry(size, size, segments, segments);
    geo.rotateX(-Math.PI / 2);

    const pos = geo.attributes.position;
    let maxY = 0;
    const heights = [];
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i);
      const y = heightAt(x, z);
      heights.push(y);
      if (y > maxY) maxY = y;
    }
    for (let i = 0; i < pos.count; i++) pos.setY(i, heights[i]);

    const colors = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i);
      const slope = slopeAt(x, z);
      const c = colorAt(heights[i], maxY, x, z, slope);
      colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
    }
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    return { geometry: geo };
  }, []);

  return (
    <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial vertexColors roughness={0.95} metalness={0} />
    </mesh>
  );
}

export { heightAt, slopeAt };
