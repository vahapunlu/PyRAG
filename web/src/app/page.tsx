"use client";

import { useState, useEffect, useRef } from 'react';
import { 
  Send, BookOpen, Activity, Search, AlertCircle, CheckCircle2, Copy,
  LayoutDashboard, FileText, BarChart3, Trash2, History, Link, GitBranch,
  Settings, Database, Zap, Menu
} from 'lucide-react';
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

  // Theme Colors (Docker Desktop / GitHub Dark)
  const colors = {
    sidebar: 'bg-[#000000]',     // Pure Black Sidebar
    main: 'bg-[#191919]',        // Dark Gray Main
    border: 'border-[#30363D]',  // Subtle borders
    text: 'text-[#e6edf3]',      // High contrast text
    textDim: 'text-[#8b949e]',   // Dimmed text
    hover: 'hover:bg-[#21262d]', // Item hover
    accent: 'bg-[#0090FF]',      // Docker Blue
  };

  useEffect(() => {
    // Check API health on load
    getHealth().then(setHealth);
    
    // Initial welcome message
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: '## ⚡ PyRAG Ready\n\nI am connected to the local engineering standards database.\n\n**Common Queries:**\n* "What is the maximum height for call points?"\n* "Calculate battery requirements for L1 system"\n* "Show me reference 23.3 in IS3218"',
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
        content: '❌ **Connection Error**\n\nCould not reach the PyRAG backend. Ensure `python main.py serve` is running.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const SidebarItem = ({ icon: Icon, label, onClick, active = false, danger = false }: any) => (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
        active 
          ? 'bg-[#1f6feb]/20 text-[#58a6ff]' 
          : danger 
            ? 'text-red-400 hover:bg-[#21262d]' 
            : 'text-[#c9d1d9] hover:bg-[#21262d]'
      }`}
    >
      <Icon size={16} />
      {label}
    </button>
  );

  return (
    <div className={`flex h-screen w-full overflow-hidden ${colors.sidebar} text-slate-200 font-sans`}>
      
      {/* 1. LEFT SIDEBAR (Fixed Width) */}
      <aside className={`w-[260px] flex-shrink-0 flex flex-col border-r ${colors.border} ${colors.sidebar}`}>
        
        {/* Header */}
        <div className="p-5">
           <div className="flex items-center gap-2 mb-1">
             <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-blue-600">
               ⚡ PyRAG
             </div>
           </div>
           <div className={`text-xs ${colors.textDim}`}>Engineering Standards AI</div>
        </div>

        {/* Action Button */}
        <div className="px-3 mb-6">
          <button className={`w-full flex items-center justify-center gap-2 ${colors.accent} hover:bg-blue-600 text-white font-semibold py-2.5 px-4 rounded-md transition-all`}>
            <span>New Document</span>
          </button>
        </div>

        {/* Menu Items */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          <div className={`px-3 py-2 text-xs font-semibold uppercase tracking-wider ${colors.textDim}`}>General</div>
          <SidebarItem icon={BarChart3} label="Statistics" />
          <SidebarItem icon={History} label="Query History" />
          
          <div className={`mt-6 px-3 py-2 text-xs font-semibold uppercase tracking-wider ${colors.textDim}`}>Tools</div>
          <SidebarItem icon={Link} label="Cross-Reference" />
          <SidebarItem icon={GitBranch} label="Rule Miner" />
          <SidebarItem icon={LayoutDashboard} label="Graph View" />

          <div className={`mt-6 px-3 py-2 text-xs font-semibold uppercase tracking-wider ${colors.textDim}`}>System</div>
          <SidebarItem icon={Trash2} label="Clear Chat" />
          <SidebarItem icon={Zap} label="Clear Cache" />
          <SidebarItem icon={Settings} label="Settings" />
        </div>

        {/* Footer Status */}
        <div className={`p-4 border-t ${colors.border} bg-black/20`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">API Status</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${health?.status === 'online' ? 'border-green-800 text-green-400' : 'border-red-800 text-red-400'}`}>
              {health?.status === 'online' ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
             <div className="w-2 h-2 rounded-full bg-green-500"></div>
             <span>OpenAI Embeddings</span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-1">
             <div className="w-2 h-2 rounded-full bg-green-500"></div>
             <span>DeepSeek LLM</span>
          </div>
        </div>
      </aside>

      {/* 2. MAIN CONTENT AREA */}
      <main className={`flex-1 flex flex-col min-w-0 ${colors.main}`}>
        
        {/* Top Navigation Bar (Minimal) */}
        <header className={`h-14 border-b ${colors.border} flex items-center justify-between px-6 bg-[#191919]/50 backdrop-blur`}>
            <div className="flex items-center gap-4">
               <span className="text-sm font-medium text-slate-400">Workspace /</span>
               <span className="text-sm font-semibold text-white">Engineering Standards</span>
            </div>
            <div className="flex items-center gap-4">
               <button className="p-2 rounded-md hover:bg-[#30363d] text-slate-400">
                  <Database size={18} />
               </button>
            </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
          <div className="mx-auto max-w-3xl space-y-8">
            {messages.map((msg) => (
              <div key={msg.id} className="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {/* Avatar */}
                <div className={`w-8 h-8 rounded mt-1 flex-shrink-0 flex items-center justify-center font-bold text-xs ${
                  msg.role === 'assistant' 
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-900' 
                    : 'bg-slate-700 text-slate-300'
                }`}>
                  {msg.role === 'assistant' ? 'AI' : 'YOU'}
                </div>

                {/* Message Bubble */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 mb-1">
                     <span className="text-sm font-bold text-slate-200">
                        {msg.role === 'assistant' ? 'PyRAG Assistant' : 'You'}
                     </span>
                     <span className="text-[10px] text-slate-500">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                     </span>
                  </div>
                  
                  <div className={`prose prose-invert max-w-none text-[15px] leading-relaxed ${colors.text}`}>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>

                  {/* Sources Widget */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-[#30363d]">
                      <div className="flex items-center gap-2 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
                         <Search size={12} /> References
                      </div>
                      <div className="flex flex-wrap gap-2">
                         {msg.sources.slice(0, 3).map((s: any, i: number) => (
                            <div key={i} className="flex items-center gap-2 bg-[#21262d] border border-[#30363d] px-2 py-1.5 rounded text-xs text-blue-400 hover:border-blue-800 transition-colors cursor-pointer">
                               <FileText size={12} />
                               <span className="truncate max-w-[150px]">{s.metadata?.file_name || 'Document'}</span>
                               <span className="text-slate-600 bg-black/30 px-1 rounded">p.{s.page}</span>
                            </div>
                         ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
               <div className="flex gap-4 pl-12">
                  <div className="flex gap-1.5 items-center bg-[#21262d] px-4 py-3 rounded-lg">
                     <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                     <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-75"></div>
                     <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-150"></div>
                  </div>
               </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-6 pt-2">
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSubmit} className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg opacity-20 group-focus-within:opacity-100 transition duration-500 blur"></div>
              <div className="relative flex items-end gap-2 bg-[#0d1117] border border-[#30363d] rounded-lg p-2 shadow-2xl">
                 <input
                   autoFocus
                   type="text"
                   value={query}
                   onChange={(e) => setQuery(e.target.value)}
                   placeholder="Ask a question about engineering standards (IS 3218, BS 5839)..."
                   className="w-full bg-transparent text-sm text-slate-200 placeholder-slate-600 px-3 py-2.5 focus:outline-none min-h-[44px]"
                   disabled={isLoading}
                 />
                 <button
                   type="submit"
                   disabled={isLoading || !query.trim()}
                   className="p-2 mb-0.5 rounded-md bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 transition-all"
                 >
                   <Send size={16} />
                 </button>
              </div>
            </form>
            <div className="mt-2 text-center text-[10px] text-slate-600">
               Press Enter to send • ⌘K to clear history • Powered by Local DeepSeek
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
