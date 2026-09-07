const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Candidate {
  id: number;
  name: string;
  title: string | null;
  company: string | null;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  source: string;
}

export interface Job {
  id: number;
  title: string;
  description: string;
  created_at: string;
  candidates: Candidate[];
}

export interface CallRecord {
  id: number;
  candidate_id: number;
  hunar_call_id: string | null;
  status: string;
  lifecycle_status: string;
  recording_url: string | null;
  result: Record<string, unknown>;
  duration_minutes: number | null;
}

export async function createJob(title: string, description: string): Promise<Job> {
  const res = await fetch(`${API_URL}/api/jobs`, { method: "POST",
    headers: { "Content-Type": "application/json" },body: JSON.stringify({ title, description }), credentials: "include" });
  if (!res.ok) throw new Error("Failed to create job");
  return res.json();
}

export async function getJob(jobId: number): Promise<Job> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch job");
  return res.json();
}

export async function triggerCalls(jobId: number, candidateIds: number[]): Promise<CallRecord[]> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/calls`, { method: "POST",
    headers: { "Content-Type": "application/json" },body: JSON.stringify({ candidate_ids: candidateIds }), credentials: "include" });
  if (!res.ok) throw new Error("Failed to trigger calls");
  return res.json();
}

export async function getCalls(jobId: number): Promise<CallRecord[]> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/calls`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch calls");
  return res.json();
}
export async function getJobs(): Promise<Job[]> {
  const res = await fetch(`${API_URL}/api/jobs`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch jobs");
  return res.json();
}

export async function deleteJob(jobId: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`, { method: "DELETE", credentials: "include" });
  if (!res.ok) throw new Error("Failed to delete job");
}
