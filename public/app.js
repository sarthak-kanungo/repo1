const listEl = document.getElementById("task-list");
const formEl = document.getElementById("new-task-form");
const inputEl = document.getElementById("new-task-input");
const statsEl = document.getElementById("stats");
const emptyEl = document.getElementById("empty-state");

async function api(path, options) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok && res.status !== 204) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

function render(tasks) {
  listEl.innerHTML = "";
  emptyEl.hidden = tasks.length > 0;

  const done = tasks.filter((t) => t.done).length;
  statsEl.innerHTML = tasks.length
    ? `<span><strong>${tasks.length}</strong> total</span><span><strong>${done}</strong> done</span><span><strong>${tasks.length - done}</strong> open</span>`
    : "";

  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = `task${task.done ? " task--done" : ""}`;

    const toggle = document.createElement("button");
    toggle.className = "task__toggle";
    toggle.setAttribute("aria-pressed", String(task.done));
    toggle.setAttribute("aria-label", task.done ? "Mark as not done" : "Mark as done");
    toggle.addEventListener("click", () => onToggle(task.id));

    const title = document.createElement("span");
    title.className = "task__title";
    title.textContent = task.title;

    const del = document.createElement("button");
    del.className = "task__delete";
    del.textContent = "✕";
    del.setAttribute("aria-label", "Delete task");
    del.addEventListener("click", () => onDelete(task.id));

    li.append(toggle, title, del);
    listEl.append(li);
  }
}

async function refresh() {
  render(await api("/api/tasks"));
}

async function onToggle(id) {
  await api(`/api/tasks/${id}`, { method: "PATCH" });
  await refresh();
}

async function onDelete(id) {
  await api(`/api/tasks/${id}`, { method: "DELETE" });
  await refresh();
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = inputEl.value.trim();
  if (!title) return;
  await api("/api/tasks", { method: "POST", body: JSON.stringify({ title }) });
  inputEl.value = "";
  inputEl.focus();
  await refresh();
});

refresh().catch((err) => {
  statsEl.textContent = `Failed to load tasks: ${err.message}`;
});
