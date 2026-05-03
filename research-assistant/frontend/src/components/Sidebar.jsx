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
        <div className="sidebar-logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a2 2 0 0 1 2 2c-.11.88-.32 1.62-.64 2.2a2 2 0 0 0 1.25 2.87L18 10a2 2 0 1 1-1.42 3.42l-2.6-1.56a2 2 0 0 0-2.82 1.05l-1.07 1.84a2 2 0 1 1-2.92-2.14l1.37-2.38a2 2 0 0 0-1-2.73 2 2 0 0 1-1.34-3.41A2 2 0 0 1 12 2Z"/>
            <path d="M22 12a10 10 0 1 0-10 10c2.76 0 5-2.24 5-5"/>
          </svg>
        </div>
        <div className="sidebar-logo-text">
          <h1>GraphLens AI</h1>
          <span>Powered by Groq + Pinecone</span>
        </div>
      </div>

      <hr className="sidebar-divider" />

      {/* Document Upload Section */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
        <p className="sidebar-section-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          Document Management
        </p>

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
          <span className="upload-icon">
            {atLimit ? (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            ) : (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            )}
          </span>
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
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <span className="upload-count-badge">
              <span className="dot" />
              {uploadCount} / {maxUploads} PDFs ingested
            </span>
          </div>
        )}

        {/* Selected File Preview */}
        {selectedFile && (
          <div className="uploaded-file-preview">
            <span className="file-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </span>
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
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        )}

        {/* Ingest Button */}
        <button
          id="ingest-btn"
          className="btn btn--primary"
          style={{ marginTop: 16 }}
          onClick={handleIngestClick}
          disabled={!selectedFile || isIngesting || atLimit}
          aria-busy={isIngesting}
        >
          {isIngesting ? (
            <><span className="spinner" /> Processing Document…</>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Ingest to Pinecone
            </>
          )}
        </button>

        {/* Status messages */}
        {ingestStatus && (
          <div className={`status-msg status-msg--${ingestStatus.type}`} style={{ marginTop: 12 }}>
            <span>
              {ingestStatus.type === 'success' ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              )}
            </span>
            <span>{ingestStatus.text}</span>
          </div>
        )}

        {ingestedFiles?.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <p className="upload-hint" style={{ marginBottom: 0 }}>
                Active Document Context:
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ingestedFiles.map((name) => {
                const isActive = name === activeDocument
                return (
                  <button
                    key={name}
                    type="button"
                    className={`file-list-item ${isActive ? 'file-list-item--active' : ''}`}
                    onClick={() => onSelectActiveDocument?.(name)}
                    title={name}
                  >
                    <div className="file-list-item-icon">
                      {isActive ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                      ) : (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                      )}
                    </div>
                    <div className="file-list-item-content">
                      <div className="file-list-item-title">{name}</div>
                      <div className="file-list-item-status">
                        {isActive ? 'Active for Q&A' : 'Click to select'}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <hr className="sidebar-divider" />

      {/* System Info Tooltip */}
      <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'center' }}>
        <div className="tooltip-container">
          <div className="tooltip-trigger">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          </div>
          <div className="tooltip-content">
            <p style={{ fontWeight: 700, marginBottom: 12, color: 'white', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10 10 10 0 0 0-10-10Zm0 16a6 6 0 1 1 6-6 6 6 0 0 1-6 6Z"/></svg>
              System Architecture
            </p>
            <p style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--text-secondary)', marginBottom: 12 }}>
              A <strong>Supervisor Agent</strong> routes your question automatically:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2 }}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span style={{ fontSize: 12, color: 'var(--text-primary)' }}><strong>Document queries</strong><br/><span style={{ color: 'var(--text-muted)' }}>via Pinecone RAG</span></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2 }}><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                <span style={{ fontSize: 12, color: 'var(--text-primary)' }}><strong>Web queries</strong><br/><span style={{ color: 'var(--text-muted)' }}>via DuckDuckGo Search</span></span>
              </div>
            </div>
            <p style={{ marginTop: 16, fontSize: 11, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 12, color: 'var(--text-muted)' }}>
              Model: <strong style={{ color: 'var(--text-secondary)' }}>llama3-70b-8192</strong> via Groq
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}
