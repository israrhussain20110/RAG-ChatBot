import React, { useState, useRef, useEffect } from "react";
import UploadPanel from "./UploadPanel";

export default function ChatWindow({ userId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [chatMode, setChatMode] = useState('agent');
  const [conversationId, setConversationId] = useState(null);
  const [handoffStatus, setHandoffStatus] = useState('inactive'); // inactive or pending
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }) };
  useEffect(() => { scrollToBottom() }, [messages]);

  const newChat = () => {
    setMessages([]);
    setConversationId(null);
    setHandoffStatus('inactive');
  };

  const requestHuman = () => {
    if (handoffStatus === 'pending') return;
    setInput("I need to speak to a human.");
  };

  const send = async (messageText = input) => {
    if (!messageText.trim()) return;

    const userMessage = { from: "user", text: messageText };
    setMessages((m) => [...m, userMessage]);
    setInput("");

    const botMessageId = Date.now();
    setMessages((m) => [...m, { id: botMessageId, from: "bot", text: "" }]);

    const endpoint = chatMode === 'agent' ? '/api/v1/chat/agent/stream' : '/api/v1/chat/rag/stream';

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: messageText, conversation_id: conversationId }),
      });

      if (!response.body) throw new Error("Response body is null");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        
        const lines = chunk.split('\n\n');
        for (const line of lines) {
          if (line.startsWith('event: conversation_id')) {
            setConversationId(line.split('data: ')[1]);
          } else if (line.startsWith('event: handoff_status')) {
            setHandoffStatus(line.split('data: ')[1]);
          } else if (line.startsWith('data: ')) {
            const data = line.substring(6);
            setMessages(prev => prev.map(msg => 
              msg.id === botMessageId ? { ...msg, text: msg.text + data } : msg
            ));
          }
        }
      }
    } catch (error) {
      console.error("Streaming failed:", error);
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId ? { ...msg, text: "Error: Could not connect." } : msg
      ));
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <div className="border rounded p-3 h-96 overflow-y-auto bg-white flex flex-col space-y-2">
        {messages.map((m, i) => (
          <div key={m.id || i} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`inline-block p-2 rounded-lg ${m.from === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-black"}`}>
              {m.text}
            </div>
          </div>
        ))}
        {handoffStatus === 'pending' && (
          <div className="text-center p-2 text-sm text-yellow-800 bg-yellow-100 rounded-lg">A human agent will be with you shortly.</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex justify-center items-center my-2">
        <div className="p-1 rounded-lg bg-gray-200 flex items-center text-sm">
          <button onClick={() => setChatMode('rag')} className={`px-3 py-1 rounded-md ${chatMode === 'rag' ? 'bg-white shadow' : ''}`}>RAG</button>
          <button onClick={() => setChatMode('agent')} className={`px-3 py-1 rounded-md ${chatMode === 'agent' ? 'bg-white shadow' : ''}`}>Agent</button>
        </div>
        <button onClick={newChat} className="ml-4 px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600">New Chat</button>
        <button onClick={requestHuman} disabled={chatMode !== 'agent' || handoffStatus === 'pending'} className="ml-2 px-3 py-1.5 text-sm bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:bg-gray-400">Request Human</button>
      </div>

      <div className="flex gap-2">
        <input value={input} onChange={e=>setInput(e.target.value)} disabled={handoffStatus === 'pending'} className="flex-1 p-2 border rounded-lg disabled:bg-gray-100" onKeyPress={(e) => e.key === 'Enter' && send()} />
        <button onClick={() => send()} disabled={handoffStatus === 'pending'} className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 disabled:bg-gray-400">Send</button>
      </div>
      <UploadPanel />
    </div>
  );
}