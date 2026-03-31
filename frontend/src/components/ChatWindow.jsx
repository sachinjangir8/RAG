import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';

const ChatWindow = ({ messages, isProcessing }) => {
  const bottomRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isProcessing]);

  return (
    <div className="flex-1 w-full overflow-y-auto px-4 py-6 scroll-smooth">
      <div className="max-w-4xl mx-auto flex flex-col items-center justify-start flex-1 min-h-full">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center text-gray-400 mt-20 space-y-4">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
              <span className="text-2xl">📄</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300">Welcome to DocMind</h2>
            <p className="max-w-md">
              Upload a PDF, Word document, Excel sheet, or CSV using the file button below, then start asking questions.
            </p>
          </div>
        ) : (
          <div className="w-full flex flex-col">
            {messages.map((msg, index) => (
              <MessageBubble key={index} message={msg} />
            ))}
            {isProcessing && (
              <MessageBubble
                message={{
                  role: 'assistant',
                  isLoading: true,
                }}
              />
            )}
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatWindow;
