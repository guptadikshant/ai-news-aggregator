import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import { useChat } from "./hooks/useChat";

function App() {
  const { messages, loading, error, sendMessage, clearChat } = useChat();

  return (
    <div className="flex h-screen flex-col bg-white dark:bg-gray-900">
      <Header onClear={clearChat} />
      <ChatWindow messages={messages} loading={loading} />
      {error && (
        <div className="mx-auto max-w-3xl px-4 pb-1 text-sm text-red-500">
          {error}
        </div>
      )}
      <ChatInput onSend={sendMessage} disabled={loading} />
    </div>
  );
}

export default App
