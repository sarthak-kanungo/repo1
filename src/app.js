import express from "express";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { TaskStore, ValidationError } from "./store.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Build the Express application. Accepts the data file path so tests can use an
 * isolated store without touching the real one.
 */
export function createApp({ dataFile } = {}) {
  const store = new TaskStore(dataFile ?? join(__dirname, "..", "data", "tasks.json"));
  const app = express();

  app.use(express.json());
  app.use(express.static(join(__dirname, "..", "public")));

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", uptime: process.uptime() });
  });

  app.get("/api/tasks", (_req, res) => {
    res.json(store.list());
  });

  app.post("/api/tasks", (req, res) => {
    try {
      const task = store.create(req.body?.title);
      res.status(201).json(task);
    } catch (err) {
      if (err instanceof ValidationError) {
        res.status(400).json({ error: err.message });
        return;
      }
      throw err;
    }
  });

  app.patch("/api/tasks/:id", (req, res) => {
    const task = store.toggle(req.params.id);
    if (!task) {
      res.status(404).json({ error: "task not found" });
      return;
    }
    res.json(task);
  });

  app.delete("/api/tasks/:id", (req, res) => {
    const removed = store.remove(req.params.id);
    if (!removed) {
      res.status(404).json({ error: "task not found" });
      return;
    }
    res.status(204).end();
  });

  return app;
}
