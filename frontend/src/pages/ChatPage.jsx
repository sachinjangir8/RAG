import React, { useState, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import { streamChat } from '../services/api';
import { AlertCircle, FileText, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatPage = () => {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return [];
      }
    }
    return [];
  });
  
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('sessionId') || '';
  });
  
  const [uploadedFiles, setUploadedFiles] = useState(() => {
    const saved = localStorage.getItem('uploadedFiles');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return [];
      }
    }
    return [];
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const [errorBanner, setErrorBanner] = useState('');

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
    localStorage.setItem('sessionId', sessionId);
    localStorage.setItem('uploadedFiles', JSON.stringify(uploadedFiles));
  }, [messages, sessionId, uploadedFiles]);

  const handleSend = async (text) => {
    if (!sessionId) {
      setErrorBanner('Please upload a document before chatting.');
      return;
    }

    const newUserMsg = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setIsProcessing(true);
    setErrorBanner('');

    // Filter message history for backend
    const history = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    let currentResponse = '';

    const handleChunk = (chunkStr) => {
      currentResponse += chunkStr;
      
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.id === 'current-stream') {
          // Update existing assistant message
          const newPrev = [...prev];
          newPrev[newPrev.length - 1] = {
            ...lastMsg,
            content: currentResponse,
            timestamp: new Date().toISOString(),
          };
          return newPrev;
        } else {
          // Add new assistant message
          return [
            ...prev,
            {
              id: 'current-stream',
              role: 'assistant',
              content: currentResponse,
              timestamp: new Date().toISOString(),
            },
          ];
        }
      });
      setIsProcessing(false);
    };

    const handleError = (errMsg) => {
      setErrorBanner(errMsg);
      setIsProcessing(false);
      setMessages((prev) => {
         const last = prev[prev.length - 1];
         if (last && last.id === 'current-stream') {
            const newPrev = [...prev];
            delete newPrev[newPrev.length - 1].id;
            return newPrev;
         }
         return prev;
      });
    };

    const handleDone = () => {
      setIsProcessing(false);
      setMessages((prev) => {
         const last = prev[prev.length - 1];
         if (last && last.id === 'current-stream') {
            const newPrev = [...prev];
            delete newPrev[newPrev.length - 1].id;
            return newPrev;
         }
         return prev;
      });
    };

    // Delay start slightly to feel more human
    setTimeout(() => {
      streamChat(text, sessionId, history, handleChunk, handleError, handleDone);
    }, 500);
  };

  const handleUploadSuccess = (fileInfo) => {
    setUploadedFiles((prev) => {
      if (prev.find((f) => f.filename === fileInfo.filename)) {
         return prev;
      }
      return [...prev, fileInfo];
    });
    setErrorBanner('');
    
    // Add system notification in chat
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: `I've successfully processed **${fileInfo.filename}**. You can now ask me questions about it!`,
        timestamp: new Date().toISOString(),
      }
    ]);
  };

  const handleUploadError = (err) => {
    setErrorBanner(err);
  };

  const resetSession = () => {
    setMessages([]);
    setSessionId('');
    setUploadedFiles([]);
    setErrorBanner('');
    localStorage.removeItem('chatHistory');
    localStorage.removeItem('sessionId');
    localStorage.removeItem('uploadedFiles');
  };

  return (
    <div className="flex flex-col h-screen w-full bg-white dark:bg-gray-900 border-x border-gray-100 dark:border-gray-800 md:max-w-6xl md:mx-auto">
      {/* Header */}
      <header className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 text-white p-2 rounded-xl shadow-sm">
            <FileText size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              DocMind Chat
            </h1>
            {uploadedFiles.length > 0 ? (
              <p className="text-xs text-gray-500 font-medium">Session Active • {uploadedFiles.length} file(s)</p>
            ) : (
              <p className="text-xs text-gray-400">Waiting for Document Upload...</p>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {sessionId && (
            <button
              onClick={resetSession}
              className="text-xs px-3 py-1.5 rounded-full bg-gray-100 hover:bg-red-50 text-gray-600 hover:text-red-500 transition-colors"
            >
              Clear Session
            </button>
          )}
        </div>
      </header>

      {/* Error Banner */}
      <AnimatePresence>
        {errorBanner && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-red-50 dark:bg-red-900/20 border-b border-red-100 dark:border-red-900/30 overflow-hidden"
          >
            <div className="px-6 py-3 flex items-start gap-3">
              <AlertCircle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-400 font-medium flex-1">
                {errorBanner}
              </p>
              <button 
                onClick={() => setErrorBanner('')}
                className="text-red-400 hover:text-red-600 transition-colors p-1"
              >
                <X size={16} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Uploaded Files Chips */}
      {uploadedFiles.length > 0 && (
         <div className="px-6 pt-3 flex flex-wrap gap-2">
            {uploadedFiles.map((f, i) => (
              <div key={i} className="flex items-center gap-1.5 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/50 text-blue-700 dark:text-blue-300 text-xs px-2.5 py-1 rounded-md">
                 <FileText size={12} />
                 <span>{f.filename}</span>
              </div>
            ))}
         </div>
      )}

      {/* Chat Area */}
      <ChatWindow messages={messages} isProcessing={isProcessing} />

      {/* Input Area */}
      <div className="flex-shrink-0 bg-gradient-to-t from-white via-white to-transparent dark:from-gray-900 dark:via-gray-900 pt-8 mt-auto">
        <InputBox
          onSend={handleSend}
          isProcessing={isProcessing}
          sessionId={sessionId}
          setSessionId={setSessionId}
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />
      </div>
    </div>
  );
};

export default ChatPage;
