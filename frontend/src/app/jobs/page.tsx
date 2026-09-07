"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getJobs, deleteJob, Job } from "@/lib/api";

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function JobsListPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    getJobs()
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(jobId: number) {
    const confirmed = window.confirm(
      "Delete this search and all its candidates and call results? This cannot be undone."
    );
    if (!confirmed) return;

    setDeletingId(jobId);
    try {
      await deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
    } catch {
      alert("Failed to delete. Please try again.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <main className="max-w-3xl mx-auto py-16 px-4">
      <h1 className="text-2xl font-bold mb-8">Dashboard</h1>

      {loading && <p className="text-muted-foreground">Loading...</p>}

      {!loading && jobs.length === 0 && (
        <p className="text-muted-foreground">
          No searches yet.{" "}
          <Link href="/" className="underline">
            Start one from the homepage.
          </Link>
        </p>
      )}

      <div className="space-y-3">
        {jobs.map((job) => (
          <Card key={job.id}>
            <CardContent className="py-4">
              <div className="flex items-start justify-between gap-4">
                <Link href={`/jobs/${job.id}`} className="flex-1 min-w-0">
                  <p className="font-medium">{job.title}</p>
                  <p className="text-sm text-muted-foreground truncate">
                    {job.description}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatDate(job.created_at)} · {job.candidates.length} candidate
                    {job.candidates.length !== 1 ? "s" : ""}
                  </p>
                </Link>
                <div className="flex gap-2 shrink-0">
                  <Link href={`/jobs/${job.id}`}>
                    <Button variant="outline" size="sm">View</Button>
                  </Link>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => handleDelete(job.id)}
                    disabled={deletingId === job.id}
                  >
                    {deletingId === job.id ? "..." : "Delete"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}
