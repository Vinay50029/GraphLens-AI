import { useState, useRef, useCallback } from 'react'

const MAX_SIZE_MB = 200

export default function Sidebar({
  uploadCount,
  maxUploads,
  onIngest,
  isIngesting,
  ingestStatus,
  onClearStatus,
  ingestedFiles = [],
  activeDocument = '',
  onSelectActiveDocument,
}) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  const atLimit = uploadCount >= maxUploads

  const validateAndSet = useCallback((file) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Only PDF files are supported.')
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      alert(`File is too large. Maximum is ${MAX_SIZE_MB} MB.`)
      return
    }
    setSelectedFile(file)
    onClearStatus() // reset any previous status message
  }, [onClearStatus])

  // Drag handlers
  const handleDrag = (e) => { e.preventDefault(); e.stopPropagation() }
  const handleDragIn = (e) => { e.preventDefault(); e.stopPropagation(); if (!atLimit) setDragActive(true) }
  const handleDragOut = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(false) }
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation()
    setDragActive(false)
    if (atLimit) return
    const file = e.dataTransfer?.files?.[0]
    validateAndSet(file)
  }

  // File input change
  const handleFileChange = (e) => {
    validateAndSet(e.target.files?.[0])
    e.target.value = '' // reset so same file can be re-selected
  }

  // Ingest
  const handleIngestClick = async () => {
    if (!selectedFile || isIngesting) return
    await onIngest(selectedFile)
    setSelectedFile(null)
  }

  const removeFile = () => {
    setSelectedFile(null)
    onClearStatus()
  }

  const fileSizeMB = selectedFile ? (selectedFile.size / (1024 * 1024)).toFixed(1) : null

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🤖</div>
        <div className="sidebar-logo-text">
          <h1>Intelligent Research Assistant</h1>
          <span>Powered by Groq + Pinecone</span>
        </div>
      </div>

      <hr className="sidebar-divider" />

      {/* Document Upload Section */}
      <div>
        <p className="sidebar-section-title">📄 Document Management</p>

        {/* Drop Zone */}
        <div
          id="upload-dropzone"
          className={[
            'upload-zone',
            dragActive ? 'upload-zone--active' : '',
            atLimit ? 'upload-zone--disabled' : '',
          ].join(' ')}
          onDragEnter={handleDragIn}
          onDragLeave={handleDragOut}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !atLimit && inputRef.current?.click()}
          role="button"
          aria-label="Upload PDF"
          tabIndex={atLimit ? -1 : 0}
          onKeyDown={(e) => e.key === 'Enter' && !atLimit && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            id="pdf-file-input"
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={atLimit}
            style={{ display: 'none' }}
          />
          <span className="upload-icon">{atLimit ? '🔒' : '☁️'}</span>
          {atLimit ? (
            <p>Upload limit reached<br /><span className="upload-hint">({maxUploads}/{maxUploads} PDFs ingested)</span></p>
          ) : (
            <>
              <p><strong>Drop a PDF here</strong><br />or click to browse</p>
              <p className="upload-hint">Max {MAX_SIZE_MB} MB · PDF only</p>
            </>
          )}
        </div>

        {/* Upload Counter */}
        {!atLimit && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
            <span className="upload-count-badge">
              <span className="dot" />
              {uploadCount} / {maxUploads} PDFs ingested
            </span>
          </div>
        )}

        {/* Selected File Preview */}
        {selectedFile && (
          <div className="uploaded-file-preview">
            <span className="file-icon">📄</span>
            <div className="file-info">
              <div className="file-name" title={selectedFile.name}>{selectedFile.name}</div>
              <div className="file-size">{fileSizeMB} MB</div>
            </div>
            <button
              id="remove-file-btn"
              className="file-remove"
              onClick={removeFile}
              title="Remove file"
              aria-label="Remove file"
            >
              ✕
            </button>
          </div>
        )}

        {/* Ingest Button */}
        <button
          id="ingest-btn"
          className="btn btn--primary"
          style={{ marginTop: 12 }}
          onClick={handleIngestClick}
          disabled={!selectedFile || isIngesting || atLimit}
          aria-busy={isIngesting}
        >
          {isIngesting ? (
            <><span className="spinner" /> Processing into Pinecone…</>
          ) : (
            <>⚡ Ingest Document</>
          )}
        </button>

        {/* Status messages */}
        {ingestStatus && (
          <div className={`status-msg status-msg--${ingestStatus.type}`} style={{ marginTop: 10 }}>
            <span>
              {ingestStatus.type === 'success' ? '✅' : '❌'}
            </span>
            <span>{ingestStatus.text}</span>
          </div>
        )}

        {ingestedFiles?.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <p className="upload-hint" style={{ marginBottom: 8 }}>
              Active PDF (used for document Q&amp;A):
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ingestedFiles.map((name) => {
                const isActive = name === activeDocument
                return (
                  <button
                    key={name}
                    type="button"
                    className="btn"
                    onClick={() => onSelectActiveDocument?.(name)}
                    style={{
                      textAlign: 'left',
                      border: isActive ? '1px solid rgba(139, 92, 246, 0.65)' : '1px solid var(--border-subtle)',
                      background: isActive ? 'rgba(139, 92, 246, 0.12)' : 'var(--bg-elevated)',
                      color: 'var(--text)',
                      padding: '10px 12px',
                      borderRadius: 10,
                      cursor: 'pointer',
                    }}
                    title={name}
                  >
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {isActive ? 'Selected' : 'Select'}
                    </div>
                    <div style={{ fontWeight: 600, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {name}
                    </div>
                  </button>
                )
              })}
            </div>
            <p className="upload-hint" style={{ marginTop: 8 }}>
              Tip: if your question is about a different uploaded PDF than the selected one, either select that PDF or ask using its filename (e.g. <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace' }}>MyNotes.pdf</span>).
            </p>
          </div>
        )}
      </div>

      <hr className="sidebar-divider" />

      {/* How it works note */}
      <div>
        <p className="sidebar-section-title">🧠 How It Works</p>
        <div className="sidebar-ai-badge">
          <p>
            A <strong>Supervisor Agent</strong> routes your question automatically:
          </p>
          <p style={{ marginTop: 8 }}>
            📄 <strong>Document questions</strong> → Pinecone RAG search<br />
            🌐 <strong>Web questions</strong> → DuckDuckGo + scraper
          </p>
          <p style={{ marginTop: 8, fontSize: 10 }}>
            Model: <strong>llama3-70b-8192</strong> via Groq
          </p>
        </div>
      </div>
    </aside>
  )
}
