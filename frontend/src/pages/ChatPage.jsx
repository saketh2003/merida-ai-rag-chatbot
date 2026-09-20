import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import { chatApi } from '../services/api';
import {
  Plus,
  Trash2,
  Send,
  MessageSquare,
  Bot,
  User as UserIcon,
  FileText,
  AlertCircle,
  Loader2,
  ChevronRight
} from 'lucide-react';

export const ChatPage = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [loadingConv, setLoadingConv] = useState(false);
  const [sendingMsg, setSendingMsg] = useState(false);
  const [error, setError] = useState('');

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sendingMsg]);

  const fetchConversations = async () => {
    try {
      setError('');
      const data = await chatApi.listConversations();
      setConversations(data);
      if (data.length > 0 && !activeConvId) {
        selectConversation(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load user conversations.');
    }
  };

  const selectConversation = async (id) => {
    setActiveConvId(id);
    setLoadingConv(true);
    setError('');
    try {
      const data = await chatApi.getConversation(id);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation details:', err);
      setError('Failed to fetch conversation history.');
      setMessages([]);
    } finally {
      setLoadingConv(false);
    }
  };

  const handleCreateNewChat = async () => {
    try {
      setError('');
      const newConv = await chatApi.createConversation('New Conversation');
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create new chat:', err);
      setError('Could not create a new conversation.');
    }
  };

  const handleDeleteConversation = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;

    try {
      await chatApi.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        setActiveConvId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Could not delete conversation.');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const promptText = inputPrompt.trim();
    if (!promptText || sendingMsg) return;

    // Auto-create conversation if none selected
    let currentId = activeConvId;
    if (!currentId) {
      try {
        const newConv = await chatApi.createConversation();
        setConversations((prev) => [newConv, ...prev]);
        currentId = newConv.id;
        setActiveConvId(currentId);
      } catch (err) {
        setError('Failed to initialize new conversation session.');
        return;
      }
    }

    // Optimistically append user message to UI
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: promptText,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setInputPrompt('');
    setSendingMsg(true);
    setError('');

    try {
      const assistantMsg = await chatApi.sendMessage(currentId, promptText);
      setMessages((prev) => [...prev, assistantMsg]);
      fetchConversations(); // refresh title if updated
    } catch (err) {
      console.error('Failed to send message:', err);
      const errMsg = err.response?.data?.detail || 'Failed to generate response from RAG system.';
      setError(errMsg);
    } finally {
      setSendingMsg(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Top Navbar */}
      <Navbar />

      {/* Main Container */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col border-r border-slate-800">
          <div className="p-3">
            <button
              onClick={handleCreateNewChat}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-lg text-sm shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>New Chat</span>
            </button>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1">
            <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Your Conversations
            </div>

            {conversations.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500">
                No active conversations yet. Click 'New Chat' to start.
              </div>
            ) : (
              conversations.map((conv) => {
                const isActive = conv.id === activeConvId;
                return (
                  <div
                    key={conv.id}
                    onClick={() => selectConversation(conv.id)}
                    className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
                      isActive
                        ? 'bg-slate-800 text-white font-medium border border-slate-700'
                        : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-brand-400' : 'text-slate-500'}`} />
                      <span className="truncate">{conv.title}</span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(e, conv.id)}
                      className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 p-1 rounded transition-opacity"
                      title="Delete chat"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col bg-white overflow-hidden">
          {/* Global Alert Bar */}
          {error && (
            <div className="bg-red-50 border-b border-red-200 text-red-700 px-4 py-2 text-xs flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
              <button onClick={() => setError('')} className="text-red-500 hover:text-red-800 font-bold">
                ×
              </button>
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
            {!activeConvId && messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-500">
                <div className="w-16 h-16 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mb-4">
                  <Bot className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-bold text-gray-800 mb-1">Knowledge Base Assistant</h3>
                <p className="text-sm text-gray-500 max-w-md">
                  Ask questions about documents uploaded by the admin in the knowledge base.
                </p>
              </div>
            ) : loadingConv ? (
              <div className="h-full flex items-center justify-center text-gray-500 space-x-2 text-sm">
                <Loader2 className="w-5 h-5 animate-spin text-brand-600" />
                <span>Loading chat history...</span>
              </div>
            ) : (
              messages.map((msg) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={msg.id}
                    className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold text-xs shadow-sm ${
                        isUser ? 'bg-brand-600' : 'bg-slate-800'
                      }`}
                    >
                      {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4 text-brand-400" />}
                    </div>

                    {/* Content Box */}
                    <div
                      className={`max-w-2xl rounded-2xl p-4 text-sm shadow-sm ${
                        isUser
                          ? 'bg-brand-600 text-white rounded-tr-none'
                          : 'bg-gray-100 text-gray-900 border border-gray-200 rounded-tl-none'
                      }`}
                    >
                      <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                    </div>
                  </div>
                );
              })
            )}

            {/* Thinking Indicator */}
            {sendingMsg && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-slate-800 text-brand-400 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-gray-100 text-gray-600 border border-gray-200 rounded-2xl rounded-tl-none p-3 text-xs flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                  <span>Searching Knowledge Base & generating answer...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <form onSubmit={handleSendMessage} className="flex items-center space-x-2 max-w-4xl mx-auto">
              <input
                type="text"
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                placeholder="Ask a question about the knowledge base..."
                disabled={sendingMsg}
                className="flex-1 bg-white border border-gray-300 rounded-lg px-4 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputPrompt.trim() || sendingMsg}
                className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-colors flex items-center space-x-1 disabled:opacity-50"
              >
                <span>Send</span>
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ChatPage;
