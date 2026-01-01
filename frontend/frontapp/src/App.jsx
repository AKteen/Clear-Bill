import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (content, type, data = null) => {
    const message = {
      id: Date.now(),
      content,
      type,
      timestamp: new Date(),
      data
    };
    setMessages(prev => [...prev, message]);
  };

  const fetchAllDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`);
      setDocuments(response.data);
      addMessage('📋 All documents loaded from database', 'bot');
    } catch (error) {
      if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        addMessage('❌ Cannot connect to server. Please check if backend is running on port 8000.', 'bot');
      } else {
        addMessage('Error fetching documents', 'bot');
      }
    }
  };

  const testConnection = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      addMessage('✅ Server connection successful', 'bot');
    } catch (error) {
      addMessage('❌ Server connection failed. Check if backend is running on port 8000.', 'bot');
    }
  };

  const formatInvoiceData = (text) => {
    if (!text) return text;
    
    const lines = text.split('\n');
    let inItemsSection = false;
    let formattedContent = [];
    let items = [];
    let totalAmount = '';
    
    lines.forEach(line => {
      if (line.includes('ITEMS:') || line.includes('Item |')) {
        inItemsSection = true;
        return;
      }
      
      if (line.includes('TOTAL:')) {
        totalAmount = line.replace('TOTAL:', '').trim();
        inItemsSection = false;
        return;
      }
      
      if (inItemsSection && line.includes('|')) {
        const parts = line.split('|').map(p => p.trim());
        if (parts.length >= 4) {
          items.push(parts);
        }
      } else if (!inItemsSection) {
        formattedContent.push(line);
      }
    });
    
    return { content: formattedContent.join('\n'), items, totalAmount };
  };

  const uploadFile = async (file) => {
    setIsLoading(true);
    addMessage(`Uploading ${file.name}...`, 'user');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { data } = response.data;
      addMessage('Document processed successfully!', 'bot', data);
      
      // Add to documents list
      setDocuments(prev => [data, ...prev]);
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Upload failed';
      
      if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        addMessage('❌ Cannot connect to server. Please check if backend is running on port 8000.', 'bot');
      } else if (error.response?.status === 400 && errorMsg.includes('policy violations')) {
        addMessage(`❌ Upload Rejected: ${errorMsg}`, 'bot');
        addMessage('Please ensure your document contains: Invoice Number, Amount, Date, and Vendor Name with valid formatting.', 'bot');
      } else if (error.response?.status === 400 && errorMsg.includes('Duplicate flagged')) {
        const parts = errorMsg.split('|');
        const header = parts[0];
        const filename = parts[1] || '';
        const datetime = parts[2] || '';
        
        addMessage(
          <div>
            <div className="text-red-500 font-bold text-lg mb-3">
              ⚠️ {header}
            </div>
            <div className="space-y-2">
              {filename && <p className="text-zinc-300 text-sm">{filename}</p>}
              {datetime && <p className="text-zinc-400 text-xs">{datetime}</p>}
            </div>
          </div>, 
          'bot'
        );
      } else {
        addMessage(`Error: ${errorMsg}`, 'bot');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      uploadFile(file);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file) {
      uploadFile(file);
    }
  };

  const handleDocumentClick = (doc) => {
    setSelectedDocument(doc);
    setMessages([
      {
        id: Date.now(),
        content: `Viewing ${doc.original_filename}`,
        type: 'user',
        timestamp: new Date(),
      },
      {
        id: Date.now() + 1,
        content: 'Document loaded from history',
        type: 'bot',
        timestamp: new Date(),
        data: doc
      }
    ]);
  };

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderAuditResult = (auditResult) => {
    if (!auditResult) return null;

    const { 
      is_compliant = false, 
      compliance_score = 0, 
      violations = [], 
      summary = '',
      approval_status = 'unknown',
      status_color = 'gray'
    } = auditResult;

    const getStatusIcon = (status) => {
      switch(status) {
        case 'approved': return '✅';
        case 'warning': return '⚠️';
        case 'rejected': return '❌';
        default: return '❓';
      }
    };

    const getStatusBg = (color) => {
      switch(color) {
        case 'green': return 'bg-green-600';
        case 'yellow': return 'bg-yellow-600';
        case 'red': return 'bg-red-600';
        default: return 'bg-gray-600';
      }
    };

    return (
      <div className="mt-4 p-4 bg-zinc-950 rounded-lg border border-zinc-800">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-zinc-300">Audit Result</span>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-3 py-1 rounded-full font-medium text-white ${
              getStatusBg(status_color)
            }`}>
              {getStatusIcon(approval_status)} {approval_status?.toUpperCase()}
            </span>
            <span className="text-xs px-2 py-1 rounded-full font-medium bg-zinc-700 text-zinc-300">
              {compliance_score}%
            </span>
          </div>
        </div>
        
        <p className="text-[15px] text-white mb-3 leading-relaxed">{summary}</p>
        
        {violations && violations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-zinc-400 mb-2">Issues Found:</h4>
            {violations.map((violation, index) => (
              <div key={index} className={`p-3 rounded-lg border-l-4 ${
                violation.severity === 'warning' ? 'bg-yellow-900/20 border-yellow-500 text-yellow-200' :
                violation.severity === 'high' ? 'bg-red-900/20 border-red-500 text-red-200' :
                'bg-orange-900/20 border-orange-500 text-orange-200'
              }`}>
                <div className="font-medium text-[15px] mb-1">{violation.rule_name}</div>
                <div className="text-sm opacity-90">{violation.message}</div>
                {violation.flagged_items && (
                  <div className="mt-2 text-xs opacity-75">
                    Flagged items: {violation.flagged_items.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-black text-orange-600 flex">
      {/* Fixed Sidebar */}
      <div className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col fixed h-full">
        <div className="p-3 border-b border-zinc-800">
          <h2 className="text-sm font-medium text-zinc-300">Document History</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {documents.length === 0 ? (
            <div className="p-4 text-center text-zinc-500 text-sm">
              No documents yet
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {documents.map((doc, index) => (
                <div
                  key={doc.id || index}
                  className={`p-3 rounded-lg cursor-pointer transition-colors hover:bg-zinc-900 ${
                    selectedDocument?.id === doc.id ? 'bg-zinc-900 border border-zinc-700' : ''
                  }`}
                  onClick={() => handleDocumentClick(doc)}
                >
                  <div className="text-sm font-medium text-orange-600 truncate">
                    {doc.original_filename}
                  </div>
                  <div className="text-xs text-zinc-400 mt-1">
                    {doc.file_type} • {new Date(doc.created_at).toLocaleDateString()}
                  </div>
                  {doc.is_duplicate && (
                    <div className="text-xs text-yellow-400 mt-1">⚠️ Duplicate</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content with left margin for fixed sidebar */}
      <div className="flex-1 flex flex-col ml-64">
        {/* Compact Navbar - Fixed */}
        <div className="bg-zinc-950 p-3 fixed top-0 right-0 left-64 z-10 flex justify-between items-center">
          <div>
            <h1 className="text-base font-medium text-orange-600">ClearBill</h1>
            <p className="text-xs text-zinc-400">AI-powered bill auditing and compliance verification</p>
          </div>
          <button 
            onClick={testConnection}
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-full text-xs flex items-center space-x-1 transition-colors mr-2"
          >
            <span>🔌</span>
            <span>Test Connection</span>
          </button>
          <button 
            onClick={fetchAllDocuments}
            className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-2 rounded-full text-xs flex items-center space-x-1 transition-colors"
          >
            <span>📋</span>
            <span>All Invoices</span>
          </button>
        </div>

        {/* Chat Area with top margin for fixed navbar */}
        <div className="flex-1 flex flex-col mt-16">
          <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-20">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full">
                <div className="text-center text-zinc-500">
                  <div className="text-5xl mb-4">📄</div>
                  <p className="text-lg">Upload a document to get started</p>
                  <p className="text-sm text-zinc-400 mt-2">Use the upload area at the bottom</p>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-2xl px-4 py-3 rounded-2xl shadow-lg ${
                  message.type === 'user' 
                    ? 'bg-zinc-950 text-white ml-auto rounded-br-md border border-zinc-800' 
                    : 'bg-black text-white mr-auto rounded-bl-md border border-zinc-800'
                }`}>
                  <div className="text-[15px] leading-relaxed">
                    {typeof message.content === 'string' ? message.content : message.content}
                  </div>
                  
                  {message.data && (
                    <div className="mt-3 space-y-2">
                      <div className="text-xs opacity-75 border-t border-zinc-800 pt-2">
                        <div className="mb-1">
                          <span className="font-medium">File:</span> {message.data.original_filename}
                        </div>
                        <div className="mb-1">
                          <span className="font-medium">Type:</span> {message.data.file_type}
                        </div>
                        {message.data.is_duplicate && (
                          <div className="text-yellow-300 font-medium">⚠️ Duplicate detected</div>
                        )}
                      </div>
                      
                      <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
                        <div className="font-medium mb-2 text-xs">AI Analysis:</div>
                        <div className="text-[15px] text-white leading-relaxed whitespace-pre-wrap">
                          {(() => {
                            const text = message.data.groq_response;
                            const lines = text.split('\n');
                            let items = [];
                            let total = '';
                            
                            // Extract items and amounts from AI response
                            lines.forEach(line => {
                              // Look for lines with $ amounts
                              if (line.includes('$') && line.trim().length > 5) {
                                const match = line.match(/(.+?)\s*[:\-\|]?\s*\$([\d.,]+)/);
                                if (match && match[1].length > 2) {
                                  items.push({ name: match[1].trim().replace(/^[\-\*\•]\s*/, ''), amount: match[2] });
                                }
                              }
                              // Look for total
                              if (line.toLowerCase().includes('total') && line.includes('$')) {
                                const totalMatch = line.match(/\$([\d.,]+)/);
                                if (totalMatch) total = totalMatch[1];
                              }
                            });
                            
                            return (
                              <div>
                                <div className="mb-4" dangerouslySetInnerHTML={{
                                  __html: text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                }} />
                                
                                {items.length > 0 && (
                                  <div className="mb-4">
                                    <div className="bg-zinc-900 rounded-lg overflow-hidden">
                                      <div className="grid grid-cols-2 gap-2 p-3 bg-zinc-800 text-xs font-medium text-zinc-300">
                                        <div>ITEM</div>
                                        <div>AMOUNT</div>
                                      </div>
                                      {items.map((item, idx) => (
                                        <div key={idx} className="grid grid-cols-2 gap-2 p-3 border-t border-zinc-800 text-sm">
                                          <div className="text-white">{item.name}</div>
                                          <div className="text-white font-medium">${item.amount}</div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {total && (
                                  <div className="bg-blue-600 px-4 py-2 rounded-md inline-block">
                                    <div className="text-white font-bold">
                                      TOTAL: ${total}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })()} 
                        </div>
                      </div>
                      
                      {renderAuditResult(message.data.audit_result)}
                    </div>
                  )}
                  
                  <div className="text-xs opacity-50 mt-2">
                    {formatTimestamp(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-2xl px-4 py-3 rounded-2xl shadow-lg bg-black text-white mr-auto rounded-bl-md border border-zinc-800">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    <span className="text-[15px]">Processing...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Fixed bottom upload zone */}
          <div className="fixed bottom-0 right-0 left-64 p-3 bg-black">
            <div 
              className={`border border-dashed rounded-lg p-3 text-center transition-colors cursor-pointer ${
                isDragOver 
                  ? 'border-blue-500 bg-blue-500/10' 
                  : 'border-zinc-700 hover:border-blue-500 hover:bg-zinc-900/50'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                className="hidden" 
                accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.tiff"
                onChange={handleFileSelect}
              />
              <div className="text-zinc-400">
                {isDragOver ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="text-lg">📁</div>
                    <p className="text-sm">Drop the file here...</p>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="text-lg">📎</div>
                    <div>
                      <p className="text-sm">Drag & drop or click to upload a file</p>
                      <p className="text-xs text-zinc-500 mt-1">Only compliant invoices accepted</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;