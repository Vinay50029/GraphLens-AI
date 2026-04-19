import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatWindow from './components/ChatWindow.jsx'
import ChatInput from './components/ChatInput.jsx'

const MAX_UPLOADS = 20

async function readResponseBody(response) {
  const rawText = await response.text()
  if (!rawText) return {}

  try {
    return JSON.parse(rawText)
  } catch {
    return { error: rawText }
  }
}

export default function App() {
  // ─── State ─────────────────────────────────────────────────────────────────
  const [messages, setMessages]       = useState([])         // { role, content }[]
  const [isLoading, setIsLoading]     = useState(false)      // waiting for AI
  const [isIngesting, setIsIngesting] = useState(false)      // uploading PDF
  const [uploadCount, setUploadCount] = useState(0)          // how many PDFs ingested
  const [ingestStatus, setIngestStatus] = useState(null)     // { type, text }
  const [activeDocument, setActiveDocument] = useState('')   // selected PDF for RAG filtering
  const [ingestedFiles, setIngestedFiles] = useState([])     // string[] (unique filenames)

  // ─── Send a chat message ────────────────────────────────────────────────────
  const handleSend = useCallback(async (text) => {
    if (isLoading || !text.trim()) return

    const userMsg = { role: 'user', content: text.trim() }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setIsLoading(true)

    const apiBase = import.meta.env.VITE_API_URL || ''
    try {
      const response = await fetch(`${apiBase}/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: updatedMessages, active_document: activeDocument }),
      })
      const data = await readResponseBody(response)

      if (!response.ok) {
        throw new Error(data.error || data.message || `Server error (${response.status})`)
      }

      setMessages(prev => [...prev, { role: 'assistant', content: data.content }])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `⚠️ Error: ${err.message}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [messages, isLoading, activeDocument])

  // ─── Ingest a PDF ──────────────────────────────────────────────────────────
  const handleIngest = useCallback(async (file) => {
    if (!file || isIngesting) return

    setIsIngesting(true)
    setIngestStatus(null)

    const formData = new FormData()
    formData.append('file', file)

    const apiBase = import.meta.env.VITE_API_URL || ''
    try {
      const response = await fetch(`${apiBase}/api/ingest/`, {
        method: 'POST',
        body: formData,
      })
      const data = await readResponseBody(response)

      if (response.ok && data.success) {
        setIngestStatus({ type: 'success', text: data.message })
        const name = data.file_name || file.name
        setIngestedFiles((prev) => {
          if (prev.includes(name)) return prev
          setUploadCount((c) => c + 1)
          return [...prev, name]
        })
        setActiveDocument(name)
      } else {
        setIngestStatus({ type: 'error', text: data.error || data.message || 'Ingestion failed.' })
      }
    } catch (err) {
      setIngestStatus({ type: 'error', text: `Network error: ${err.message}` })
    } finally {
      setIsIngesting(false)
    }
  }, [isIngesting])

  // ─── Handle suggestion chip clicks ─────────────────────────────────────────
  const handleSuggestion = useCallback((text) => {
    handleSend(text)
  }, [handleSend])

  // ─── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="app-layout">
      <Sidebar
        uploadCount={uploadCount}
        maxUploads={MAX_UPLOADS}
        onIngest={handleIngest}
        isIngesting={isIngesting}
        ingestStatus={ingestStatus}
        onClearStatus={() => setIngestStatus(null)}
        ingestedFiles={ingestedFiles}
        activeDocument={activeDocument}
        onSelectActiveDocument={setActiveDocument}
      />

      <div className="chat-area">
        <header className="chat-header">
          <div>
            <h2>Research Chat</h2>
            <p>Ask about your documents or search the web — the AI routes automatically</p>
          </div>
          <div className="chat-header-badge">
            <span className="live-dot" />
            Groq · llama3-70b
          </div>
        </header>

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSuggestion={handleSuggestion}
        />

        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
        />
      </div>
    </div>
  )
}
