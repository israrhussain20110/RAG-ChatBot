import React from 'react';
import CodeBlock from './CodeBlock';

export default function ChatMessage({ message }) {
  const { from, text, timestamp } = message;
  const isUser = from === 'user';

  const renderText = (text) => {
    const codeBlockRegex = /```([\s\S]*?)```/g;
    const parts = text.split(codeBlockRegex);

    return parts.map((part, index) => {
      if (index % 2 === 1) {
        return <CodeBlock key={index} code={part} />;
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-slate-300 rounded-full flex items-center justify-center text-sm font-semibold text-gray-700">Bot</div>
      )}
      <div className={`flex flex-col p-3 rounded-lg max-w-lg shadow-md ${isUser ? 'bg-blue-500 text-white items-end' : 'bg-slate-200 items-start'}`}>
        <div className="text-base">{renderText(text)}</div>
        <div className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-500'}`}>{timestamp}</div>
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-sm font-semibold text-white">You</div>
      )}
    </div>
  );
}