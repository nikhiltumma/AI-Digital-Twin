
"use client";

import { useState } from "react";

const goals = [
  { title: "Master DSA", category: "Learning", completed: 8, total: 12 },
  { title: "Build AI Digital Twin", category: "Project", completed: 5, total: 10 },
  { title: "Improve consistency", category: "Personal", completed: 3, total: 8 },
];

const initialTasks = [
  { id: 1, title: "Practice binary search problems", goal: "Master DSA", done: true },
  { id: 2, title: "Implement journal extraction API", goal: "Build AI Digital Twin", done: true },
  { id: 3, title: "Review today's learning progress", goal: "Improve consistency", done: false },
  { id: 4, title: "Solve three array problems", goal: "Master DSA", done: false },
];

const navigation = [
  { name: "Dashboard", icon: "▦" },
  { name: "Journal", icon: "▤" },
  { name: "Goals", icon: "◎" },
  { name: "Tasks", icon: "✓" },
  { name: "Progress", icon: "↗" },
];

export default function Dashboard() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [tasks, setTasks] = useState(initialTasks);

  const completedTasks = tasks.filter((task) => task.done).length;
  const overallProgress = Math.round(
    (goals.reduce((sum, goal) => sum + goal.completed / goal.total, 0) /
      goals.length) *
      100
  );

  function toggleTask(id: number) {
    setTasks((current) =>
      current.map((task) =>
        task.id === id ? { ...task, done: !task.done } : task
      )
    );
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
                <span className="nav-count">{tasks.filter((t) => !t.done).length}</span>
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

          <div className="demo-notice">
            <span>ⓘ</span>
            Preview mode — sample data only. Live backend connection comes next.
          </div>

          <section className="stats-grid">
            <StatCard label="Active goals" value={String(goals.length)} detail="Goals you're working on" icon="◎" />
            <StatCard label="Total tasks" value={String(tasks.length)} detail={`${completedTasks} completed so far`} icon="☷" />
            <StatCard label="Overall progress" value={`${overallProgress}%`} detail="Average across sample goals" icon="↗" />
            <StatCard label="Tasks remaining" value={String(tasks.length - completedTasks)} detail="Small steps still to take" icon="◷" />
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
                {goals.map((goal, index) => {
                  const percent = Math.round((goal.completed / goal.total) * 100);
                  return (
                    <article className="goal-item" key={goal.title}>
                      <div className={`goal-symbol goal-symbol-${index}`}>
                        {["◈", "⌘", "✳"][index]}
                      </div>
                      <div className="goal-body">
                        <div className="goal-title-row">
                          <div>
                            <h3>{goal.title}</h3>
                            <span className="category-label">{goal.category}</span>
                          </div>
                          <strong className="goal-percent">{percent}%</strong>
                        </div>
                        <div className="progress-track">
                          <div
                            className={`progress-fill progress-fill-${index}`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                        <p className="goal-meta">
                          {goal.completed} of {goal.total} tasks completed
                        </p>
                      </div>
                    </article>
                  );
                })}
              </div>
              <button className="secondary-button full-button" onClick={() => setActivePage("Goals")}>
                Explore your goals <span>→</span>
              </button>
            </div>

            <div className="panel overview-panel">
              <div className="panel-heading">
                <div>
                  <h2>Progress overview</h2>
                  <p>A snapshot of your sample goals.</p>
                </div>
                <span className="period-chip">All goals</span>
              </div>

              <div className="donut-wrap">
                <div
                  className="donut-chart"
                  style={{ background: `conic-gradient(#8b7cff ${overallProgress * 3.6}deg, #293044 0deg)` }}
                >
                  <div className="donut-inner">
                    <strong>{overallProgress}%</strong>
                    <span>AVERAGE</span>
                  </div>
                </div>
              </div>

              <div className="overview-legend">
                <div><span className="legend-dot purple-dot" /> Completed tasks <strong>{completedTasks}</strong></div>
                <div><span className="legend-dot gray-dot" /> Remaining tasks <strong>{tasks.length - completedTasks}</strong></div>
              </div>
              <div className="overview-footnote">
                <span className="status-dot" />
                You can update tasks below
              </div>
            </div>
          </section>

          <section className="bottom-grid">
            <div className="panel tasks-panel">
              <div className="panel-heading">
                <div>
                  <h2>Recent tasks</h2>
                  <p>Track the small steps that move you forward.</p>
                </div>
                <button className="text-button" onClick={() => setActivePage("Tasks")}>
                  View all <span>→</span>
                </button>
              </div>

              <div className="task-list">
                {tasks.map((task) => (
                  <label className={`task-row ${task.done ? "task-done" : ""}`} key={task.id}>
                    <input
                      type="checkbox"
                      checked={task.done}
                      onChange={() => toggleTask(task.id)}
                    />
                    <span className="custom-checkbox">{task.done ? "✓" : ""}</span>
                    <span className="task-copy">
                      <strong>{task.title}</strong>
                      <small>{task.goal}</small>
                    </span>
                    <span className={`task-status ${task.done ? "complete" : "pending"}`}>
                      {task.done ? "Completed" : "Pending"}
                    </span>
                  </label>
                ))}
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
                Journal insights will appear here when your entries are processed by the AI extraction service.
              </p>
              <button className="secondary-button full-button" onClick={() => setActivePage("Journal")}>
                Open journal <span>→</span>
              </button>
            </div>
          </section>

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
