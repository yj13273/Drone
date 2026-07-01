const Run = require("../models/Run");
const fileService = require("../services/fileService");
const runManager = require("../services/runManager.service");

async function createRun(req, res, next) {
  try {
    const result = await runManager.createQueuedRun(req.body);

    res.status(201).json({
      runId: result.runId,
      status: result.status
    });
  } catch (error) {
    next(error);
  }
}

async function listRuns(req, res, next) {
  try {
    const query = {};

    if (typeof req.query.clientId === "string" && req.query.clientId.trim()) {
      query.clientId = req.query.clientId.trim();
    }

    const runs = await Run.find(query)
      .sort({ createdAt: -1 })
      .lean();

    res.json({ runs });
  } catch (error) {
    next(error);
  }
}

async function getRun(req, res, next) {
  try {
    const run = await findRunOrThrow(req.params.runId);

    res.json({ run });
  } catch (error) {
    next(error);
  }
}

async function getRunStatus(req, res, next) {
  try {
    const run = await findRunOrThrow(req.params.runId);

    res.json({
      runId: run.runId,
      status: run.status,
      startedAt: run.startedAt,
      finishedAt: run.finishedAt,
      error: run.error
    });
  } catch (error) {
    next(error);
  }
}

async function getRunLogs(req, res, next) {
  try {
    await findRunOrThrow(req.params.runId);
    const log = await fileService.readPipelineLog(req.params.runId);

    res.json({
      runId: req.params.runId,
      log
    });
  } catch (error) {
    next(error);
  }
}

async function getRunPlot(req, res, next) {
  try {
    await findRunOrThrow(req.params.runId);
    await fileService.sendPlot(res, req.params.runId, req.params.filename);
  } catch (error) {
    next(error);
  }
}

async function getRunFile(req, res, next) {
  try {
    await findRunOrThrow(req.params.runId);
    await fileService.sendCsvFile(res, req.params.runId, req.params.filename);
  } catch (error) {
    next(error);
  }
}

async function findRunOrThrow(runId) {
  const run = await Run.findOne({ runId }).lean();

  if (!run) {
    const error = new Error("Run not found");
    error.statusCode = 404;
    throw error;
  }

  return run;
}

module.exports = {
  createRun,
  listRuns,
  getRun,
  getRunStatus,
  getRunLogs,
  getRunPlot,
  getRunFile
};
