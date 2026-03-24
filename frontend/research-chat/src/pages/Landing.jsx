import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'


const TOPICS = [
  'AI in Healthcare',
  'Vision Transformers',
  'Federated Learning',
  'Large Language Models',
  'Diffusion Models',
  'Reinforcement Learning',
]

const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    ),
    title: 'arXiv Search',
    desc: 'Automatically fetches relevant papers from arXiv based on your topic',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
    ),
    title: 'RAG Extraction',
    desc: 'Extracts methodology, results and limitations from each paper',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    title: 'LangGraph Pipeline',
    desc: 'Multi-agent system with Reviewer/Reviser quality control loop',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
    ),
    title: 'Export Ready',
    desc: 'Download your literature review as PDF or Markdown instantly',
  },
]

const STEPS = [
  { num: '01', title: 'Enter your topic',   desc: 'Type any research subject into the chat' },
  { num: '02', title: 'Watch agents work',  desc: 'See each AI agent run in real time' },
  { num: '03', title: 'Get your review',    desc: 'Receive a structured literature survey' },
  { num: '04', title: 'Download it',        desc: 'Export as PDF or Markdown in one click' },
]

export default function Landing() {
  const navigate = useNavigate()
  const [topicIdx, setTopicIdx] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setTopicIdx(i => (i + 1) % TOPICS.length), 2400)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>

      {/* ---- Nav ---- */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(250,250,248,0.92)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--border)',
        padding: '0 40px',
        height: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>
          <span style={{
            fontFamily: 'var(--font-display)', fontWeight: 700,
            fontSize: '1.25rem', color: 'var(--text)', letterSpacing: '-0.3px',
          }}>ScholarAI</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a href="#features" style={{
            fontSize: '0.875rem', color: 'var(--text-2)',
            padding: '6px 14px', borderRadius: 'var(--radius-sm)',
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => e.target.style.color = 'var(--accent)'}
          onMouseLeave={e => e.target.style.color = 'var(--text-2)'}
          >Features</a>
          <a href="#how" style={{
            fontSize: '0.875rem', color: 'var(--text-2)',
            padding: '6px 14px', borderRadius: 'var(--radius-sm)',
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => e.target.style.color = 'var(--accent)'}
          onMouseLeave={e => e.target.style.color = 'var(--text-2)'}
          >How it works</a>
          <button
            onClick={() => navigate('/chat')}
            style={{
              background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: 'var(--radius-sm)',
              padding: '8px 20px', fontSize: '0.875rem', fontWeight: 500,
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.target.style.background = 'var(--accent-dark)'}
            onMouseLeave={e => e.target.style.background = 'var(--accent)'}
          >
            Open Chat
          </button>
        </div>
      </nav>

      {/* ---- Hero ---- */}
      <section style={{
        maxWidth: 1100, margin: '0 auto',
        padding: '67px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80,
        alignItems: 'center',
      }}>
        {/* Left */}
        <div style={{ animation: 'fadeUp 0.6s ease both' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'var(--accent-light)', color: 'var(--accent)',
            border: '1px solid #c8e8e2',
            borderRadius: 20, padding: '5px 14px',
            fontSize: '0.78rem', fontWeight: 500, letterSpacing: '0.03em',
            marginBottom: 28,
          }}>
            <span style={{
              width: 7, height: 7, borderRadius: '50%',
              background: 'var(--accent)', display: 'inline-block',
            }}/>
            Powered by LangGraph + arXiv
          </div>

          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(2.4rem, 4vw, 3.6rem)',
            fontWeight: 700, lineHeight: 1.1,
            color: 'var(--text)', letterSpacing: '-1px',
            marginBottom: 24,
          }}>
            Research smarter,<br />
            <span style={{ color: 'var(--accent)', fontStyle: 'italic' }}>
              not harder.
            </span>
          </h1>

          <p style={{
            fontSize: '1.05rem', color: 'var(--text-2)',
            lineHeight: 1.7, marginBottom: 40, maxWidth: 440,
          }}>
            Turn any research topic into a structured literature review in minutes.
            Our AI agents search arXiv, extract insights, and compile a publication-ready survey.
          </p>

          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate('/chat')}
              style={{
                background: 'var(--accent)', color: 'white',
                border: 'none', borderRadius: 'var(--radius)',
                padding: '14px 32px', fontSize: '1rem', fontWeight: 600,
                display: 'flex', alignItems: 'center', gap: 10,
                boxShadow: '0 4px 16px rgba(26,107,90,0.3)',
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'var(--accent-dark)'
                e.currentTarget.style.transform = 'translateY(-1px)'
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(26,107,90,0.35)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'var(--accent)'
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(26,107,90,0.3)'
              }}
            >
              Start Researching
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </button>

            <a href="#how" style={{
              background: 'transparent', color: 'var(--text)',
              border: '1.5px solid var(--border2)',
              borderRadius: 'var(--radius)',
              padding: '14px 28px', fontSize: '1rem', fontWeight: 500,
              display: 'flex', alignItems: 'center', gap: 8,
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border2)'}
            >
              See how it works
            </a>
          </div>

          <p style={{ fontSize: '0.82rem', color: 'var(--text-3)', marginTop: 24 }}>
            Saves 40-60 hours of manual survey work
          </p>
        </div>

        {/* Right - animated topic card */}
        <div style={{ animation: 'fadeUp 0.6s 0.15s ease both' }}>
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-xl)',
            padding: 32,
            boxShadow: 'var(--shadow-lg)',
          }}>
            {/* Mock chat preview */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              borderBottom: '1px solid var(--border)', paddingBottom: 16, marginBottom: 20,
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: 'var(--accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                </svg>
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>ScholarAI</div>
                <div style={{
                  fontSize: '0.75rem', color: 'var(--green)',
                  display: 'flex', alignItems: 'center', gap: 4,
                }}>
                  <span style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: 'var(--green)', display: 'inline-block',
                  }}/> Ready
                </div>
              </div>
            </div>

            {/* User message */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
              <div style={{
                background: 'var(--accent)', color: 'white',
                borderRadius: '16px 16px 4px 16px',
                padding: '10px 16px', maxWidth: '80%',
                fontSize: '0.9rem', lineHeight: 1.5,
                minHeight: 40, display: 'flex', alignItems: 'center',
              }}>
                <span key={topicIdx} style={{ animation: 'fadeIn 0.4s ease' }}>
                  {TOPICS[topicIdx]}
                </span>
              </div>
            </div>

            {/* Agent steps preview */}
            {['Searching arXiv...', 'Parsing PDFs...', 'Building review...'].map((s, i) => (
              <div key={s} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px',
                background: i === 1 ? 'var(--accent-light)' : 'var(--bg2)',
                borderRadius: 'var(--radius-sm)',
                marginBottom: 8,
                fontSize: '0.82rem',
                color: i === 1 ? 'var(--accent)' : 'var(--text-3)',
                border: i === 1 ? '1px solid #c8e8e2' : '1px solid transparent',
              }}>
                <span style={{
                  width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
                  background: i < 1 ? 'var(--green)' : i === 1 ? 'var(--accent)' : 'var(--border2)',
                  animation: i === 1 ? 'pulse 1.4s infinite' : 'none',
                }}/>
                {s}
                {i < 1 && (
                  <span style={{ marginLeft: 'auto', color: 'var(--green)', fontSize: '0.75rem' }}>
                    Done
                  </span>
                )}
              </div>
            ))}

            <div style={{
              marginTop: 16, padding: '14px 16px',
              background: 'var(--bg2)', borderRadius: 'var(--radius)',
              fontSize: '0.8rem', color: 'var(--text-2)', lineHeight: 1.6,
            }}>
              <strong style={{ color: 'var(--text)' }}>Literature Review ready.</strong>
              {' '}Found 3 papers with methodology extraction, results analysis...
              <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                <span style={{
                  background: 'var(--accent-light)', color: 'var(--accent)',
                  borderRadius: 6, padding: '2px 10px', fontSize: '0.75rem', fontWeight: 500,
                }}>Download PDF</span>
                <span style={{
                  background: 'var(--bg3)', color: 'var(--text-2)',
                  borderRadius: 6, padding: '2px 10px', fontSize: '0.75rem',
                }}>Download MD</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---- Stats bar ---- */}
      <section style={{
        background: 'var(--accent)',
        padding: '32px 40px',
      }}>
        <div style={{
          maxWidth: 1100, margin: '0 auto',
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 32, textAlign: 'center',
        }}>
          {[
            { val: '40-60h', label: 'Hours saved per survey' },
            { val: '8',      label: 'AI agents working together' },
            { val: '10+',    label: 'Papers analyzed per run' },
            { val: '100%',   label: 'Real arXiv data' },
          ].map(s => (
            <div key={s.val}>
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: '2.2rem', fontWeight: 700,
                color: 'white', lineHeight: 1,
              }}>{s.val}</div>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.75)', marginTop: 6 }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ---- Features ---- */}
      <section id="features" style={{ padding: '100px 40px', background: 'var(--bg)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(1.8rem, 3vw, 2.6rem)',
              fontWeight: 700, color: 'var(--text)',
              letterSpacing: '-0.5px', marginBottom: 16,
            }}>
              Everything you need for a<br />
              <span style={{ fontStyle: 'italic', color: 'var(--accent)' }}>thorough literature survey</span>
            </h2>
            <p style={{ color: 'var(--text-2)', fontSize: '1rem', maxWidth: 480, margin: '0 auto' }}>
              A complete multi-agent pipeline that handles the entire research process automatically.
            </p>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 24,
          }}>
            {FEATURES.map((f, i) => (
              <div key={f.title} style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-lg)',
                padding: 28,
                boxShadow: 'var(--shadow-sm)',
                animation: 'fadeUp 0.5s ' + (i * 0.08) + 's ease both',
                transition: 'box-shadow 0.2s, border-color 0.2s, transform 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.boxShadow = 'var(--shadow)'
                e.currentTarget.style.borderColor = 'var(--accent-mid)'
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
              >
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: 'var(--accent-light)',
                  color: 'var(--accent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 18,
                }}>
                  {f.icon}
                </div>
                <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: 8 }}>{f.title}</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-2)', lineHeight: 1.6 }}>{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- How it works ---- */}
      <section id="how" style={{ padding: '100px 40px', background: 'var(--bg2)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(1.8rem, 3vw, 2.6rem)',
              fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.5px', marginBottom: 16,
            }}>
              From topic to review<br />
              <span style={{ fontStyle: 'italic', color: 'var(--accent)' }}>in four steps</span>
            </h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 0, position: 'relative',
          }}>
            {STEPS.map((step, i) => (
              <div key={step.num} style={{
                padding: '32px 28px', position: 'relative',
                borderRight: i < STEPS.length - 1 ? '1px solid var(--border)' : 'none',
              }}>
                <div style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '3.5rem', fontWeight: 700,
                  color: 'var(--accent-light)',
                  lineHeight: 1, marginBottom: 20,
                  userSelect: 'none',
                }}>
                  {step.num}
                </div>
                <div style={{ fontWeight: 600, fontSize: '1.05rem', marginBottom: 10 }}>
                  {step.title}
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-2)', lineHeight: 1.6 }}>
                  {step.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- CTA ---- */}
      <section style={{ padding: '100px 40px', background: 'var(--bg)', textAlign: 'center' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(2rem, 3.5vw, 3rem)',
            fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.5px', marginBottom: 20,
          }}>
            Ready to start your<br />
            <span style={{ fontStyle: 'italic', color: 'var(--accent)' }}>literature survey?</span>
          </h2>
          <p style={{ color: 'var(--text-2)', fontSize: '1rem', marginBottom: 36, lineHeight: 1.7 }}>
            Just type your research topic and let ScholarAI handle the rest.
            No setup required.
          </p>
          <button
            onClick={() => navigate('/chat')}
            style={{
              background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: 'var(--radius)',
              padding: '16px 40px', fontSize: '1.05rem', fontWeight: 600,
              display: 'inline-flex', alignItems: 'center', gap: 12,
              boxShadow: '0 4px 16px rgba(26,107,90,0.3)',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'var(--accent-dark)'
              e.currentTarget.style.transform = 'translateY(-2px)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'var(--accent)'
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            Open Chat
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        </div>
      </section>

      {/* ---- Footer ---- */}
      <footer style={{
        borderTop: '1px solid var(--border)',
        padding: '28px 40px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 24, height: 24, borderRadius: 6, background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>
          <span style={{ fontWeight: 600, fontSize: '0.9rem', fontFamily: 'var(--font-display)' }}>ScholarAI</span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-3)' }}>
          React + Vite &nbsp;|&nbsp; Spring Boot &nbsp;|&nbsp; LangGraph &nbsp;|&nbsp; arXiv
        </p>
      </footer>

    </div>
  )
}