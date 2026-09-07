"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createJob } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (!title.trim() || !description.trim()) {
      setError("Please fill in both the job title and description.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const job = await createJob(title, description);
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError("Something went wrong while creating the job. Please try again.");
      setLoading(false);
    }
  }

  return (
    <main className="max-w-2xl mx-auto py-16 px-4">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold mb-3">Welcome to AI Hiring Assistant</h1>
        <p className="text-muted-foreground">
          Paste a job description, get matched candidates, and reach out
          instantly with AI-powered voice screening calls.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Find Candidates</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Job Title</label>
            <Input
              placeholder="e.g. Backend Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-1 block">Job Description</label>
            <Textarea
              placeholder="Paste the full job description here..."
              rows={10}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button onClick={handleSubmit} disabled={loading} className="w-full">
            {loading ? "Finding candidates..." : "Find Candidates"}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
