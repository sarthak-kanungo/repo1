import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

/**
 * Tiny JSON-file backed store for tasks. Kept dependency-free on purpose so the
 * environment stays fast to install and easy to reason about. Not intended for
 * concurrent production writes; it is a demonstration persistence layer.
 */
export class TaskStore {
  constructor(filePath) {
    this.filePath = filePath;
    this.tasks = [];
    this.#load();
  }

  #load() {
    if (existsSync(this.filePath)) {
      try {
        this.tasks = JSON.parse(readFileSync(this.filePath, "utf8"));
      } catch {
        this.tasks = [];
      }
    }
  }

  #persist() {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, JSON.stringify(this.tasks, null, 2));
  }

  list() {
    return [...this.tasks].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  create(title) {
    const trimmed = (title ?? "").trim();
    if (!trimmed) {
      throw new ValidationError("title is required");
    }
    const task = {
      id: randomUUID(),
      title: trimmed,
      done: false,
      createdAt: new Date().toISOString(),
    };
    this.tasks.push(task);
    this.#persist();
    return task;
  }

  toggle(id) {
    const task = this.tasks.find((t) => t.id === id);
    if (!task) return null;
    task.done = !task.done;
    this.#persist();
    return task;
  }

  remove(id) {
    const before = this.tasks.length;
    this.tasks = this.tasks.filter((t) => t.id !== id);
    const removed = this.tasks.length !== before;
    if (removed) this.#persist();
    return removed;
  }
}

export class ValidationError extends Error {}
