import React, { useState } from 'react';
import './App.css';
import ReactMarkdown from 'react-markdown';
import { Mic } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';


function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Welcome to Inventory checker bot! Ask your question below.',
      timestamp: new Date().toISOString()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [showMenu, setShowMenu] = useState(false);

  

  const downloadChatAsPDF = () => {
    const doc = new jsPDF();
    const tableData = messages.map((msg) => [
      msg.sender === 'bot' ? 'Bot' : 'User',
      new Date(msg.timestamp).toLocaleDateString(),
      new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      msg.text
    ]);
  
    autoTable(doc, {
      head: [['Name', 'Date', 'Time', 'Message']],
      body: tableData,
      startY: 20,
      styles: {
        cellPadding: 2,
        fontSize: 10,
        overflow: 'linebreak'
      },
      headStyles: {
        fillColor: [60, 179, 113] 
      },
      theme: 'grid',
      pageBreak: 'auto',
    });
  
    doc.save('chat_history.pdf');
    setShowMenu(false);
  };
  

  const sendMessage = async (message = input) => {
    if (!message.trim()) return;
  
    const now = new Date().toISOString();
  
    const userMessage = { sender: 'user', text: message, timestamp: now };
    setMessages(prev => [...prev, userMessage]);
  
    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: message })
      });
  
      const data = await res.json();
      const botReply = {
        sender: 'bot',
        text: data.response || data.error || 'No response',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, botReply]);
    } catch (error) {
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Error contacting the server.',
        timestamp: new Date().toISOString()
      }]);
    }
  
    setInput('');
    setShowSuggestions(false);
  };

  const clearChat = () => {
    setMessages([{ sender: 'bot', text: 'Welcome to Inventory checker bot! Ask your question below.',timestamp: new Date() }]);
    setShowSuggestions(true);
  };

  const startVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Your browser does not support Speech Recognition.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.start();
    setIsListening(true);

    let finalTranscript = '';

    recognition.onresult = (event) => {
      finalTranscript = event.results[0][0].transcript;
      setInput(finalTranscript); 
    };

    recognition.onend = () => {
      setIsListening(false);
      if (finalTranscript.trim()) {
        sendMessage(finalTranscript);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };
  };

  const handleSuggestionClick = (text) => {
    sendMessage(text);
    setShowSuggestions(false);
  };
  

  return (
    <div className="App">
      <div className="chat-header">
      <div className="chat-title">Inventory Checker Bot</div>
      <div className="menu-button" onClick={() => setShowMenu(prev => !prev)}>⋮</div>
      {showMenu && (
        <div className="menu-dropdown">
        <button onClick={downloadChatAsPDF}>Download Chat</button>
        </div>
      )}
    </div>


      <div className="chat-box">
  {messages.map((msg, i) => (
    <React.Fragment key={i}>
      <div className={msg.sender === 'user' ? 'user-msg' : 'bot-msg'}>
        <div className="markdown">
          <ReactMarkdown>{msg.text}</ReactMarkdown>
        </div>
        <div className="timestamp">
          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>

      { i === 0 && showSuggestions && (
  <div className="user-msg suggestion-bubble">
    <div className="markdown suggestion-label">Need help? Start with</div>
    <div className="suggestion-buttons">
      {[
        "How many units of <strong>P103P15</strong> are currently available?",
        "What is the current quantity available for the <strong>HPC stator variable vane</strong>?",
        "Can you provide a list of parts available in location <strong>C01-19</strong>?"
      ].map((suggestion, idx) => (
        <button
          key={idx}
          className="suggestion-btn"
          onClick={() => handleSuggestionClick(suggestion.replace(/<[^>]+>/g, ''))} // Removes <strong> for backend input
          dangerouslySetInnerHTML={{ __html: suggestion }}
        />
      ))}
    </div>
  </div>
)}


    </React.Fragment>
  ))}
</div>



      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask your inventory question..."
        />
        <button onClick={() => sendMessage()}>Send</button>
        <button onClick={clearChat} style={{ marginLeft: '10px', backgroundColor: '#f44336' }}>
          Clear Chat
        </button>
        <button
            onClick={startVoiceInput}
            className={`voice-button ${isListening ? 'listening' : ''}`}
            style={{ marginLeft: '10px' }}
          >
            <Mic size={20} color="#fff" />
          </button>
      </div>
    </div>
  );
}

export default App;
