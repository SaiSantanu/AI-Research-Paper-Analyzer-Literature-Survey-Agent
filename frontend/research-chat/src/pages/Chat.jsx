import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

// -- API -----------------------------------------------------------------------
async function apiResearch(topic) {
  const res = await fetch('/api/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Server error ' + res.status)
  return data
}

async function apiAsk(topic, question, history) {
  const res = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, question, history }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Server error ' + res.status)
  return data
}

function downloadUrl(type, topic) {
  return '/api/export/' + type + '?topic=' + encodeURIComponent(topic)
}

// -- Detect if input is a follow-up question or new research topic -------------
function isFollowUpQuestion(input, currentTopic, hasReport) {
  if (!currentTopic) return false
  const q = input.toLowerCase().trim()

  // KEY RULE: once a report exists, default to follow-up
  // UNLESS the input looks like a brand new research topic
  if (hasReport) {
    const hasQuestionMark = input.includes('?')
    const questionStarters = [
      'what', 'which', 'how', 'why', 'who', 'where', 'when',
      'tell', 'explain', 'describe', 'summarize', 'compare',
      'list', 'show', 'give', 'find', 'can you', 'could you',
      'is ', 'are ', 'did ', 'does ', 'do ',
    ]
    const hasQuestionWord = questionStarters.some(w => q.startsWith(w))
    const refWords = [
      'paper', 'papers', 'study', 'studies', 'review', 'literature',
      'result', 'method', 'author', 'find', 'show', 'mention',
      'discuss', 'used', 'you', 'this', 'these', 'those', 'above', 'said',
    ]
    const hasRefWord = refWords.some(w => q.includes(w))

    // Has question indicators -> follow-up
    if (hasQuestionMark || hasQuestionWord || hasRefWord) return true

    // Short phrase with no question indicators -> likely new topic
    // e.g. 'Federated Learning' or 'Vision Transformers'
    if (input.split(' ').length <= 5 && !hasQuestionMark) return false

    // Default: treat as follow-up when report exists
    return true
  }

  // No report yet - basic detection only
  const followUpStarters = [
    'what', 'which', 'how', 'why', 'who', 'tell',
    'explain', 'describe', 'summarize', 'compare', 'list', 'show',
  ]
  const firstWord = q.split(' ')[0]
  if (followUpStarters.includes(firstWord)) return true
  const topicWords = currentTopic.toLowerCase().split(' ').filter(w => w.length > 3)
  if (topicWords.some(w => q.includes(w))) return true
  return false
}

// -- Sub-components ------------------------------------------------------------

function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: 5, alignItems: 'center', padding: '4px 0' }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: 'var(--text-3)', display: 'inline-block',
          animation: 'pulse 1.2s ' + (i * 0.2) + 's infinite',
        }} />
      ))}
    </div>
  )
}

function AgentProgress({ steps, currentStep }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', padding: '16px 20px', marginBottom: 4,
    }}>
      <div style={{
        fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-3)',
        letterSpacing: '0.06em', textTransform: 'uppercase',
        marginBottom: 14, fontFamily: 'var(--font-mono)',
      }}>
        Pipeline Progress
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {steps.map((step, i) => {
          const isDone   = i < currentStep
          const isActive = i === currentStep
          return (
            <div key={step.key} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '8px 12px',
              background: isActive ? 'var(--accent-light)' : isDone ? 'var(--green-bg)' : 'transparent',
              border: '1px solid ' + (isActive ? '#c8e8e2' : isDone ? '#c3e9d5' : 'transparent'),
              borderRadius: 'var(--radius-sm)',
              transition: 'all 0.3s ease',
              opacity: (!isDone && !isActive) ? 0.5 : 1,
            }}>
              <div style={{ flexShrink: 0, width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {isDone ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : isActive ? (
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)', animation: 'pulse 1.2s infinite' }} />
                ) : (
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--border2)' }} />
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.84rem', fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--accent-dark)' : isDone ? 'var(--green)' : 'var(--text-2)' }}>
                  {step.label}
                </div>
                {isActive && <div style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginTop: 1 }}>{step.desc}</div>}
              </div>
              {isDone && <span style={{ fontSize: '0.72rem', color: 'var(--green)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>done</span>}
              {isActive && <TypingDots />}
            </div>
          )
        })}
      </div>
      <div style={{ marginTop: 14, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: Math.min((currentStep / steps.length) * 100, 100) + '%',
          background: 'linear-gradient(90deg, var(--accent), var(--accent-mid))',
          borderRadius: 2, transition: 'width 0.6s ease',
        }} />
      </div>
    </div>
  )
}

