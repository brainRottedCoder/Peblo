import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ErrorBanner, Loading } from "../components/States";
import type { Issue, PublishRun, ValidationReport } from "../types";

const CODE_LABELS: Record<string, string> = {
  show_published_no_section: "Published show has no section",
  show_unknown_section: "Unknown section",
  episode_published_no_duration: "Published episode has no duration",
  episode_published_no_artwork: "Published episode has no pictures",
  duplicate_content_group_language: "Two episodes share a language in one content group",
  show_missing_poster: "Show missing poster",
  show_missing_banner: "Show missing banner",
  episode_incomplete_artwork: "Episode missing a picture size",
  title_whitespace: "Title has extra spaces",
  title_lowercase: "Title starts lowercase",
};

function IssueGroup({ title, issues }: { title?: string; issues: Issue[] }) {
  if (issues.length === 0) return null;
  const grouped = new Map<string, Issue[]>();
  for (const issue of issues) {
    const list = grouped.get(issue.code) ?? [];
    list.push(issue);
    grouped.set(issue.code, list);
  }
  return (
    <>
      {title ? (
        <h2>
          {title} ({issues.length})
        </h2>
      ) : null}
      {[...grouped.entries()].map(([code, rows]) => (
        <section className="issue-group" key={code}>
          <h3>
            {CODE_LABELS[code] ?? code} <span className="mono">{rows.length}</span>
          </h3>
          <div className="issue-list">
            {rows.map((issue, i) => (
              <article className="issue" key={`${issue.code}-${issue.episode_id ?? issue.show_id}-${i}`}>
                <h3>{issue.message}</h3>
                <p>{issue.how_to_fix}</p>
                {issue.show_id ? <Link to={`/shows/${issue.show_id}`}>{issue.show_title ?? "Open show"}</Link> : null}
              </article>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}

export function PublishPage() {
  const { role } = useAuth();
  const qc = useQueryClient();

  const reportQ = useQuery({
    queryKey: ["validation"],
    queryFn: () => api<ValidationReport>("/admin/validation-report"),
  });
  const runsQ = useQuery({
    queryKey: ["runs"],
    queryFn: () => api<PublishRun[]>("/admin/catalog/publish-runs"),
  });
  const publish = useMutation({
    mutationFn: () => api<PublishRun>("/admin/catalog/publish", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs"] });
      qc.invalidateQueries({ queryKey: ["validation"] });
    },
  });

  const report = reportQ.data;
  const blocked = !report?.can_publish;
  const notAdmin = role !== "admin";
  const reasons: string[] = [];
  if (notAdmin) reasons.push("Only an admin can publish. You are signed in as an editor.");
  if (blocked) reasons.push("There are still problems to fix in the list below.");

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="kicker">Go-live</p>
          <h1>Publish catalogue</h1>
          <p className="lede">
            Writes a new catalogue.json for the kids’ app. Drafts stay out. Language variants of one episode collapse
            into a single card.
          </p>
        </div>
      </header>
      {publish.isError && <ErrorBanner error={publish.error} />}
      {publish.isSuccess && (
        <div className="banner ok">
          {publish.data.notes && typeof publish.data.notes === "object" && "idempotent" in (publish.data.notes as object)
            ? "Already up to date — same catalogue as the last successful run."
            : `Published. ${publish.data.show_count} shows, ${publish.data.episode_count} grouped episodes.`}{" "}
          Outcome: {publish.data.outcome}.
        </div>
      )}

      <div className="publish-hero">
        <div className="stat">
          <span>Blocking</span>
          <strong>{report ? report.blocking.length : "—"}</strong>
        </div>
        <div className="stat">
          <span>Warnings</span>
          <strong>{report ? report.warnings.length : "—"}</strong>
        </div>
        <div className="stat">
          <span>Last run</span>
          <strong>{runsQ.data?.[0] ? new Date(runsQ.data[0].started_at).toLocaleDateString() : "None"}</strong>
        </div>
        <div className="publish-actions">
          <button type="button" disabled={blocked || notAdmin || publish.isPending} onClick={() => publish.mutate()}>
            {publish.isPending ? "Publishing…" : "Publish now"}
          </button>
          {reasons.length > 0 && (
            <ul>
              {reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {reportQ.isLoading && <Loading label="Checking what would block publish…" />}
      {reportQ.isError && <ErrorBanner error={reportQ.error} />}
      {report && report.blocking.length === 0 && (
        <div className="banner ok">Nothing blocking. An admin can publish.</div>
      )}
      {report && <IssueGroup title="Must fix before publish" issues={report.blocking} />}
      {report && (
        <>
          <h2>Worth a look ({report.warnings.length})</h2>
          <p className="hint">These do not block publish, but an editor will want them tidy.</p>
          <IssueGroup issues={report.warnings} />
        </>
      )}

      <h2>Run history</h2>
      {runsQ.isLoading && <Loading label="Loading past runs…" />}
      {runsQ.data && runsQ.data.length === 0 && <p className="hint">No publishes yet.</p>}
      {runsQ.data && runsQ.data.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>When</th>
              <th>Who</th>
              <th>Outcome</th>
              <th>Counts</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {runsQ.data.map((run) => (
              <tr key={run.id}>
                <td>{new Date(run.started_at).toLocaleString()}</td>
                <td>{run.actor_email}</td>
                <td>
                  <span className={`badge ${run.outcome === "success" ? "published" : "draft"}`}>{run.outcome}</span>
                </td>
                <td>
                  {run.show_count} shows / {run.episode_count} episodes
                </td>
                <td className="mono">{run.error ?? run.catalogue_key ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
