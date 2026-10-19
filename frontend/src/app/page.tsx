
"use client";

import { useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type Goal = {
  id: number;
  title: string;
  description: string | null;
  target_date: string | null;
  status: string;
};

type Task = {
  id: number;
  goal_id: number;
  title: string;
  completed: boolean;
};

type DashboardGoal = Goal & { tasks: Task[] };

const navigation = [
  { name: "Dashboard", icon: "▦" },
  { name: "Journal", icon: "▤" },
  { name: "Goals", icon: "◎" },
  { name: "Tasks", icon: "✓" },
  { name: "Progress", icon: "↗" },
];

export default function Dashboard() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [goals, setGoals] = useState<DashboardGoal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [completingTaskId, setCompletingTaskId] = useState<number | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API_BASE_URL}/goals`);
        if (!response.ok) throw new Error(`Could not load goals (${response.status})`);

        const goalData: Goal[] = await response.json();

        const dashboardGoals = await Promise.all(
          goalData.map(async (goal) => {
            const taskResponse = await fetch(
              `${API_BASE_URL}/goals/${goal.id}/tasks`
            );
            if (!taskResponse.ok) {
              throw new Error(`Could not load tasks for "${goal.title}"`);
            }

            const tasks: Task[] = await taskResponse.json();
            return { ...goal, tasks };
          })
        );

        setGoals(dashboardGoals);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const allTasks = goals.flatMap((goal) => goal.tasks);
  const completedTasks = allTasks.filter((task) => task.completed).length;
  const totalTasks = allTasks.length;
  const remainingTasks = totalTasks - completedTasks;
  const activeGoals = goals.filter((goal) => goal.status === "active").length;
  const overallProgress =
    totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  async function toggleTask(taskId: number) {
    const task = allTasks.find((item) => item.id === taskId);
    if (!task || task.completed || completingTaskId !== null) return;

    try {
      setCompletingTaskId(taskId);
      setError("");

      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
        method: "PATCH",
      });

      if (!response.ok) {
        throw new Error(`Could not complete task (${response.status})`);
      }

      const updatedTask: Task = await response.json();

      setGoals((current) =>
        current.map((goal) => ({
          ...goal,
          tasks: goal.tasks.map((item) =>
            item.id === taskId ? updatedTask : item
          ),
        }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update task.");
    } finally {
      setCompletingTaskId(null);
    }
  }

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">T</div>
          <div>
            <h2>Digital Twin</h2>
            <p>PERSONAL WORKSPACE</p>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <nav className="nav-list">
          {navigation.map((item) => (
            <button
              key={item.name}
              onClick={() => setActivePage(item.name)}
              className={`nav-item ${activePage === item.name ? "active" : ""}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
              {item.name === "Tasks" && (
                <span className="nav-count">{remainingTasks}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="future-label">COMING LATER</div>
          <div className="future-item">◷ &nbsp; Calendar integration</div>
          <div className="future-item">⌘ &nbsp; Activity insights</div>
          <div className="profile">
            <div className="avatar">N</div>
            <div>
              <strong>My Workspace</strong>
              <p>Personal Digital Twin</p>
            </div>
            <span className="profile-dots">···</span>
          </div>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{activePage}</strong>
          </div>
          <div className="topbar-right">
            <span className="status-dot" />
            <span>Local workspace</span>
            <div className="top-avatar">N</div>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">YOUR PERSONAL PROGRESS SPACE</p>
              <h1>{activePage === "Dashboard" ? "Welcome back." : activePage}</h1>
              <p className="subtitle">
                Turn your intentions into action, one step at a time.
              </p>
            </div>
            <button
              className="primary-button"
              onClick={() => setActivePage("Journal")}
            >
              <span>＋</span> New journal entry
            </button>
          </section>

          {loading && <p>Loading your goals and tasks...</p>}
          {error && <p role="alert" style={{ color: "#ff8b8b" }}>{error}</p>}

          {!loading && !error && (
            <>
              <section className="stats-grid">
                <StatCard label="Active goals" value={String(activeGoals)} detail="Goals you're working on" icon="◎" />
                <StatCard label="Total tasks" value={String(totalTasks)} detail={`${completedTasks} completed so far`} icon="☷" />
                <StatCard label="Overall progress" value={`${overallProgress}%`} detail="Based on saved tasks" icon="↗" />
                <StatCard label="Tasks remaining" value={String(remainingTasks)} detail="Tasks not yet completed" icon="◷" />
              </section>

              <section className="content-grid">
                <div className="panel goals-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>My goals</h2>
                      <p>Your goals, broken into manageable steps.</p>
                    </div>
                    <button className="text-button" onClick={() => setActivePage("Goals")}>
                      View all <span>→</span>
                    </button>
                  </div>

                  <div className="goals-list">
                    {goals.length === 0 && <p>No goals found. Create a goal through the API first.</p>}
                    {goals.map((goal, index) => {
                      const completed = goal.tasks.filter((task) => task.completed).length;
                      const total = goal.tasks.length;
                      const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

                      return (
                        <article className="goal-item" key={goal.id}>
                          <div className={`goal-symbol goal-symbol-${index % 3}`}>
                            {["◈", "⌘", "✳"][index % 3]}
                          </div>
                          <div className="goal-body">
                            <div className="goal-title-row">
                              <div>
                                <h3>{goal.title}</h3>
                                <span className="category-label">{goal.status}</span>
                              </div>
                              <strong className="goal-percent">{percent}%</strong>
                            </div>
                            <div className="progress-track">
                              <div
                                className={`progress-fill progress-fill-${index % 3}`}
                                style={{ width: `${percent}%` }}
                              />
                            </div>
                            <p className="goal-meta">
                              {completed} of {total} tasks completed
                            </p>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                </div>

                <div className="panel overview-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Progress overview</h2>
                      <p>Calculated from your saved tasks.</p>
                    </div>
                    <span className="period-chip">All goals</span>
                  </div>
                  <div className="donut-wrap">
                    <div
                      className="donut-chart"
                      style={{
                        background: `conic-gradient(#8b7cff ${overallProgress * 3.6}deg, #293044 0deg)`,
                      }}
                    >
                      <div className="donut-inner">
                        <strong>{overallProgress}%</strong>
                        <span>COMPLETE</span>
                      </div>
                    </div>
                  </div>
                  <div className="overview-legend">
                    <div><span className="legend-dot purple-dot" /> Completed tasks <strong>{completedTasks}</strong></div>
                    <div><span className="legend-dot gray-dot" /> Remaining tasks <strong>{remainingTasks}</strong></div>
                  </div>
                  <div className="overview-footnote">
                    <span className="status-dot" /> Task data from your backend
                  </div>
                </div>
              </section>

              <section className="bottom-grid">
                <div className="panel tasks-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Recent tasks</h2>
                      <p>Mark an unfinished task complete to save the change.</p>
                    </div>
                    <button className="text-button" onClick={() => setActivePage("Tasks")}>
                      View all <span>→</span>
                    </button>
                  </div>
                  <div className="task-list">
                    {allTasks.length === 0 && <p>No tasks found for your goals yet.</p>}
                    {allTasks.map((task) => {
                      const parentGoal = goals.find((goal) => goal.id === task.goal_id);
                      return (
                        <label className={`task-row ${task.completed ? "task-done" : ""}`} key={task.id}>
                          <input
                            type="checkbox"
                            checked={task.completed}
                            disabled={task.completed || completingTaskId !== null}
                            onChange={() => toggleTask(task.id)}
                          />
                          <span className="custom-checkbox">{task.completed ? "✓" : ""}</span>
                          <span className="task-copy">
                            <strong>{task.title}</strong>
                            <small>{parentGoal?.title ?? "Goal"}</small>
                          </span>
                          <span className={`task-status ${task.completed ? "complete" : "pending"}`}>
                            {task.completed ? "Completed" : "Pending"}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                <div className="panel insight-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Journal insights</h2>
                      <p>From intention to action.</p>
                    </div>
                    <span className="insight-spark">✳</span>
                  </div>
                  <div className="insight-empty-icon">✧</div>
                  <h3>Your intentions matter.</h3>
                  <p className="insight-description">
                    Journal insights will appear here when we connect the journal extraction API.
                  </p>
                  <button className="secondary-button full-button" onClick={() => setActivePage("Journal")}>
                    Open journal <span>→</span>
                  </button>
                </div>
              </section>
            </>
          )}

          <footer className="dashboard-footer">
            <span>AI Digital Twin <span className="footer-separator">·</span> Review 2 preview</span>
            <span>Purpose <b>→</b> Action <b>→</b> Progress</span>
          </footer>
        </div>
      </section>
    </main>
  );
}

function StatCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: string;
}) {
  return (
    <article className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <strong className="stat-value">{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
