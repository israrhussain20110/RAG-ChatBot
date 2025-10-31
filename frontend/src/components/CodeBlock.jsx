import React from 'react';

export default function CodeBlock({ code }) {
  return (
    <pre className="bg-gray-800 text-white p-4 rounded-lg my-4 overflow-x-auto">
      <code>{code}</code>
    </pre>
  );
}