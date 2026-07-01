const fs = require("fs/promises");
const path = require("path");

const { getRunPaths, resolveSafeRunFile } = require("../utils/paths");

async function createRunDirectories(paths) {
  await Promise.all([
    fs.mkdir(paths.runDir, { recursive: true }),
    fs.mkdir(paths.configDir, { recursive: true }),
    fs.mkdir(paths.dataDir, { recursive: true }),
    fs.mkdir(paths.outputsDir, { recursive: true }),
    fs.mkdir(paths.plotsDir, { recursive: true }),
    fs.mkdir(paths.logsDir, { recursive: true })
  ]);
}

async function readPipelineLog(runId) {
  const paths = getRunPaths(runId);

  try {
    return await fs.readFile(paths.pipelineLogFile, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") {
      return "";
    }

    throw error;
  }
}

async function sendPlot(res, runId, filename) {
  assertExtension(filename, ".png", "Only PNG plot files are allowed");

  const paths = getRunPaths(runId);
  const filePath = resolveSafeRunFile(paths.plotsDir, filename);

  await assertFileExists(filePath);
  res.sendFile(filePath);
}

async function sendCsvFile(res, runId, filename) {
  assertExtension(filename, ".csv", "Only CSV files are allowed");

  const paths = getRunPaths(runId);
  const dataFile = resolveSafeRunFile(paths.dataDir, filename);
  const outputFile = resolveSafeRunFile(paths.outputsDir, filename);

  if (await exists(dataFile)) {
    res.sendFile(dataFile);
    return;
  }

  if (await exists(outputFile)) {
    res.sendFile(outputFile);
    return;
  }

  const error = new Error("File not found");
  error.statusCode = 404;
  throw error;
}

function assertExtension(filename, extension, message) {
  if (path.extname(filename).toLowerCase() !== extension) {
    const error = new Error(message);
    error.statusCode = 400;
    throw error;
  }
}

async function assertFileExists(filePath) {
  if (!(await exists(filePath))) {
    const error = new Error("File not found");
    error.statusCode = 404;
    throw error;
  }
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }

    throw error;
  }
}

module.exports = {
  createRunDirectories,
  readPipelineLog,
  sendPlot,
  sendCsvFile
};
