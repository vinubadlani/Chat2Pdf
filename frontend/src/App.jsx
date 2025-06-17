import { useState, useRef, useEffect } from 'react';
import { Upload, Send, MessageCircle, FileText, Sparkles, Plus, Settings, User, Bot, Paperclip, MoreHorizontal, ChevronDown, Star, Clock, Zap } from 'lucide-react';
import axios from 'axios';

const ModernChatPDF = () => {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [searchHistory, setSearchHistory] = useState([
    "What are the main points discussed?",
    "Summarize the conclusions",
    "Extract key financial data",
    "List all mentioned companies"
  ]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [typingIndex, setTypingIndex] = useState(-1);
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const typingSpeed = 5; // milliseconds per character

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, displayedText]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [question]);

  // Typing animation effect
  useEffect(() => {
    if (typingIndex >= 0 && typingIndex < messages.length && messages[typingIndex].type === 'ai') {
      const fullText = messages[typingIndex].content;
      let currentIndex = 0;
      setIsTyping(true);
      setDisplayedText("");
      
      const typingInterval = setInterval(() => {
        if (currentIndex < fullText.length) {
          setDisplayedText(prev => prev + fullText[currentIndex]);
          currentIndex++;
        } else {
          clearInterval(typingInterval);
          setIsTyping(false);
          setTypingIndex(-1);
        }
      }, typingSpeed);
      
      return () => clearInterval(typingInterval);
    }
  }, [typingIndex, messages]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files[0] && files[0].type === 'application/pdf') {
      setFile(files[0]);
    }
  };

  const uploadPDF = async () => {
    if (!file) {
      setUploadStatus("Please select a PDF file first!");
      return;
    }
    
    setLoading(true);
    setUploadStatus("Analyzing document...");
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      // Fix URL formatting to prevent double slashes
      const baseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      // Remove trailing slashes from the base URL
      const cleanBaseUrl = baseUrl.replace(/\/+$/, '');
      const uploadEndpoint = '/upload';
      const url = `${cleanBaseUrl}${uploadEndpoint}`;
      
      console.log("Making request to:", url); // Debug log
      
      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setUploadStatus("✨ Document ready for questions!");
      setUploadedFileName(file.name);
      
      const welcomeMessage = {
        type: 'ai',
        content: `Great! I've analyzed "${file.name}". I can now help you with questions about the document's content, summaries, key insights, and more. What would you like to know?`
      };
      
      setMessages([welcomeMessage]);
      setTypingIndex(0); // Start typing animation for the welcome message
      
    } catch (error) {
      setUploadStatus("❌ Error uploading PDF: " + (error.response?.data?.detail || error.message));
      console.error("Upload error:", error);
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;
    if (!uploadedFileName) {
      setUploadStatus("Please upload a PDF first!");
      return;
    }

    const currentQuestion = question;
    setQuestion("");
    
    const userMessage = { type: 'user', content: currentQuestion };
    setMessages(prev => [...prev, userMessage]);
    
    setSearchHistory(prev => [currentQuestion, ...prev.slice(0, 9)]);
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append("question", currentQuestion);
      
      // More robust URL handling to prevent double slashes
      const baseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      // Remove trailing slashes from the base URL
      const cleanBaseUrl = baseUrl.replace(/\/+$/, '');
      const askEndpoint = '/ask';
      const url = `${cleanBaseUrl}${askEndpoint}`;
      
      console.log("Making question request to:", url); // Debug log
      
      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const aiMessage = { 
        type: 'ai', 
        content: response.data.answer
      };
      setMessages(prev => [...prev, aiMessage]);
      setTypingIndex(messages.length + 1); // Set typing index to the new message
      
    } catch (error) {
      const errorMessage = { 
        type: 'ai', 
        content: "❌ Error getting answer: " + (error.response?.data?.detail || error.message)
      };
      setMessages(prev => [...prev, errorMessage]);
      setTypingIndex(messages.length + 1); // Set typing index to the error message
      console.error("Question error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  const handleHistoryClick = (historyQuestion) => {
    setQuestion(historyQuestion);
  };

  const newChat = () => {
    setMessages([]);
    setQuestion("");
    setUploadedFileName("");
    setFile(null);
    setUploadStatus("");
    setTypingIndex(-1);
    setDisplayedText("");
    setIsTyping(false);
  };

  const quickPrompts = [
    { icon: <Sparkles className="w-4 h-4" />, text: "Summarize key points", color: "from-purple-500 to-pink-500" },
    { icon: <FileText className="w-4 h-4" />, text: "Extract main topics", color: "from-blue-500 to-cyan-500" },
    { icon: <Star className="w-4 h-4" />, text: "Find important dates", color: "from-amber-500 to-orange-500" },
    { icon: <Zap className="w-4 h-4" />, text: "Quick analysis", color: "from-green-500 to-emerald-500" }
  ];

  // Render message content with typing animation for AI messages
  const renderMessageContent = (message, index) => {
    if (message.type === 'user' || index !== typingIndex) {
      return message.content;
    }
    
    return displayedText;
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Sidebar */}
      <div className={`${showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 bg-white/70 backdrop-blur-xl border-r border-white/20 flex flex-col shadow-2xl relative overflow-hidden`}>
        <div className="absolute inset-0 bg-gradient-to-b from-white/50 to-white/30"></div>
        
        {/* Header */}
        <div className="relative p-6 border-b border-white/20">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  ChatPDF Pro
                </h1>
                <p className="text-xs text-slate-500">AI-Powered Document Chat</p>
              </div>
            </div>
            <button
              onClick={() => setShowSidebar(false)}
              className="lg:hidden p-2 hover:bg-white/50 rounded-xl transition-colors"
            >
              <ChevronDown className="w-4 h-4 rotate-90" />
            </button>
          </div>
          
          <button 
            onClick={newChat}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium py-3 px-4 rounded-2xl transition-all duration-200 transform hover:scale-[1.02] flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
          >
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        {/* Current Document */}
        {uploadedFileName && (
          <div className="relative p-4 bg-gradient-to-r from-indigo-50/80 to-purple-50/80 border-b border-white/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-xl flex items-center justify-center">
                <FileText className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-800 truncate">{uploadedFileName}</p>
                <p className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Chat History */}
        <div className="relative flex-1 p-4 overflow-y-auto">
          <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Recent Chats
          </h3>
          
          {searchHistory.length > 0 ? (
            <div className="space-y-2">
              {searchHistory.map((item, index) => (
                <button
                  key={index}
                  onClick={() => handleHistoryClick(item)}
                  className="w-full text-left p-3 hover:bg-white/60 rounded-xl text-sm text-slate-600 hover:text-slate-900 transition-all duration-200 line-clamp-2 group"
                >
                  <div className="flex items-start gap-2">
                    <MessageCircle className="w-3 h-3 mt-1 text-slate-400 group-hover:text-indigo-500 transition-colors" />
                    <span className="flex-1">{item}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-slate-400 text-sm space-y-4">
              <div className="p-4 bg-white/40 rounded-xl border border-white/30">
                <h4 className="font-medium text-slate-600 mb-2">Get Started:</h4>
                <ul className="space-y-2 text-xs">
                  <li className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full"></div>
                    Upload your PDF document
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-400 rounded-full"></div>
                    Ask questions about content
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-pink-400 rounded-full"></div>
                    Get AI-powered insights
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Upload Section */}
        <div className="relative p-4 border-t border-white/20">
          <div 
            className={`mb-4 border-2 border-dashed rounded-2xl p-6 transition-all duration-300 ${
              isDragOver 
                ? 'border-indigo-400 bg-indigo-50/50 scale-[1.02]' 
                : file 
                  ? 'border-green-400 bg-green-50/50' 
                  : 'border-slate-300 hover:border-slate-400 hover:bg-white/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input 
              ref={fileInputRef}
              type="file" 
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])} 
              className="hidden"
            />
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="cursor-pointer flex flex-col items-center gap-3 text-center"
            >
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 ${
                file ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-500'
              }`}>
                {file ? <FileText className="w-6 h-6" /> : <Upload className="w-6 h-6" />}
              </div>
              <div className="text-sm">
                {file ? (
                  <div>
                    <p className="font-medium text-green-700">{file.name}</p>
                    <p className="text-xs text-green-600">Ready to upload</p>
                  </div>
                ) : (
                  <div>
                    <p className="font-medium text-slate-700">Drop PDF here</p>
                    <p className="text-xs text-slate-500">or click to browse</p>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <button 
            onClick={uploadPDF} 
            disabled={loading || !file}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-slate-300 disabled:to-slate-400 text-white font-medium py-3 px-4 rounded-2xl transition-all duration-200 transform hover:scale-[1.02] disabled:scale-100 disabled:cursor-not-allowed shadow-lg hover:shadow-xl disabled:shadow-none"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Processing...
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2">
                <Upload className="w-4 h-4" />
                Upload & Analyze
              </div>
            )}
          </button>
          
          {uploadStatus && (
            <div className="mt-3 p-3 rounded-xl bg-white/60 backdrop-blur-sm text-xs text-slate-600 border border-white/30">
              {uploadStatus}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white/70 backdrop-blur-xl border-b border-white/20 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            {!showSidebar && (
              <button
                onClick={() => setShowSidebar(true)}
                className="lg:hidden p-2 hover:bg-white/50 rounded-xl transition-colors"
              >
                <MoreHorizontal className="w-5 h-5" />
              </button>
            )}
            
            <div className="flex items-center gap-4 flex-1 justify-center lg:justify-start">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <h2 className="text-lg font-semibold text-slate-800">
                  {uploadedFileName ? `Chatting with ${uploadedFileName}` : "Ready to analyze your document"}
                </h2>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button className="p-2 hover:bg-white/50 rounded-xl transition-colors">
                <Settings className="w-5 h-5 text-slate-500" />
              </button>
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="max-w-4xl mx-auto text-center py-20">
              <div className="w-24 h-24 bg-gradient-to-br from-indigo-100 via-purple-100 to-pink-100 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                <MessageCircle className="w-12 h-12 text-indigo-600" />
              </div>
              <h3 className="text-3xl font-bold text-slate-800 mb-4">
                Welcome to ChatPDF Pro
              </h3>
              <p className="text-slate-600 text-lg max-w-2xl mx-auto mb-8">
                Upload any PDF document and start having intelligent conversations with your content. 
                Get summaries, ask questions, and extract insights instantly.
              </p>
              
              {!uploadedFileName && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                  {quickPrompts.map((prompt, index) => (
                    <div
                      key={index}
                      className="p-4 bg-white/60 backdrop-blur-sm rounded-2xl border border-white/30 hover:bg-white/80 transition-all duration-200 cursor-pointer group"
                    >
                      <div className={`w-8 h-8 bg-gradient-to-r ${prompt.color} rounded-lg flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                        {prompt.icon}
                      </div>
                      <p className="text-sm font-medium text-slate-700">{prompt.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message, index) => (
                <div key={index} className={`flex gap-4 ${
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                }`}>
                  {message.type === 'ai' && (
                    <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg flex-shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div className={`max-w-2xl ${
                    message.type === 'user' 
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-3xl rounded-br-lg p-4 shadow-lg' 
                      : 'bg-white/80 backdrop-blur-sm text-slate-800 rounded-3xl rounded-bl-lg p-4 shadow-sm border border-white/30'
                  }`}>
                    <p className="leading-relaxed whitespace-pre-wrap">
                      {renderMessageContent(message, index)}
                      {message.type === 'ai' && index === typingIndex && (
                        <span className="inline-block w-1 h-4 ml-1 bg-indigo-500 animate-pulse"></span>
                      )}
                    </p>
                  </div>
                  {message.type === 'user' && (
                    <div className="w-10 h-10 bg-gradient-to-br from-slate-400 to-slate-600 rounded-2xl flex items-center justify-center shadow-lg flex-shrink-0">
                      <User className="w-5 h-5 text-white" />
                    </div>
                  )}
                </div>
              ))}
              
              {loading && (
                <div className="flex gap-4 justify-start">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-white/80 backdrop-blur-sm rounded-3xl rounded-bl-lg p-4 shadow-sm border border-white/30">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                        <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                      </div>
                      <span className="text-slate-500 text-sm ml-2">AI is analyzing...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white/70 backdrop-blur-xl border-t border-white/20 p-6 shadow-lg">
          <div className="max-w-4xl mx-auto">
            {uploadedFileName && messages.length === 0 && (
              <div className="mb-4 flex flex-wrap gap-2">
                {quickPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => setQuestion(prompt.text)}
                    className="flex items-center gap-2 px-4 py-2 bg-white/60 hover:bg-white/80 rounded-full text-sm font-medium text-slate-700 transition-all duration-200 border border-white/30 hover:scale-105"
                  >
                    {prompt.icon}
                    {prompt.text}
                  </button>
                ))}
              </div>
            )}
            
            <div className="relative flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={uploadedFileName ? "Ask anything about your document..." : "Upload a PDF first to start chatting"}
                  className="w-full p-4 pr-20 bg-white/80 backdrop-blur-sm border border-white/30 rounded-3xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none transition-all duration-200 shadow-sm hover:shadow-md placeholder-slate-400"
                  rows="1"
                  style={{ minHeight: '56px', maxHeight: '120px' }}
                  disabled={!uploadedFileName || isTyping}
                />
                <div className="absolute right-2 bottom-2 flex items-center gap-2">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-slate-400 hover:text-indigo-500 transition-colors rounded-xl hover:bg-white/50"
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={askQuestion} 
                    disabled={loading || !question.trim() || !uploadedFileName || isTyping}
                    className="p-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 disabled:scale-100 shadow-lg hover:shadow-xl"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            <div className="mt-3 text-xs text-slate-500 text-center flex items-center justify-center gap-4">
              <span>Press Enter to send • Shift+Enter for new line</span>
              <div className="flex items-center gap-1">
                <div className="w-1 h-1 bg-slate-300 rounded-full"></div>
                <span>Powered by AI</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModernChatPDF;
