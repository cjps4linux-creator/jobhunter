import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 p-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        JobHunter
      </h1>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Google Jobs-style job dashboard
      </p>
      <Link
        href="/jobs"
        className="rounded-xl bg-indigo-600 px-6 py-3 text-white font-semibold shadow hover:bg-indigo-500 transition"
      >
        Browse jobs →
      </Link>
    </div>
  );
}
