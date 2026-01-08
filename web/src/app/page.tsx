"use client";

import { useState, useEffect, useRef } from 'react';
import { Send,  BookOpen, Activity, Search, AlertCircle, CheckCircle2, Copy } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { searchDocuments, getHealth } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  metadata?: any;
  timestamp: Date;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check API health on load
    getHealth().then(setHealth);
    
    // Initial welcome message
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am PyRAG, your engineering standards assistant.\n\nI can help you find information in **IS 3218**, **BS 5839**, and other technical documents. Ask me anything about:\n\n* Cable requirements\n* Fire alarm zones\n* Installation heights\n* Battery calculations',
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setIsLoading(true);

    try {
      const result = await searchDocuments(userMsg.content);
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.response,
        sources: result.sources,
        metadata: result.metadata,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiMsg]);
      
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Sorry, I encountered an error connecting to the server. Please check if the PyRAG backend is running.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 p-4 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-900/20">
              <BookOpen className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">PyRAG Web</h1>
              <p className="text-xs text-slate-400">Engineering Standards AI</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             <div className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium border ${health?.status === 'healthy' ? 'border-green-800 bg-green-900/30 text-green-400' : 'border-red-800 bg-red-900/30 text-red-400'}`}>
                <Activity size={14} />
                {health?.status === 'healthy' ? 'System Online' : 'Backend Offline'}
             </div>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 scroll-smooth">
        <div className="mx-auto max-w-4xl space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`flex max-w-[85%] flex-col gap-2 rounded-2xl p-4 shadow-lg ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800/80 border border-slate-700 text-slate-100'
                }`}
              >
                <div className="prose prose-invert max-w-none text-sm leading-relaxed">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {/* Sources Section */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 border-t border-slate-700/50 pt-3">
                    <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                      <Search size={12} /> Sources Used
                    </p>
                    <div className="grid gap-2 sm:grid-cols-2">
                       {msg.sources.slice(0, 4).map((source: any, idx: number) => (
                          <div key={idx} className="group relative cursor-pointer overflow-hidden rounded-lg bg-slate-900/50 p-2 hover:bg-slate-900 border border-transparent hover:border-slate-600 transition-all">
                             <div className="flex items-start gap-2">
                                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-slate-800 text-[10px] font-bold text-slate-400 group-hover:bg-blue-900 group-hover:text-blue-200">
                                   {idx + 1}
                                </span>
                                <div className="min-w-0 flex-1">
                                   <p className="truncate text-xs font-medium text-blue-200">
                                      {source.document || source.metadata?.file_name}
                                   </p>
                                   <div className="mt-0.5 flex items-center gap-2 text-[10px] text-slate-500">
                                      {source.page && <span>Page {source.page}</span>}
                                      {source.score && <span>{Math.round(source.score * 100)}% match</span>}
                                   </div>
                                </div>
                             </div>
                          </div>
                       ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
               <div className="flex max-w-[85%] items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
                  <div className="flex gap-1">
                     <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.3s]"></span>
                     <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.15s]"></span>
                     <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500"></span>
                  </div>
                  <span className="text-sm font-medium text-slate-400">Analyzing documents...</span>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800 bg-slate-900 p-4">
        <div className="mx-auto max-w-4xl">
          <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3.5 text-slate-200 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="absolute right-2 rounded-lg bg-blue-600 p-2 text-white shadow-lg transition-transform hover:bg-blue-500 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
            >
              <Send size={20} />
            </button>
          </form>
          <div className="mt-2 text-center">
             <p className="text-[10px] text-slate-600">
                PyRAG v2.0 • Powered by DeepSeek & GraphRAG • Detailed Chunking (128t) Enabled
             </p>
          </div>
        </div>
      </div>
    </main>
  );
}
