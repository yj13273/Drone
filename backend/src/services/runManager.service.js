const Run = require("../models/Run");
const fileService = require("./fileService");
const scenarioConfig = require("./scenarioConfig.service");
const { createRunId } = require("../utils/ids");
const { getRunPaths } = require("../utils/paths");

async function createQueuedRun(payload) {
  const clientId = validateClientId(payload && payload.clientId);
  const config = scenarioConfig.validateScenarioConfig(payload && payload.config);
  const runId = createRunId();
  const paths = getRunPaths(runId);

  await fileService.createRunDirectories(paths);
  await scenarioConfig.writeScenarioEnv(paths.scenarioConfigFile, config);

  const run = await Run.create({
    runId,
    clientId,
    status: "queued",
    config,
    paths,
    startedAt: null,
    finishedAt: null,
    error: null
  });

  return {
    runId: run.runId,
    status: run.status
  };
}

function validateClientId(clientId) {
  if (typeof clientId !== "string" || clientId.trim().length === 0) {
    const error = new Error("clientId is required");
    error.statusCode = 400;
    throw error;
  }

  if (clientId.length > 128) {
    const error = new Error("clientId is too long");
    error.statusCode = 400;
    throw error;
  }

  return clientId.trim();
}

module.exports = {
  createQueuedRun
};
