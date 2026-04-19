import { useEffect, useRef } from 'react'

const SUGGESTIONS = [
  '📄 Summarize my document',
  '🌐 What is happening in AI today?',
  '🔍 Search for recent research on LLMs',
  '📊 What are the key findings in the paper?',
]

export default function ChatWindow({ messages, isLoading, onSuggestion }) {
  const bottomRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="chat-window">
        <div className="chat-empty">
          <span className="chat-empty-icon">🤖</span>
          <h3>Ready to Research</h3>
          <p>
            Upload a PDF and ask questions about it, or ask any web question.
            The AI Supervisor will route your query automatically.
          </p>
          <div className="chat-empty-suggestions">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                id={`suggestion-${s.replace(/\W+/g, '-').toLowerCase()}`}
                className="chat-suggestion-chip"
                onClick={() => onSuggestion(s.replace(/^[^\w]+/, '').trim())}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-window" role="log" aria-live="polite" aria-label="Chat messages">
      {messages.map((msg, i) => (
        <MessageBubble key={i} message={msg} />
      ))}

      {isLoading && <TypingIndicator />}

      <div ref={bottomRef} aria-hidden="true" />
    </div>
  )
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`message message--${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-bubble">
        <p>{message.content}</p>
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="message-avatar" style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        width: 34, height: 34,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 16,
        flexShrink: 0,
      }}>
        🤖
      </div>
      <div className="typing-bubble">
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 6 }}>Thinking</span>
        <span className="typing-dots">
          <span /><span /><span />
        </span>
      </div>
    </div>
  )
}
