import Link from "next/link";

export function Navbar() {
  return (
    <nav className="border-b">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold">
          AI Hiring Assistant
        </Link>
        <Link href="/jobs" className="text-sm text-muted-foreground hover:text-foreground">
          Dashboard
        </Link>
      </div>
    </nav>
  );
}
