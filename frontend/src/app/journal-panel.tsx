
"use client";

import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type JournalEntry = {
  id: number;
  content: string;
  created_at: string;
};

type JournalExtraction = {
  purpose: string;
  actions: string[];
  deadline: string | null;
  blockers: string[];
};

type CreatedGoal = {
  id: number;
  title: string;
};

export default function JournalPanel() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [content, setContent] = useState("");
  const [selectedEntry, setSelectedEntry] = useState<number | null>(null);
  const [extraction, setExtraction] = useState<JournalExtraction | null>(
    null
  );

  const [goalTitle, setGoalTitle] = useState("");
  const [createdGoal, setCreatedGoal] = useState<CreatedGoal | null>(null);

  const [loadingEntries, setLoadingEntries] = useState(true);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [creatingGoal, setCreatingGoal] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadEntries() {
    try {
      setLoadingEntries(true);
      setError("");

      const response = await fetch(`${API_BASE_URL}/journal`);

      if (!response.ok) {
        throw new Error(
          `Could not load journal entries (${response.status})`
        );
      }

      const data: JournalEntry[] = await response.json();
      setEntries(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load entries."
      );
    } finally {
      setLoadingEntries(false);
    }
  }

  useEffect(() => {
    void loadEntries();
  }, []);

  async function submitEntry(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!content.trim()) {
      setError("Please write something before saving.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setMessage("");
      setExtraction(null);
      setCreatedGoal(null);

      const response = await fetch(`${API_BASE_URL}/journal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: content.trim() }),
      });

      if (!response.ok) {
        throw new Error(`Could not save entry (${response.status})`);
      }

      const entry: JournalEntry = await response.json();

      setEntries((current) => [
        entry,
        ...current.filter((item) => item.id !== entry.id),
      ]);

      setContent("");
      setSelectedEntry(entry.id);

      await extractEntry(entry.id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not save entry."
      );
    } finally {
      setSaving(false);
    }
  }

  async function extractEntry(entryId: number) {
    try {
      setExtracting(true);
      setError("");
      setMessage("Extracting purpose, actions, deadline, and blockers...");
      setSelectedEntry(entryId);
      setExtraction(null);
      setGoalTitle("");
      setCreatedGoal(null);

      const response = await fetch(
        `${API_BASE_URL}/journal/${entryId}/extract`,
        { method: "POST" }
      );

      if (!response.ok) {
        const detail = await response.text();

        throw new Error(
          `AI extraction failed (${response.status}): ${detail}`
        );
      }

      const result: JournalExtraction = await response.json();

      setExtraction(result);
      setGoalTitle(result.purpose ?? "");
      setMessage("AI extraction completed successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "AI extraction failed."
      );
      setMessage("");
    } finally {
      setExtracting(false);
    }
  }

  async function createGoalAndTasks() {
    if (!extraction) {
      setError("Analyse a journal entry before creating a goal.");
      return;
    }

    if (!goalTitle.trim()) {
      setError("Please enter a title for your goal.");
      return;
    }

    try {
      setCreatingGoal(true);
      setError("");
      setMessage("Creating your goal...");

      // Step 1: Create the goal.
      const goalResponse = await fetch(`${API_BASE_URL}/goals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: goalTitle.trim(),
          description: extraction.purpose,
        }),
      });

      if (!goalResponse.ok) {
        const detail = await goalResponse.text();

        throw new Error(
          `Could not create goal (${goalResponse.status}): ${detail}`
        );
      }

      const goal: CreatedGoal = await goalResponse.json();

      // Step 2: Create a task for each extracted action.
      const actions = [
        ...new Set(
          extraction.actions
            .map((action) => action.trim())
            .filter(Boolean)
        ),
      ];

      const failedActions: string[] = [];

      for (const action of actions) {
        try {
          const taskResponse = await fetch(
            `${API_BASE_URL}/goals/${goal.id}/tasks`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ title: action }),
            }
          );

          if (!taskResponse.ok) {
            failedActions.push(action);
          }
        } catch {
          failedActions.push(action);
        }
      }

      setCreatedGoal(goal);

      if (failedActions.length > 0) {
        setMessage(
          `Goal "${goal.title}" was created, but ${failedActions.length} task(s) could not be saved. You can retry by checking the backend.`
        );
      } else if (actions.length === 0) {
        setMessage(
          `Goal "${goal.title}" was created. No actions were extracted, so no tasks were added.`
        );
      } else {
        setMessage(
          `Success! Goal "${goal.title}" and ${actions.length} task(s) were created.`
        );
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not create the goal and tasks."
      );
      setMessage("");
    } finally {
      setCreatingGoal(false);
    }
  }

  return (
    <div className="journal-workspace">
      <section className="panel journal-editor">
        <div className="panel-heading">
          <div>
            <h2>Today's journal</h2>
            <p>
              Write naturally. Your local AI will identify your
              intentions and next steps.
            </p>
          </div>
          <span className="insight-spark">✳</span>
        </div>

        <form onSubmit={submitEntry}>
          <label className="journal-label" htmlFor="journal-content">
            What's on your mind?
          </label>

          <textarea
            id="journal-content"
            className="journal-textarea"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="Example: I want to improve my DSA skills. Today I will practise binary search, but I struggle with choosing the correct search boundaries..."
            rows={7}
            required
          />

          <div className="journal-form-footer">
            <span>
              Only extract information supported by your entry.
            </span>

            <button
              className="primary-button"
              type="submit"
              disabled={saving || extracting || creatingGoal}
            >
              {saving
                ? "Saving..."
                : extracting
                  ? "Extracting..."
                  : "Save & analyse"}
            </button>
          </div>
        </form>

        {message && <p className="journal-message">{message}</p>}

        {error && (
          <p className="journal-error" role="alert">
            {error}
          </p>
        )}
      </section>

      <section className="panel journal-results">
        <div className="panel-heading">
          <div>
            <h2>AI-extracted insights</h2>
            <p>Structured results from your journal entry.</p>
          </div>
        </div>

        {extracting && (
          <p className="journal-empty">
            Your local AI is analysing the entry. This may take a little
            while.
          </p>
        )}

        {!extracting && !extraction && (
          <p className="journal-empty">
            Save a journal entry and run AI analysis to see your purpose,
            actions, deadline, and blockers here.
          </p>
        )}

        {extraction && (
          <>
            <div className="extraction-results">
              <InsightSection title="Purpose identified">
                <p>{extraction.purpose}</p>
              </InsightSection>

              <InsightSection title="Actions identified">
                {extraction.actions.length > 0 ? (
                  <ul>
                    {extraction.actions.map((action, index) => (
                      <li key={`${index}-${action}`}>{action}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No explicit actions identified.</p>
                )}
              </InsightSection>

              <InsightSection title="Deadline">
                <p>{extraction.deadline ?? "No deadline mentioned."}</p>
              </InsightSection>

              <InsightSection title="Blockers">
                {extraction.blockers.length > 0 ? (
                  <ul>
                    {extraction.blockers.map((blocker, index) => (
                      <li key={`${index}-${blocker}`}>{blocker}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No blockers identified.</p>
                )}
              </InsightSection>
            </div>

            {/* Goal creation form */}
            <div className="goal-creation">
              <div className="panel-heading">
                <div>
                  <h2>Turn intention into action</h2>
                  <p>
                    Review your goal title, then save the goal and
                    extracted actions.
                  </p>
                </div>
              </div>

              {createdGoal ? (
                <div className="goal-created">
                  <p>
                    <strong>Goal created:</strong> {createdGoal.title}
                  </p>
                  <p className="journal-empty">
                    Open Dashboard to view the goal and its saved tasks.
                  </p>
                </div>
              ) : (
                <>
                  <label
                    className="journal-label"
                    htmlFor="goal-title"
                  >
                    Goal title
                  </label>

                  <input
                    id="goal-title"
                    className="journal-textarea"
                    value={goalTitle}
                    onChange={(event) =>
                      setGoalTitle(event.target.value)
                    }
                    placeholder="Enter a clear goal title"
                    maxLength={200}
                    disabled={creatingGoal}
                  />

                  <p className="journal-empty">
                    {extraction.actions.length} action(s) detected.
                    Each action will be added as a task.
                  </p>

                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => void createGoalAndTasks()}
                    disabled={
                      creatingGoal ||
                      extracting ||
                      !goalTitle.trim()
                    }
                  >
                    {creatingGoal
                      ? "Creating goal and tasks..."
                      : "Create Goal & Tasks"}
                  </button>
                </>
              )}
            </div>
          </>
        )}
      </section>

      <section className="panel journal-history">
        <div className="panel-heading">
          <div>
            <h2>Journal history</h2>
            <p>Your saved entries from PostgreSQL.</p>
          </div>

          <button
            type="button"
            className="text-button"
            onClick={() => void loadEntries()}
            disabled={loadingEntries}
          >
            Refresh ↻
          </button>
        </div>

        {loadingEntries && (
          <p className="journal-empty">Loading entries...</p>
        )}

        {!loadingEntries && entries.length === 0 && (
          <p className="journal-empty">
            No journal entries yet. Write your first entry above.
          </p>
        )}

        {entries.map((entry) => (
          <article className="journal-entry" key={entry.id}>
            <div className="journal-entry-meta">
              <span>Entry #{entry.id}</span>
              <time>
                {new Date(entry.created_at).toLocaleString()}
              </time>
            </div>

            <p className="journal-entry-content">{entry.content}</p>

            <button
              type="button"
              className="secondary-button"
              disabled={extracting || creatingGoal}
              onClick={() => void extractEntry(entry.id)}
            >
              Analyse entry
            </button>

            {selectedEntry === entry.id && extraction && (
              <p className="journal-inline-status">
                AI analysis loaded above
              </p>
            )}
          </article>
        ))}
      </section>
    </div>
  );
}

function InsightSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <article className="insight-section">
      <h3>{title}</h3>
      {children}
    </article>
  );
}
