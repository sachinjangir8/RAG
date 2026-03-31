import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check } from 'lucide-react';
import { motion } from 'framer-motion';

const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex w-full max-w-4xl px-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-4`}>
        {/* Avatar */}
        <div className="flex-shrink-0 flex items-start mt-1">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white shadow-sm ring-1 ring-black/5'
          }`}>
            {isUser ? <User size={20} /> : <Bot size={20} />}
          </div>
        </div>

        {/* Bubble */}
        <div className={`flex-1 overflow-hidden relative group p-4 rounded-2xl shadow-sm ${
          isUser 
            ? 'bg-blue-600 text-white rounded-tr-none' 
            : 'bg-white text-gray-800 dark:bg-gray-800 dark:text-gray-100 rounded-tl-none ring-1 ring-black/5 dark:ring-white/10'
        }`}>
          {/* Action buttons (only for AI) */}
          {!isUser && message.content && (
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                title="Copy message"
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
            </div>
          )}

          <div className={`prose ${isUser ? 'prose-invert' : 'dark:prose-invert'} max-w-none text-sm md:text-base`}>
            {message.isLoading ? (
              <div className="flex items-center gap-1.5 h-6">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({node, inline, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={dracula}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-md my-4"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
          
          {message.timestamp && (
            <div className={`text-xs mt-2 text-right ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          )}

          {/* Source Citations */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
              <span className="font-semibold block mb-1">Sources Reference:</span>
              <ul className="space-y-1 list-disc list-inside">
                {message.sources.map((s, idx) => (
                  <li key={idx} className="truncate">
                    {s.filename} (Chunk {s.chunk_index + 1}) - Score {s.relevance_score.toFixed(2)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;
