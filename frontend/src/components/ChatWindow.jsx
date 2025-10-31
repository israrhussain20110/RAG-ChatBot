import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import TypingIndicator from './TypingIndicator';
import UploadPanel from './UploadPanel';

export default function ChatWindow({ userId }) {
  const [messages, setMessages] = useState([{ from: "bot", text: "Hello! I'm a RAG bot. You can ask me questions about the documents you upload.", timestamp: new Date().toLocaleTimeString() }]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [ragPrompt, setRagPrompt] = useState("");
  const [promptSaved, setPromptSaved] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSavePrompt = () => {
    setPromptSaved(true);
    setTimeout(() => {
      setPromptSaved(false);
    }, 2000); // Hide message after 2 seconds
  };

  useEffect(() => {
    const fetchPrompt = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/chat/rag/prompt');
        const data = await response.json();
        setRagPrompt(data.prompt);
      } catch (error) {
        console.error("Failed to fetch RAG prompt:", error);
        // Set a fallback prompt in case of an error
        setRagPrompt("You are a helpful assistant. Use the following context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\nContext:\n{context}\n\nQuestion:\n{question}");
      }
    };

    fetchPrompt();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const newChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  const send = async (messageText = input) => {
    if (!messageText.trim()) return;

    const userMessage = { from: "user", text: messageText, timestamp: new Date().toLocaleTimeString() };
    setMessages((m) => [...m, userMessage]);
    setInput("");
    setIsLoading(true);

    const botMessageId = Date.now();

    const baseUrl = 'http://localhost:8000';
    const endpoint = `${baseUrl}/api/v1/chat/rag/stream`;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
        },
        body: JSON.stringify({ message: messageText, conversation_id: conversationId, rag_prompt: ragPrompt }),
      });

      if (!response.body) throw new Error("Response body is null");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let firstChunk = true;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        
        const lines = chunk.split('\n\n');
        for (const line of lines) {
          if (!line || !line.trim()) continue;

          // handle event lines that may include a data: part in the same chunk
          if (line.includes('event: conversation_id')) {
            const dataIndex = line.indexOf('data: ');
            if (dataIndex !== -1) {
              const id = cleanDataLine(line.slice(dataIndex));
              if (id) setConversationId(id);
            }
            continue;
          }

          if (line.includes('data:')) {
            const raw = cleanDataLine(line);
            if (!raw) continue;

            if (firstChunk) {
              setMessages((m) => [...m, { id: botMessageId, from: "bot", text: raw, timestamp: new Date().toLocaleTimeString() }]);
              firstChunk = false;
            } else {
              setMessages(prev => prev.map(msg => 
                msg.id === botMessageId ? { ...msg, text: msg.text + raw } : msg
              ));
            }
          }
        }
      }
    } catch (error) {
      console.error("Streaming failed:", error);
      let errorMessage = "Error: Could not connect to the server.";
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        errorMessage = "Error: Could not connect to the server. Please check if the backend is running.";
      }
      setMessages(prev => [...prev, { id: botMessageId, from: 'bot', text: errorMessage, timestamp: new Date().toLocaleTimeString()}]);
    } finally {
      setIsLoading(false);
    }
  };

  // helper to clean a line and extract just the text content
  function cleanDataLine(line) {
    // Remove all "data:" prefixes and trim
    return line.replace(/data:\s*/gi, '').trim();
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="border rounded p-3 h-[calc(100vh-200px)] overflow-y-auto bg-white flex flex-col space-y-2">
            {messages.map((msg, i) => <ChatMessage key={i} message={msg} />)}
            <div ref={messagesEndRef} />
            {isLoading && <TypingIndicator />}
          </div>

          <div className="flex justify-center items-center my-2">
            <button onClick={newChat} className="ml-4 px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600">New Chat</button>
          </div>

          <div className="flex gap-2">
            <input 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
              className="flex-1 p-2 border rounded-lg" 
              placeholder="Type your message..."
            />
            <button onClick={() => send()} className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800">Send</button>
            <button
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
              onClick={() => setShowUpload(!showUpload)}
            >
              {showUpload ? 'Hide Upload' : 'Upload'}
            </button>
          </div>
          {showUpload && (
            <div className="mt-2 overflow-y-auto">
              <UploadPanel />
            </div>
          )}
        </div>

        <div className="w-1/3 flex flex-col gap-4">
          <div className="p-4 border rounded-lg bg-gray-100 flex-grow overflow-y-auto flex flex-col">
            <h2 className="text-lg font-bold mb-2">RAG Prompt Options</h2>
            <textarea
              className="w-full p-2 border rounded-lg resize-y flex-grow"
              rows="15"
              value={ragPrompt}
              onChange={(e) => setRagPrompt(e.target.value)}
            />
            <button onClick={handleSavePrompt} className="px-4 py-2 mt-auto bg-slate-700 text-white rounded-lg hover:bg-slate-800">Submit</button>
            {promptSaved && <p className="text-green-500 mt-2">Prompt saved!</p>}
          </div>

          <div className="p-4 border rounded-lg bg-gray-100 flex-grow overflow-y-auto flex flex-col">
            <h2 className="text-lg font-bold mb-2">Create Agent Options</h2>
            <p className="flex-grow">This is a placeholder for creating a new agent. Click the button to submit.</p>
            <button onClick={() => {}} className="px-4 py-2 mt-auto bg-slate-700 text-white rounded-lg hover:bg-slate-800">Submit</button>
          </div>
        </div>
      </div>
    </div>
  );
}
