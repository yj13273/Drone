const express = require("express");

const runController = require("../controllers/run.controller");

const router = express.Router();

router.post("/", runController.createRun);
router.get("/", runController.listRuns);
router.get("/:runId", runController.getRun);
router.get("/:runId/status", runController.getRunStatus);
router.get("/:runId/logs", runController.getRunLogs);
router.get("/:runId/plots/:filename", runController.getRunPlot);
router.get("/:runId/files/:filename", runController.getRunFile);

module.exports = router;
