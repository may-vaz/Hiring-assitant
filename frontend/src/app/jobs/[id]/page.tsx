"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getJob, triggerCalls, getCalls, Job, CallRecord } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: "bg-green-100 text-green-800",
  NOT_STARTED: "bg-gray-100 text-gray-800",
  SCHEDULED: "bg-blue-100 text-blue-800",
  IN_PROGRESS: "bg-yellow-100 text-yellow-800",
  FAILED: "bg-red-100 text-red-800",
  NOT_CONNECTED: "bg-red-100 text-red-800",
};

export default function JobDetailPage() {
  const params = useParams();
  const jobId = Number(params.id);

  const [job, setJob] = useState<Job | null>(null);
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [calling, setCalling] = useState(false);
  const [error, setError] = useState("");

  const loadJob = useCallback(async () => {
    try {
      const data = await getJob(jobId);
      setJob(data);
    } catch {
      setError("Could not load this job. It may not exist.");
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const loadCalls = useCallback(async () => {
    try {
      const data = await getCalls(jobId);
      setCalls(data);
    } catch {
      // silent
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();
    loadCalls();
  }, [loadJob, loadCalls]);

  useEffect(() => {
    const interval = setInterval(loadCalls, 5000);
    return () => clearInterval(interval);
  }, [loadCalls]);

  function toggleCandidate(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleExpanded(candidateId: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(candidateId)) next.delete(candidateId);
      else next.add(candidateId);
      return next;
    });
  }

  async function handleCallSelected() {
    if (selected.size === 0) {
      setError("Select at least one candidate to call.");
      return;
    }
    setError("");
    setCalling(true);
    try {
      await triggerCalls(jobId, Array.from(selected));
      setSelected(new Set());
      await loadCalls();
    } catch {
      setError("Failed to trigger calls. Please try again.");
    } finally {
      setCalling(false);
    }
  }

  if (loading) {
    return <main className="max-w-4xl mx-auto py-16 px-4">Loading...</main>;
  }

  if (error && !job) {
    return (
      <main className="max-w-4xl mx-auto py-16 px-4">
        <p className="text-red-500">{error}</p>
      </main>
    );
  }

  if (!job) return null;

  const callByCandidateId = new Map(calls.map((c) => [c.candidate_id, c]));

  return (
    <main className="max-w-4xl mx-auto py-16 px-4">
      <h1 className="text-2xl font-bold mb-1">{job.title}</h1>
      <p className="text-muted-foreground mb-8 line-clamp-2">{job.description}</p>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Candidates ({job.candidates.length})</CardTitle>
          <Button
            onClick={handleCallSelected}
            disabled={calling || selected.size === 0}
            size="sm"
          >
            {calling ? "Starting calls..." : `Call Selected (${selected.size})`}
          </Button>
        </CardHeader>
        <CardContent>
          {error && <p className="text-sm text-red-500 mb-4">{error}</p>}

          <div className="space-y-2">
            {job.candidates.map((c) => {
              const call = callByCandidateId.get(c.id);
              const isExpanded = expanded.has(c.id);

              return (
                <div key={c.id} className="border rounded-lg">
                  <div className="flex items-center gap-3 p-3">
                    {!call && (
                      <Checkbox
                        checked={selected.has(c.id)}
                        onCheckedChange={() => toggleCandidate(c.id)}
                      />
                    )}
                    <div className="flex-1">
                      <p className="font-medium">{c.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {c.title} {c.company && `· ${c.company}`}
                      </p>
                    </div>

                    {call ? (
                      <>
                        <Badge className={STATUS_COLORS[call.status] || "bg-gray-100 text-gray-800"}>
                          {call.status}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleExpanded(c.id)}
                        >
                          {isExpanded ? "Hide" : "View"}
                        </Button>
                      </>
                    ) : (
                      <Badge variant="outline">Not called</Badge>
                    )}
                  </div>

                  {call && isExpanded && (
                    <div className="border-t p-4 bg-muted/30">
                      <p className="text-sm text-muted-foreground mb-2">
                        Lifecycle: {call.lifecycle_status}
                        {call.duration_minutes !== null &&
                          ` · Duration: ${call.duration_minutes.toFixed(1)} min`}
                      </p>

                      {call.recording_url && (
                        <audio controls className="w-full mb-3">
                          <source src={call.recording_url} />
                        </audio>
                      )}

                      {Object.keys(call.result).length > 0 ? (
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          {Object.entries(call.result).map(([key, value]) => (
                            <div key={key} className="border rounded p-2 bg-background">
                              <div className="text-xs text-muted-foreground uppercase">
                                {key.replace(/_/g, " ")}
                              </div>
                              <div>{String(value)}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground italic">
                          Waiting for call result...
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
