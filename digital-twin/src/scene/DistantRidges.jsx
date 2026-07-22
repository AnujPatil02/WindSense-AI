import { useMemo } from "react";
import * as THREE from "three";

// Flat layered ridge silhouettes far in the background, like the hazy distant
// mountain layers visible in reference photos (image 4/7) - cheap (3 meshes).
export default function DistantRidges({ isNight }) {
  const layers = useMemo(() => {
    return [
      { dist: -250, height: 22, color: "#9fb3c2", opacity: 0.55 },
      { dist: -320, height: 26, color: "#b7c8d4", opacity: 0.4 },
      { dist: -400, height: 30, color: "#d3dee6", opacity: 0.3 },
    ].map((layer) => {
      const shape = new THREE.Shape();
      shape.moveTo(-500, 0);
      let x = -500;
      while (x < 500) {
        const step = 20 + Math.random() * 25;
        x += step;
        const h = layer.height * (0.4 + Math.random() * 0.6);
        shape.lineTo(x, h);
      }
      shape.lineTo(500, 0);
      shape.closePath();
      return { ...layer, geo: new THREE.ShapeGeometry(shape) };
    });
  }, []);

  return (
    <group>
      {layers.map((l, i) => (
        <mesh key={i} geometry={l.geo} position={[0, 0, l.dist]}>
          <meshBasicMaterial
            color={isNight ? "#1a2550" : l.color}
            transparent
            opacity={isNight ? l.opacity * 0.6 : l.opacity}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  );
}
