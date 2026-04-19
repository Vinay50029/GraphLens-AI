import { useState, useRef, useCallback } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  const submit = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, onSend])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  // Auto-resize textarea
  const handleInput = (e) => {
    setValue(e.target.value)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px'
  }

  return (
    <div className="chat-input-area">
      <form
        id="chat-form"
        className="chat-input-form"
        onSubmit={(e) => { e.preventDefault(); submit() }}
        role="form"
        aria-label="Chat message input"
      >
        <textarea
          ref={textareaRef}
          id="chat-input"
          className="chat-input-field"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your documents or search the web… (Shift+Enter for new line)"
          rows={1}
          disabled={disabled}
          aria-label="Type your message"
          aria-multiline="true"
        />
        <button
          id="send-btn"
          type="submit"
          className="chat-input-send"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          title="Send (Enter)"
        >
          ➤
        </button>
      </form>
      <p className="chat-input-hint">
        Press <kbd style={{ background: 'var(--bg-elevated)', padding: '1px 5px', borderRadius: 4, fontSize: 10 }}>Enter</kbd> to send · <kbd style={{ background: 'var(--bg-elevated)', padding: '1px 5px', borderRadius: 4, fontSize: 10 }}>Shift+Enter</kbd> for new line
      </p>
    </div>
  )
}
