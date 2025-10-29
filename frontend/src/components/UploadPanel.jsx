import React, { useState } from 'react';

export default function UploadPanel() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadStatus('');
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploadStatus('Uploading...');

    try {
      const response = await fetch('/api/v1/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setUploadStatus(`File uploaded successfully! Doc ID: ${data.doc_id}`);
      setFile(null);
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    }
  };

  return (
    <div className="mt-4 p-4 border rounded-lg bg-white">
      <h3 className="text-lg font-semibold">Ingest Knowledge</h3>
      <p className="text-sm text-gray-600 mb-2">Upload a PDF, DOCX, or TXT file to add it to the knowledge base.</p>
      <div className="flex items-center gap-2">
        <input 
          type="file" 
          onChange={handleFileChange} 
          className="block w-full text-sm text-slate-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-violet-50 file:text-violet-700
            hover:file:bg-violet-100"
        />
        <button 
          onClick={handleUpload} 
          className="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors disabled:bg-gray-400"
          disabled={!file}
        >
          Upload
        </button>
      </div>
      {uploadStatus && <p className="mt-2 text-sm text-gray-700">{uploadStatus}</p>}
    </div>
  );
}