const fs = require("fs/promises");

const DEFAULTS = {
  gridSize: 100,
  cellScaleM: 1000,
  zScaleM: 100,
  flightZ: 50,
  sensorCount: 20,
  threatTypes: ["radar", "ir", "visual"],
  terrainSeed: 42,
  nfzCount: 3,
  droneName: "IAI Heron",
  placementMode: "greedy"
};

const ALLOWED_THREAT_TYPES = new Set([
  "radar",
  "ir",
  "infrared",
  "visual",
  "acoustic"
]);

const ALLOWED_PLACEMENT_MODES = new Set(["greedy"]);

function validateScenarioConfig(config) {
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    const error = new Error("config object is required");
    error.statusCode = 400;
    throw error;
  }

  const validated = {
    flightZ: getInteger(config.flightZ, DEFAULTS.flightZ, "flightZ", 0, 100),
    sensorCount: getInteger(
      config.sensorCount,
      DEFAULTS.sensorCount,
      "sensorCount",
      0,
      200
    ),
    threatTypes: getThreatTypes(config.threatTypes),
    terrainSeed: getInteger(
      config.terrainSeed,
      DEFAULTS.terrainSeed,
      "terrainSeed",
      0,
      1000000
    ),
    nfzCount: getInteger(config.nfzCount, DEFAULTS.nfzCount, "nfzCount", 0, 10),
    droneName: getString(config.droneName, DEFAULTS.droneName, "droneName"),
    placementMode: getPlacementMode(config.placementMode)
  };

  return validated;
}

async function writeScenarioEnv(filename, config) {
  const lines = [
    `GRID_SIZE=${DEFAULTS.gridSize}`,
    `CELL_SCALE_M=${DEFAULTS.cellScaleM}`,
    `Z_SCALE_M=${DEFAULTS.zScaleM}`,
    `FLIGHT_Z=${config.flightZ}`,
    `SENSOR_COUNT=${config.sensorCount}`,
    `THREAT_TYPES=${config.threatTypes.join(",")}`,
    `TERRAIN_SEED=${config.terrainSeed}`,
    `NFZ_COUNT=${config.nfzCount}`,
    `DRONE_NAME=${config.droneName}`,
    `PLACEMENT_MODE=${config.placementMode}`
  ];

  await fs.writeFile(filename, `${lines.join("\n")}\n`, "utf8");
}

function getInteger(value, defaultValue, fieldName, min, max) {
  const candidate = value === undefined || value === null ? defaultValue : value;
  const number = Number(candidate);

  if (!Number.isInteger(number) || number < min || number > max) {
    const error = new Error(`${fieldName} must be an integer from ${min} to ${max}`);
    error.statusCode = 400;
    throw error;
  }

  return number;
}

function getString(value, defaultValue, fieldName) {
  const candidate = value === undefined || value === null ? defaultValue : value;

  if (typeof candidate !== "string" || candidate.trim().length === 0) {
    const error = new Error(`${fieldName} must be a non-empty string`);
    error.statusCode = 400;
    throw error;
  }

  return candidate.trim();
}

function getThreatTypes(value) {
  const candidate = value === undefined || value === null ? DEFAULTS.threatTypes : value;

  if (!Array.isArray(candidate) || candidate.length === 0) {
    const error = new Error("threatTypes must be a non-empty array");
    error.statusCode = 400;
    throw error;
  }

  const normalized = [];

  for (const threatType of candidate) {
    if (typeof threatType !== "string") {
      const error = new Error("threatTypes must contain strings only");
      error.statusCode = 400;
      throw error;
    }

    const cleanType = threatType.trim().toLowerCase();

    if (!ALLOWED_THREAT_TYPES.has(cleanType)) {
      const error = new Error(`Unsupported threat type: ${threatType}`);
      error.statusCode = 400;
      throw error;
    }

    if (!normalized.includes(cleanType)) {
      normalized.push(cleanType);
    }
  }

  return normalized;
}

function getPlacementMode(value) {
  const placementMode = getString(
    value,
    DEFAULTS.placementMode,
    "placementMode"
  ).toLowerCase();

  if (!ALLOWED_PLACEMENT_MODES.has(placementMode)) {
    const error = new Error(`Unsupported placementMode: ${placementMode}`);
    error.statusCode = 400;
    throw error;
  }

  return placementMode;
}

module.exports = {
  validateScenarioConfig,
  writeScenarioEnv
};