function ReportMessage({ report, topic, score, paperCount, revisionCount }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {[
          { label: 'Papers', val: paperCount },
          { label: 'Score', val: score + '/10', color: score >= 7 ? 'var(--green)' : 'var(--amber)' },
          { label: 'Revisions', val: revisionCount },
        ].map(s => (
          <div key={s.label} style={{
            background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)', padding: '6px 14px', fontSize: '0.78rem',
          }}>
            <span style={{ color: 'var(--text-3)' }}>{s.label}: </span>
            <span style={{ fontWeight: 600, color: s.color || 'var(--text)', fontFamily: 'var(--font-mono)' }}>{s.val}</span>
          </div>
        ))}
      </div>

      <div style={{
        background: 'var(--bg2)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: '20px 24px',
        fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
        lineHeight: 1.8, color: 'var(--text-2)', whiteSpace: 'pre-wrap',
        maxHeight: 420, overflowY: 'auto',
      }}>
        {report}
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <a href={downloadUrl('pdf', topic)} download style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'var(--accent)', color: 'white', border: 'none',
          borderRadius: 'var(--radius-sm)', padding: '9px 18px',
          fontSize: '0.85rem', fontWeight: 500, textDecoration: 'none', transition: 'background 0.15s',
        }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--accent-dark)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--accent)'}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download PDF
        </a>
        <a href={downloadUrl('md', topic)} download style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'var(--surface)', color: 'var(--text)',
          border: '1.5px solid var(--border2)', borderRadius: 'var(--radius-sm)',
          padding: '9px 18px', fontSize: '0.85rem', fontWeight: 500,
          textDecoration: 'none', transition: 'border-color 0.15s',
        }}
          onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
          onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border2)'}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
          </svg>
          Download Markdown
        </a>
      </div>
    </div>
  )
}

