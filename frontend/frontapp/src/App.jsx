import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [editingDoc, setEditingDoc] = useState(null);
  const [newName, setNewName] = useState('');
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

  const renameDocument = async (docId, newName) => {
    try {
      await axios.put(`${API_BASE_URL}/document/${docId}/rename?new_name=${encodeURIComponent(newName)}`);
      setDocuments(prev => prev.map(doc => 
        doc.id === docId ? {...doc, original_filename: newName} : doc
      ));
      setEditingDoc(null);
      addMessage(`Document renamed to "${newName}"`, 'bot');
    } catch (error) {
      addMessage('Error renaming document', 'bot');
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
      <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">Audit Result</span>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-3 py-1 rounded-full font-medium text-white ${
              getStatusBg(status_color)
            }`}>
              {getStatusIcon(approval_status)} {approval_status?.toUpperCase()}
            </span>
            <span className="text-xs px-2 py-1 rounded-full font-medium bg-gray-200 text-gray-700">
              {compliance_score}%
            </span>
          </div>
        </div>
        
        <p className="text-[15px] text-gray-800 mb-3 leading-relaxed">{summary}</p>
        
        {violations && violations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-gray-600 mb-2">Issues Found:</h4>
            {violations.map((violation, index) => (
              <div key={index} className={`p-3 rounded-lg border-l-4 ${
                violation.severity === 'warning' ? 'bg-amber-50 border-amber-400 text-amber-800' :
                violation.severity === 'high' ? 'bg-red-50 border-red-400 text-red-800' :
                'bg-orange-50 border-orange-400 text-orange-800'
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
    <div className="min-h-screen bg-gray-50 text-gray-800 flex">
      {/* Fixed Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col fixed h-full shadow-sm">
        <div className="p-3 border-b border-gray-200">
          <h2 className="text-sm font-medium text-gray-700">Document History</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {documents.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No documents yet
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {documents.map((doc, index) => (
                <div
                  key={doc.id || index}
                  className={`p-3 pb-8 rounded-lg cursor-pointer transition-colors hover:bg-gray-100 relative ${
                    selectedDocument?.id === doc.id ? 'bg-blue-50 border border-blue-200' : ''
                  }`}
                >
                  <div onClick={() => handleDocumentClick(doc)}>
                    {editingDoc === doc.id ? (
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        onBlur={() => {
                          if (newName.trim()) renameDocument(doc.id, newName.trim());
                          else setEditingDoc(null);
                        }}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && newName.trim()) {
                            renameDocument(doc.id, newName.trim());
                          }
                        }}
                        className="text-sm font-medium text-blue-600 bg-transparent border-b border-blue-300 outline-none w-full"
                        autoFocus
                      />
                    ) : (
                      <div className="text-sm font-medium text-blue-600 truncate">
                        {doc.original_filename}
                      </div>
                    )}
                    <div className="text-xs text-gray-500 mt-1">
                      {doc.file_type} • {new Date(doc.created_at).toLocaleDateString()}
                    </div>
                    {doc.is_duplicate && (
                      <div className="text-xs text-amber-600 mt-1">⚠️ Duplicate</div>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingDoc(doc.id);
                      setNewName(doc.original_filename);
                    }}
                    className="absolute bottom-1 right-1 p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Rename document"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content with left margin for fixed sidebar */}
      <div className="flex-1 flex flex-col ml-64">
        {/* Compact Navbar - Fixed */}
        <div className="bg-white p-3 fixed top-0 right-0 left-64 z-10 flex justify-between items-center border-b border-gray-200 shadow-sm">
          <div>
            <h1 className="text-base font-medium text-blue-600">ClearBill</h1>
            <p className="text-xs text-gray-600">AI-powered bill auditing and compliance verification</p>
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
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-full text-xs flex items-center space-x-1 transition-colors"
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
                <div className="text-center text-gray-500">
                  <div className="text-5xl mb-4">📄</div>
                  <p className="text-lg">Upload a document to get started</p>
                  <p className="text-sm text-gray-400 mt-2">Use the upload area at the bottom</p>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-2xl px-4 py-3 rounded-2xl shadow-lg ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white ml-auto rounded-br-md' 
                    : 'bg-white text-gray-800 mr-auto rounded-bl-md border border-gray-200'
                }`}>
                  <div className="text-[15px] leading-relaxed">
                    {typeof message.content === 'string' ? message.content : message.content}
                  </div>
                  
                  {message.data && (
                    <div className="mt-3 space-y-2">
                      <div className="text-xs opacity-75 border-t border-gray-200 pt-2">
                        <div className="mb-1">
                          <span className="font-medium">File:</span> {message.data.original_filename}
                        </div>
                        <div className="mb-1">
                          <span className="font-medium">Type:</span> {message.data.file_type}
                        </div>
                        {message.data.is_duplicate && (
                          <div className="text-amber-600 font-medium">⚠️ Duplicate detected</div>
                        )}
                      </div>
                      
                      <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                        <div className="font-medium mb-2 text-xs text-gray-600">AI Analysis:</div>
                        <div className="text-[15px] text-gray-800 leading-relaxed whitespace-pre-wrap">
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
                                    <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
                                      <div className="grid grid-cols-2 gap-2 p-3 bg-gray-100 text-xs font-medium text-gray-700">
                                        <div>ITEM</div>
                                        <div>AMOUNT</div>
                                      </div>
                                      {items.map((item, idx) => (
                                        <div key={idx} className="grid grid-cols-2 gap-2 p-3 border-t border-gray-200 text-sm">
                                          <div className="text-gray-800">{item.name}</div>
                                          <div className="text-gray-800 font-medium">${item.amount}</div>
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
                <div className="max-w-2xl px-4 py-3 rounded-2xl shadow-lg bg-white text-gray-800 mr-auto rounded-bl-md border border-gray-200">
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
          <div className="fixed bottom-0 right-0 left-64 p-3 bg-gray-50 border-t border-gray-200">
            <div 
              className={`border border-dashed rounded-lg p-5 text-center transition-colors cursor-pointer ${
                isDragOver 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-blue-500 hover:bg-gray-100'
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
              <div className="text-gray-600">
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
                      <p className="text-xs text-gray-500 mt-1">Only compliant invoices accepted</p>
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