"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  posted_at: string;
  source: string;
  job_type: string;
  tags: string[];
}

function timeAgo(iso: string) {
  const now = new Date();
  const then = new Date(iso);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function companyInitial(name: string) {
  return name
    .split(/[^a-zA-Z0-9]+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bookmarks, setBookmarks] = useState<Set<string>>(new Set());
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) root.classList.add("dark");
    else root.classList.remove("dark");
  }, [darkMode]);

  const fetchJobs = async () => {
    try {
      setError(null);
      const res = await fetch("/api/jobs/today", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as Job[];
      setJobs(data);
      setLastRefresh(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 3 * 60 * 60 * 1000); // 3 hours
    return () => clearInterval(interval);
  }, []);

  const toggleBookmark = (id: string) => {
    setBookmarks((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
        <div className="mx-auto max-w-2xl px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
            Jobs
          </h1>
          <div className="flex items-center gap-3">
            {lastRefresh && (
              <span className="hidden text-sm text-gray-500 dark:text-gray-400 sm:inline">
                Updated {timeAgo(lastRefresh.toISOString())}
              </span>
            )}
            <button
              onClick={fetchJobs}
              className="rounded-full bg-gray-100 dark:bg-gray-700 px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition"
            >
              Refresh
            </button>
            <button
              onClick={() => setDarkMode((v) => !v)}
              className="rounded-full bg-gray-100 dark:bg-gray-700 p-1.5 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-4 w-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-4 w-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-4">
        {loading && (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-2xl bg-gray-200 dark:bg-gray-800"
              />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            <p className="font-medium">Oops — couldn’t load jobs.</p>
            <p className="text-sm opacity-80">{error}</p>
            <button
              onClick={fetchJobs}
              className="mt-2 text-sm font-semibold underline"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && jobs.length === 0 && (
          <div className="py-20 text-center text-gray-500 dark:text-gray-400">
            <p className="text-lg font-medium">No jobs found</p>
            <p className="mt-1 text-sm">Check back later or adjust your filters.</p>
          </div>
        )}

        <ul className="space-y-3">
          {jobs.map((job) => (
            <li
              key={job.id}
              className="group rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
            >
              <div className="flex items-start gap-3">
                {/* Company avatar placeholder */}
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold">
                  {companyInitial(job.company)}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h2 className="truncate text-base font-bold text-gray-900 dark:text-white">
                      {job.title}
                    </h2>
                    <div className="flex shrink-0 items-center gap-2">
                      <button
                        onClick={() => toggleBookmark(job.id)}
                        className={`rounded-full p-1.5 transition ${
                          bookmarks.has(job.id)
                            ? "text-yellow-500"
                            : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        }`}
                        aria-label={bookmarks.has(job.id) ? "Unbookmark" : "Bookmark"}
                      >
                        {bookmarks.has(job.id) ? (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="currentColor"
                            className="h-5 w-5"
                          >
                            <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                          </svg>
                        ) : (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={1.5}
                            stroke="currentColor"
                            className="h-5 w-5"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
                            />
                          </svg>
                        )}
                      </button>
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-full p-1.5 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                        aria-label="Apply"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={1.5}
                          stroke="currentColor"
                          className="h-5 w-5"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
                          />
                        </svg>
                      </a>
                    </div>
                  </div>

                  <p className="mt-0.5 truncate text-sm text-gray-600 dark:text-gray-300">
                    {job.company} · {job.location}
                  </p>

                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                      {job.source}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {timeAgo(job.posted_at)}
                    </span>
                    <span className="rounded-full border border-gray-200 px-2.5 py-0.5 text-xs text-gray-600 dark:border-gray-600 dark:text-gray-400">
                      {job.job_type}
                    </span>
                    {job.tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
