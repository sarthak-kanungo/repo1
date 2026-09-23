# repo1

A minimal full-stack **task manager** used to demonstrate a working Cloud Agent
development environment end to end. It has an Express JSON API, a small vanilla
JS frontend, a file-backed store, and automated tests.

## Requirements

- Node.js >= 20 (developed against Node 22)

## Getting started

```bash
npm ci          # install dependencies (uses package-lock.json)
npm run dev     # start the dev server with auto-reload on http://localhost:3000
```

Then open http://localhost:3000 and add, complete, or delete tasks.

## Scripts

| Command        | Description                                        |
| -------------- | -------------------------------------------------- |
| `npm start`    | Start the production server (`src/server.js`).     |
| `npm run dev`  | Start the server with `--watch` auto-reload.       |
| `npm test`     | Run the Node built-in test-runner suite.           |
| `npm run lint` | Lint the codebase with ESLint.                     |

The server listens on `PORT` (default `3000`) and `HOST` (default `0.0.0.0`).

## API

| Method | Path              | Description                     |
| ------ | ----------------- | ------------------------------- |
| GET    | `/api/health`     | Liveness/health check.          |
| GET    | `/api/tasks`      | List tasks (newest first).      |
| POST   | `/api/tasks`      | Create a task `{ "title" }`.    |
| PATCH  | `/api/tasks/:id`  | Toggle a task's done state.     |
| DELETE | `/api/tasks/:id`  | Delete a task.                  |

## Project layout

```
src/       Express app, server entrypoint, and store
public/    Static frontend (HTML/CSS/JS)
test/      Node test-runner API tests
data/      File-backed task storage (git-ignored, created at runtime)
```

## Cloud Agent environment

`.cursor/environment.json` configures the Cloud Agent development environment:
`npm ci` installs dependencies and a `dev-server` terminal runs `npm run dev`.
