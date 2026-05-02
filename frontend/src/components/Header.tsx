export default function Header({ onClear }: { onClear: () => void }) {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white/80 px-6 py-3 backdrop-blur dark:border-gray-700 dark:bg-gray-900/80">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
        AI News Aggregator
      </h1>
      <button
        onClick={onClear}
        className="rounded-md px-3 py-1.5 text-sm text-gray-500 transition hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
      >
        Clear chat
      </button>
    </header>
  );
}
