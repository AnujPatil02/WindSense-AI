import { useRef, useEffect } from "react";
import { useThree, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import gsap from "gsap";
import * as THREE from "three";

// target: optional {x,y,z} - when set, camera flies to focus on it
export default function CameraRig({ target }) {
  const controls = useRef();
  const { camera } = useThree();
  const idleTimer = useRef(0);
  const isIdling = useRef(false);

  // Auto-orbit when idle (no user interaction for 6s)
  useFrame((_, delta) => {
    if (!controls.current) return;
    if (isIdling.current) {
      controls.current.autoRotate = true;
      controls.current.autoRotateSpeed = 0.4; // slow cinematic drift
    }
  });

  useEffect(() => {
    const c = controls.current;
    if (!c) return;
    const onStart = () => {
      isIdling.current = false;
      c.autoRotate = false;
      clearTimeout(idleTimer.current);
    };
    const onEnd = () => {
      clearTimeout(idleTimer.current);
      idleTimer.current = setTimeout(() => { isIdling.current = true; }, 6000);
    };
    c.addEventListener("start", onStart);
    c.addEventListener("end", onEnd);
    onEnd(); // arm idle timer on mount
    return () => {
      c.removeEventListener("start", onStart);
      c.removeEventListener("end", onEnd);
      clearTimeout(idleTimer.current);
    };
  }, []);

  // Fly camera to clicked turbine
  useEffect(() => {
    if (!target || !controls.current) return;
    const c = controls.current;
    c.autoRotate = false;

    const flyPos = {
      x: target.x + 24,
      y: target.y + 16,
      z: target.z + 30,
    };

    gsap.to(camera.position, {
      x: flyPos.x,
      y: flyPos.y,
      z: flyPos.z,
      duration: 0.85,
      ease: "power2.inOut",
    });
    gsap.to(c.target, {
      x: target.x,
      y: target.y + 8,
      z: target.z,
      duration: 0.85,
      ease: "power2.inOut",
      onUpdate: () => c.update(),
    });
  }, [target, camera]);

  return (
    <OrbitControls
      ref={controls}
      enableDamping
      dampingFactor={0.08}
      minDistance={6}
      maxDistance={160}
      maxPolarAngle={Math.PI / 2.05}
      target={[-14, 16, 28]}
    />
  );
}