// -- Answer bubble (follow-up response) ----------------------------------------
function AnswerMessage({ answer, papersUsed }) {
  // Convert **bold** markdown to styled spans
  const formatAnswer = (text) => {
    return text.split('\n').map((line, i) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <div key={i} style={{ fontWeight: 700, color: 'var(--text)', marginTop: i > 0 ? 10 : 0, marginBottom: 4 }}>
            {line.replace(/\*\*/g, '')}
          </div>
        )
      }
      if (line.startsWith('- ')) {
        return (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
            <span style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 1 }}>•</span>
            <span style={{ color: 'var(--text-2)', lineHeight: 1.6 }}>{line.slice(2)}</span>
          </div>
        )
      }
      if (!line.trim()) return <div key={i} style={{ height: 6 }} />
      return <div key={i} style={{ color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 2 }}>{line}</div>
    })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{
        background: 'var(--bg2)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: '16px 20px',
        fontSize: '0.88rem',
      }}>
        {formatAnswer(answer)}
      </div>
      {papersUsed && papersUsed.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>Sources:</span>
          {papersUsed.map((p, i) => (
            <span key={i} style={{
              background: 'var(--accent-light)', color: 'var(--accent)',
              border: '1px solid #c8e8e2', borderRadius: 20,
              padding: '2px 10px', fontSize: '0.72rem',
            }}>
              {p.length > 40 ? p.slice(0, 40) + '...' : p}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// -- Message bubble ------------------------------------------------------------
function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{
      display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 20, animation: 'slideIn 0.3s ease both',
      gap: 12, alignItems: 'flex-start',
    }}>
      {!isUser && (
        <div style={{
          width: 34, height: 34, borderRadius: 10, flexShrink: 0,
          background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 2,
        }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
          </svg>
        </div>
      )}

      <div style={{ maxWidth: isUser ? '65%' : '82%', minWidth: 0 }}>
        <div style={{
          fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 500,
          marginBottom: 5, textAlign: isUser ? 'right' : 'left', letterSpacing: '0.03em',
        }}>
          {isUser ? 'You' : 'ScholarAI'}
        </div>
        <div style={{
          background: isUser ? 'var(--accent)' : 'var(--surface)',
          color: isUser ? 'white' : 'var(--text)',
          border: isUser ? 'none' : '1px solid var(--border)',
          borderRadius: isUser ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
          padding: (msg.type === 'report' || msg.type === 'answer') ? '16px 18px' : '12px 16px',
          boxShadow: 'var(--shadow-sm)',
          fontSize: '0.9rem', lineHeight: 1.65,
        }}>
          {msg.type === 'progress' && <AgentProgress steps={msg.steps} currentStep={msg.currentStep} />}
          {msg.type === 'report'   && <ReportMessage {...msg} />}
          {msg.type === 'answer'   && <AnswerMessage answer={msg.answer} papersUsed={msg.papersUsed} />}
          {msg.type === 'typing'   && <TypingDots />}
          {msg.type === 'error'    && (
            <div style={{ color: 'var(--red)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              {msg.content}
            </div>
          )}
          {(msg.type === 'text' || !msg.type) && msg.content}
        </div>
      </div>

      {isUser && (
        <div style={{
          width: 34, height: 34, borderRadius: 10, flexShrink: 0,
          background: 'var(--bg3)', border: '1.5px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 2,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-2)" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      )}
    </div>
  )
}

// -- Pipeline steps ------------------------------------------------------------
const PIPELINE_STEPS = [
  { key: 'planner',     label: 'Planner',       desc: 'Decomposing query into research tasks...' },
  { key: 'searcher',    label: 'Searcher',       desc: 'Fetching relevant papers from arXiv...' },
  { key: 'reader',      label: 'Reader',         desc: 'Downloading and parsing PDFs...' },
  { key: 'vectorstore', label: 'Vector Store',   desc: 'Chunking and embedding paper text...' },
  { key: 'rag',         label: 'RAG Extraction', desc: 'Extracting methodology and results...' },
  { key: 'synthesizer', label: 'Synthesizer',    desc: 'Compiling structured literature review...' },
  { key: 'reviewer',    label: 'Reviewer',       desc: 'Evaluating report quality...' },
]

const SUGGESTIONS = [
  'AI in Healthcare', 'Vision Transformers',
  'Federated Learning', 'Diffusion Models',
]

const FOLLOW_UP_SUGGESTIONS = [
  'What accuracy did the models achieve?',
  'What datasets were used?',
  'What are the main limitations?',
  'Compare the methodologies',
  'What are the future research directions?',
]

// -- Main Chat -----------------------------------------------------------------
export default function Chat() {
  const navigate = useNavigate()
  const [messages, setMessages]       = useState([{
    id: 1, role: 'assistant', type: 'text',
    content: 'Hello! I am ScholarAI. Type a research topic to generate a literature review, or ask me questions about the papers after the review is ready.',
  }])
  const [input, setInput]             = useState('')
  const [loading, setLoading]         = useState(false)
  const [currentTopic, setCurrentTopic] = useState('')   // track active research topic
  const [hasReport, setHasReport]     = useState(false)  // show follow-up suggestions
  const [chatHistory, setChatHistory] = useState([])     // for context
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = useCallback((msg) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), ...msg }])
  }, [])

  // -- Handle research pipeline ------------------------------------------------
  async function runResearch(topic) {
    setLoading(true)
    setCurrentTopic(topic)

    const progressId = Date.now()
    setMessages(prev => [...prev, {
      id: progressId, role: 'assistant', type: 'progress',
      steps: PIPELINE_STEPS, currentStep: 0,
    }])

    let stepIdx = 0
    const stepInterval = setInterval(() => {
      stepIdx++
      if (stepIdx < PIPELINE_STEPS.length) {
        setMessages(prev => prev.map(m =>
          m.id === progressId ? { ...m, currentStep: stepIdx } : m
        ))
      }
    }, 1600)

    try {
      const data = await apiResearch(topic)
      clearInterval(stepInterval)
      setMessages(prev => prev.map(m =>
        m.id === progressId ? { ...m, currentStep: PIPELINE_STEPS.length } : m
      ))
      await new Promise(r => setTimeout(r, 400))

      if (!data.report && data.paperCount === 0) {
        addMessage({ role: 'assistant', type: 'text', content: 'No relevant papers found for "' + topic + '". Try a more specific topic.' })
      } else {
        addMessage({
          role: 'assistant', type: 'report',
          report: data.report, topic,
          score: data.reviewScore,
          paperCount: data.paperCount,
          revisionCount: data.revisionCount,
        })
        addMessage({
          role: 'assistant', type: 'text',
          content: 'Review complete! You can download the PDF or Markdown above. Feel free to ask me any questions about these papers.',
        })
        setHasReport(true)
        setChatHistory(prev => [...prev,
          { role: 'user', content: topic },
          { role: 'assistant', content: 'Literature review generated for: ' + topic },
        ])
      }
    } catch (err) {
      clearInterval(stepInterval)
      setMessages(prev => prev.filter(m => m.id !== progressId))
      addMessage({ role: 'assistant', type: 'error', content: err.message })
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  // -- Handle follow-up question -----------------------------------------------
  async function runAsk(question) {
    setLoading(true)

    // Show typing indicator
    const typingId = Date.now()
    setMessages(prev => [...prev, { id: typingId, role: 'assistant', type: 'typing' }])

    try {
      const data = await apiAsk(currentTopic, question, chatHistory)

      setMessages(prev => prev.filter(m => m.id !== typingId))

      addMessage({
        role: 'assistant', type: 'answer',
        answer: data.answer,
        papersUsed: data.papersUsed || [],
      })

      // Update chat history
      setChatHistory(prev => [...prev,
        { role: 'user', content: question },
        { role: 'assistant', content: data.answer },
      ])
    } catch (err) {
      setMessages(prev => prev.filter(m => m.id !== typingId))
      addMessage({ role: 'assistant', type: 'error', content: err.message })
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  // -- Handle send --------------------------------------------------------------
  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')

    addMessage({ role: 'user', type: 'text', content: text })

    if (isFollowUpQuestion(text, currentTopic, hasReport)) {
      await runAsk(text)
    } else {
      await runResearch(text)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  // -- Render ------------------------------------------------------------------
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>

      {/* Header */}
      <header style={{
        height: 60, borderBottom: '1px solid var(--border)',
        background: 'var(--surface)', display: 'flex', alignItems: 'center',
        padding: '0 24px', gap: 16, flexShrink: 0, boxShadow: 'var(--shadow-sm)',
      }}>
        <button onClick={() => navigate('/')} style={{
          background: 'none', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)', padding: '6px 12px',
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: '0.82rem', color: 'var(--text-2)', transition: 'all 0.15s',
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--accent)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)' }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
          Home
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', fontFamily: 'var(--font-display)' }}>ScholarAI</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-3)' }}>
              {currentTopic ? 'Topic: ' + currentTopic : 'Research Paper Analyzer'}
            </div>
          </div>
        </div>

        {/* Mode indicator */}
        {hasReport && (
          <div style={{
            marginLeft: 'auto',
            background: 'var(--accent-light)', color: 'var(--accent)',
            border: '1px solid #c8e8e2', borderRadius: 20,
            padding: '4px 12px', fontSize: '0.75rem', fontWeight: 500,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
            Ask me anything about the papers
          </div>
        )}

        <div style={{ marginLeft: hasReport ? 12 : 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: loading ? 'var(--amber)' : 'var(--green)',
            display: 'inline-block',
            animation: loading ? 'pulse 1s infinite' : 'none',
          }} />
          <span style={{ fontSize: '0.78rem', color: 'var(--text-3)' }}>
            {loading ? (isFollowUpQuestion(input, currentTopic, hasReport) ? 'Thinking...' : 'Analyzing...') : 'Ready'}
          </span>
        </div>
      </header>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ maxWidth: 800, margin: '0 auto', width: '100%', flex: 1 }}>
          {messages.map(msg => <Message key={msg.id} msg={msg} />)}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Suggestion chips */}
      {!loading && (
        <div style={{
          padding: '0 24px 12px', display: 'flex', gap: 8, flexWrap: 'wrap',
          maxWidth: 848, margin: '0 auto', width: '100%',
        }}>
          {(hasReport ? FOLLOW_UP_SUGGESTIONS : SUGGESTIONS).slice(0, 4).map(s => (
            <button key={s} onClick={() => { setInput(s); inputRef.current?.focus() }} style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 20, padding: '5px 14px', fontSize: '0.78rem',
              color: 'var(--text-2)', transition: 'all 0.15s',
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--accent)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)' }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div style={{ borderTop: '1px solid var(--border)', background: 'var(--surface)', padding: '16px 24px', flexShrink: 0 }}>
        <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
              placeholder={
                loading ? 'Please wait...' :
                hasReport ? 'Ask a question about the papers, or type a new topic...' :
                'Type a research topic (e.g. AI in Healthcare)'
              }
              rows={1}
              style={{
                width: '100%', background: 'var(--bg)',
                border: '1.5px solid var(--border2)', borderRadius: 'var(--radius)',
                padding: '12px 16px', fontSize: '0.92rem', color: 'var(--text)',
                outline: 'none', resize: 'none', fontFamily: 'var(--font-body)',
                lineHeight: 1.5, transition: 'border-color 0.15s',
                opacity: loading ? 0.6 : 1,
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e  => e.target.style.borderColor = 'var(--border2)'}
            />
          </div>
          <button onClick={handleSend} disabled={loading || !input.trim()} style={{
            width: 46, height: 46, borderRadius: 'var(--radius)',
            background: loading || !input.trim() ? 'var(--bg3)' : 'var(--accent)',
            color: loading || !input.trim() ? 'var(--text-3)' : 'white',
            border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, transition: 'all 0.15s',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
          }}>
            {loading ? (
              <div style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid var(--border)', borderTopColor: 'var(--accent)', animation: 'spin 0.8s linear infinite' }} />
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
        <p style={{ textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-3)', marginTop: 10, fontFamily: 'var(--font-mono)' }}>
          {hasReport
            ? 'Ask questions about the papers | Type a new topic to start fresh'
            : 'Press Enter to send | Shift+Enter for new line | Results take 60-120 seconds'}
        </p>
      </div>
    </div>
  )
}