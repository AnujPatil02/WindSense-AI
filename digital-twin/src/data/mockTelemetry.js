// Power values scaled so the fleet total (3.191 MW avg) matches the updated
// realistic Energy Generation Forecast (5 x 2MW turbines, 10MW rated capacity).
// Health scores match the 67% Fleet Health KPI.
export const turbines = [
  { id: "WT-001", position: [-38.6, 0, 25.1], status: "CRITICAL", healthScore: 37, rul: 93, anomalyScore: 0.94, power: 0.330, windSpeed: 11.8, rotorSpeed: 0.6 },
  { id: "WT-002", position: [-24.3, 0, 18.2], status: "WARNING", healthScore: 61, rul: 84, anomalyScore: 0.71, power: 0.534, windSpeed: 12.1, rotorSpeed: 0.9 },
  { id: "WT-003", position: [-3.4, 0, 22.2], status: "WARNING", healthScore: 72, rul: 88, anomalyScore: 0.45, power: 0.659, windSpeed: 12.6, rotorSpeed: 1.1 },
  { id: "WT-004", position: [12.0, 0, 29.7], status: "HEALTHY", healthScore: 89, rul: 89, anomalyScore: 0.09, power: 0.824, windSpeed: 13.0, rotorSpeed: 1.35 },
  { id: "WT-005", position: [-15.5, 0, 44.9], status: "HEALTHY", healthScore: 96, rul: 83, anomalyScore: 0.06, power: 0.844, windSpeed: 13.2, rotorSpeed: 1.4 },
];