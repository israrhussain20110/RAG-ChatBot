import React from 'react';
import ChatWindow from '../components/ChatWindow';

export default function Home() {
  // In a real app, the user ID would come from an authentication context
  const userId = "test-user"; 

  return (
    <div>
      <header className="bg-slate-800 text-white p-4 text-center text-xl">
        <h1>RAG Bot</h1>
      </header>
      <main>
        <ChatWindow userId={userId} />
      </main>
    </div>
  );
}