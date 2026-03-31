import React, { useState, useRef, useEffect } from 'react';
import { Send, FileUp } from 'lucide-react';
import { uploadFile } from '../services/api';

const InputBox = ({ onSend, isProcessing, sessionId, setSessionId, onUploadSuccess, onUploadError }) => {
  const [text, setText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (text.trim() && !isProcessing && !isUploading) {
      onSend(text.trim());
      setText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const result = await uploadFile(file, sessionId);
      setSessionId(result.session_id);
      onUploadSuccess(result.file_info);
    } catch (err) {
      onUploadError(err.response?.data?.detail || err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2">
      <div className="relative flex items-end bg-white dark:bg-gray-800 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 p-2 overflow-hidden transition-all focus-within:ring-2 focus-within:ring-blue-500/50">
        
        {/* File Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing || isUploading}
          className="p-3 text-gray-500 hover:text-blue-600 transition-colors disabled:opacity-50 flex-shrink-0 relative group"
          title="Upload Document"
        >
          {isUploading ? (
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          ) : (
             <FileUp size={20} />
          )}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.docx,.doc,.txt,.csv,.xlsx,.pptx,.json,.html"
          />
        </button>

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the document... (Shift+Enter for newline)"
          className="flex-1 max-h-48 min-h-[44px] bg-transparent border-0 focus:ring-0 resize-none p-3 text-gray-800 dark:text-gray-100 disabled:opacity-50"
          rows={1}
          disabled={isProcessing || isUploading}
          autoFocus
        />

        <button
          onClick={handleSend}
          disabled={!text.trim() || isProcessing || isUploading}
          className={`p-3 rounded-xl m-1 transition-all ${
            text.trim() && !isProcessing && !isUploading
              ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md transform active:scale-95'
              : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500'
          }`}
        >
          <Send size={18} className={text.trim() && !isProcessing ? 'translate-x-0.5' : ''} />
        </button>
      </div>
      <div className="text-center mt-2 text-xs text-gray-400 font-medium">
        Remember to upload a document first before asking questions.
      </div>
    </div>
  );
};

export default InputBox;
