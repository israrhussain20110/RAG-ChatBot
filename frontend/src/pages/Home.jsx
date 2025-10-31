import React from 'react';
import ChatWindow from '../components/ChatWindow';

export default function Home() {
  // In a real app, the user ID would come from an authentication context
  const userId = "test-user"; 

  return (
    <div className="flex flex-col h-screen">
      <header className="bg-slate-800 text-white p-4 text-center text-xl flex-shrink-0">
        <h1>RAG Bot</h1>
      </header>
      <main className="flex flex-grow"> {/* Main content area, takes remaining height */}
        <ChatWindow userId={userId} className="flex-grow" />
      </main>
    </div>
  );
}