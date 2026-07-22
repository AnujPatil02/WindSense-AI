import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import Terrain from "./scene/Terrain.jsx";
import RidgeRoad from "./scene/RidgeRoad.jsx";
import Forest from "./scene/Forest.jsx";
import Bushes from "./scene/Bushes.jsx";
import Sky from "./scene/Sky.jsx";
import DistantRidges from "./scene/DistantRidges.jsx";
import TurbineField from "./scene/TurbineField.jsx";
import CameraRig from "./scene/CameraRig.jsx";
import WindParticles from "./scene/WindParticles.jsx";
import TopBar from "./hud/TopBar.jsx";
import FleetPanel from "./hud/FleetPanel.jsx";
import AlertFeed from "./hud/AlertFeed.jsx";
import TurbineCard from "./hud/TurbineCard.jsx";
import ModeToggle from "./hud/ModeToggle.jsx";
import { notifyParent } from "./bridge/streamlitBridge.js";

export default function App() {
  const [hovered, setHovered] = useState(null);
  const [target, setTarget] = useState(null);
  const [isNight, setIsNight] = useState(false);

  const handleSelect = (t) => {
    setTarget({ x: t.position[0], y: t.position[1], z: t.position[2] });
    notifyParent("turbine_click", { id: t.id, status: t.status, healthScore: t.healthScore });
  };

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh" }}>
      <Canvas shadows camera={{ position: [10, 45, 100], fov: 48 }} gl={{ antialias: true }}>
        <Sky isNight={isNight} />
        <DistantRidges isNight={isNight} />
        <directionalLight
          position={[30, 12, -60]}
          intensity={isNight ? 0.7 : 2.2}
          color={isNight ? "#aab8e8" : "#fff4dd"}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-100}
          shadow-camera-right={100}
          shadow-camera-top={100}
          shadow-camera-bottom={-100}
        />
        <ambientLight intensity={isNight ? 1.0 : 0.75} color={isNight ? "#4a5a90" : "#d8e4ea"} />
        <Terrain />
        <RidgeRoad />
        <Forest />
        <Bushes />
        <WindParticles />
        <TurbineField onHoverChange={setHovered} onSelect={handleSelect} isNight={isNight} />
        <CameraRig target={target} />
      </Canvas>

      <TopBar agentsActive={3} />
      <FleetPanel />
      <AlertFeed />
      <TurbineCard turbine={hovered} />
      <ModeToggle
        isNight={isNight}
        onToggleNight={() => setIsNight((v) => !v)}
      />
    </div>
  );
}
