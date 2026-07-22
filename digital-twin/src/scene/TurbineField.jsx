import Turbine from "./Turbine.jsx";
import { turbines } from "../data/mockTelemetry.js";
import { heightAt } from "./Terrain.jsx";

export default function TurbineField({ onHoverChange, onSelect, isNight }) {
  const handleHover = (id, isHovering) => {
    onHoverChange?.(isHovering ? turbines.find((t) => t.id === id) : null);
  };

  return (
    <group>
      {turbines.map((t) => {
        const groundY = heightAt(t.position[0], t.position[2]);
        const snappedPos = [t.position[0], groundY, t.position[2]];
        return (
          <Turbine
            key={t.id}
            id={t.id}
            position={snappedPos}
            status={t.status}
            rotorSpeed={t.rotorSpeed}
            isNight={isNight}
            onHover={handleHover}
            onClick={() => onSelect?.({ ...t, position: snappedPos })}
          />
        );
      })}
    </group>
  );
}
