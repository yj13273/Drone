const path = require("path");

function getRunsRoot() {
  return path.resolve(process.env.RUNS_DIR || path.join(process.cwd(), "../runs"));
}

function getRunPaths(runId) {
  assertSafePathSegment(runId, "runId");

  const runDir = path.join(getRunsRoot(), runId);
  const configDir = path.join(runDir, "config");
  const dataDir = path.join(runDir, "data");
  const outputsDir = path.join(runDir, "outputs");
  const plotsDir = path.join(runDir, "plots");
  const logsDir = path.join(runDir, "logs");

  return {
    runDir,
    configDir,
    dataDir,
    outputsDir,
    plotsDir,
    logsDir,
    scenarioConfigFile: path.join(configDir, "scenario.env"),
    pipelineLogFile: path.join(logsDir, "pipeline.log")
  };
}

function resolveSafeRunFile(directory, filename) {
  assertSafeFilename(filename);

  const resolvedDirectory = path.resolve(directory);
  const resolvedFile = path.resolve(resolvedDirectory, filename);

  if (!resolvedFile.startsWith(`${resolvedDirectory}${path.sep}`)) {
    const error = new Error("Invalid filename");
    error.statusCode = 400;
    throw error;
  }

  return resolvedFile;
}

function assertSafePathSegment(value, label) {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.includes("..") ||
    value.includes("/") ||
    value.includes("\\")
  ) {
    const error = new Error(`Invalid ${label}`);
    error.statusCode = 400;
    throw error;
  }
}

function assertSafeFilename(filename) {
  assertSafePathSegment(filename, "filename");
}

module.exports = {
  getRunsRoot,
  getRunPaths,
  resolveSafeRunFile
};
