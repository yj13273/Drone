const cors = require("cors");
const express = require("express");
const morgan = require("morgan");

const runRoutes = require("./routes/run.routes");

const app = express();

app.use(cors());
app.use(express.json({ limit: "1mb" }));
app.use(morgan("dev"));

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.use("/api/runs", runRoutes);

app.use((req, res) => {
  res.status(404).json({
    error: "Not found",
    path: req.originalUrl
  });
});

app.use((error, _req, res, _next) => {
  const status = error.statusCode || 500;

  res.status(status).json({
    error: error.message || "Internal server error"
  });
});

module.exports = app;
