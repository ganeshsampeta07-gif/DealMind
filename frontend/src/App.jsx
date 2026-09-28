import { useEffect, useRef, useState } from 'react';

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

const prompts = [
  'Tell me what you know about Ravi.',
  'Prepare me for my meeting with Ravi.',
  'What does Ravi care about?',
  "How should I handle Ravi's pricing objection?",
  'What should I know before talking to Ravi?',
];

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.7,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
  };

  const paths = {
    spark: <><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" /></>,
    chat: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l-1-4.5A7.5 7.5 0 1 1 20 11.5Z" /><path d="M8 11h.01M12 11h.01M16 11h.01" /></>,
    brain: <><path d="M12 5a3 3 0 0 0-5.8 1.1A3.5 3.5 0 0 0 5 12.5 3.5 3.5 0 0 0 8 18a3 3 0 0 0 4 1V5Z" /><path d="M12 5a3 3 0 0 1 5.8 1.1 3.5 3.5 0 0 1 1.2 6.4 3.5 3.5 0 0 1-3 5.5 3 3 0 0 1-4 1V5Z" /><path d="M8 9a2 2 0 0 1 2 2M16 9a2 2 0 0 0-2 2M8 15h1M15 15h1" /></>,
    send: <><path d="m21 3-7.2 18-3.6-7.2L3 10.2 21 3Z" /><path d="M10.2 13.8 15 9" /></>,
    arrow: <><path d="M7 17 17 7M7 7h10v10" /></>,
    chevron: <path d="m9 18 6-6-6-6" />,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    more: <><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></>,
    user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
    bulb: <><path d="M9 18h6M10 22h4M8.2 14.5A7 7 0 1 1 15.8 14.5c-.9.7-1.3 1.5-1.3 2.5h-5c0-1-.4-1.8-1.3-2.5Z" /></>,
  };

  return <svg {...common}>{paths[name] || paths.spark}</svg>;
}

function BrandMark({ small = false }) {
  return (
    <span className={`brand-mark${small ? ' brand-mark-small' : ''}`} aria-hidden="true">
      <Icon name="spark" size={small ? 18 : 21} />
    </span>
  );
}

function getMemoryLabel(memory) {
  const value = memory.toLowerCase();
  if (value.includes('prefer') || value.includes('billing')) return 'Preference';
  if (value.includes('expensive') || value.includes('price') || value.includes('cost') || value.includes('objection')) return 'Objection';
  if (value.includes('compar') || value.includes('zoho') || value.includes('competitor')) return 'Competitor';
  if (value.includes('interest') || value.includes('purchase') || value.includes('buying')) return 'Interest';
  return 'Customer detail';
}

function formatInline(text, prefix) {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={`${prefix}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={`${prefix}-${index}`}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function FormattedResponse({ content }) {
  const lines = content.split(/\r?\n/);
  const blocks = [];
  let paragraph = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push(<p key={`paragraph-${blocks.length}`}>{formatInline(paragraph.join(' '), `paragraph-${blocks.length}`)}</p>);
      paragraph = [];
    }
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line || /^[-*_]{3,}$/.test(line)) {
      flushParagraph();
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      const Heading = heading[1].length === 1 ? 'h3' : 'h4';
      blocks.push(<Heading key={`heading-${index}`}>{formatInline(heading[2], `heading-${index}`)}</Heading>);
      continue;
    }

    const listMatch = line.match(/^[-*]\s+(.+)$/);
    if (listMatch) {
      flushParagraph();
      const items = [];
      while (index < lines.length) {
        const item = lines[index].trim().match(/^[-*]\s+(.+)$/);
        if (!item) break;
        items.push(item[1]);
        index += 1;
      }
      index -= 1;
      blocks.push(
        <ul key={`list-${index}`}>
          {items.map((item, itemIndex) => <li key={`list-${index}-${itemIndex}`}>{formatInline(item, `list-${index}-${itemIndex}`)}</li>)}
        </ul>,
      );
      continue;
    }

    const orderedMatch = line.match(/^\d+[.)]\s+(.+)$/);
    if (orderedMatch) {
      flushParagraph();
      const items = [];
      while (index < lines.length) {
        const item = lines[index].trim().match(/^\d+[.)]\s+(.+)$/);
        if (!item) break;
        items.push(item[1]);
        index += 1;
      }
      index -= 1;
      blocks.push(
        <ol key={`ordered-${index}`}>
          {items.map((item, itemIndex) => <li key={`ordered-${index}-${itemIndex}`}>{formatInline(item, `ordered-${index}-${itemIndex}`)}</li>)}
        </ol>,
      );
      continue;
    }

    paragraph.push(line);
  }

  flushParagraph();
  return <div className="formatted-response">{blocks}</div>;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [memories, setMemories] = useState([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');
  const [error, setError] = useState('');
  const endOfMessages = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error('Backend health check failed');
        return response.json();
      })
      .then((data) => {
        if (active) setApiStatus(data.status === 'ok' ? 'online' : 'offline');
      })
      .catch(() => {
        if (active) setApiStatus('offline');
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    endOfMessages.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  async function sendMessage(value = draft) {
    const message = value.trim();
    if (!message || loading) return;

    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', content: message }]);
    setDraft('');
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) throw new Error('The DealMind API returned an error.');
      const data = await response.json();
      if (typeof data.response !== 'string' || !data.response.trim()) {
        throw new Error('The response was incomplete.');
      }

      setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', content: data.response }]);
      setMemories(Array.isArray(data.memories) ? data.memories.filter((item) => typeof item === 'string') : []);
      setApiStatus('online');
    } catch {
      setApiStatus('offline');
      setError('DealMind couldn’t connect to the backend. Check that the API is running at 127.0.0.1:8000, then try again.');
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function onComposerKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand-lockup" href="#home" aria-label="DealMind home">
          <BrandMark />
          <span className="brand-name">deal<span>mind</span></span>
        </a>

        <div className="sidebar-product-label">AI SALES INTELLIGENCE</div>

        <div className="nav-section-label">WORKSPACE</div>
        <button className="nav-item nav-item-active" type="button">
          <Icon name="chat" />
          <span>Sales copilot</span>
          <span className="nav-item-dot" />
        </button>
        <button className="nav-item" type="button">
          <Icon name="brain" />
          <span>Customer memory</span>
          <span className="nav-count">{memories.length || '—'}</span>
        </button>

        <div className="sidebar-divider" />
        <div className="customer-heading">
          <span className="nav-section-label">CUSTOMERS</span>
          <button type="button" className="icon-button subtle-icon" aria-label="Add customer">
            <Icon name="plus" size={16} />
          </button>
        </div>

        <button className="customer-item customer-item-active" type="button">
          <span className="customer-avatar">R</span>
          <span className="customer-info">
            <strong>Ravi</strong>
            <small>Sales Prospect</small>
          </span>
          <Icon name="chevron" size={15} />
        </button>

        <div className="sidebar-spacer" />

        <div className="memory-status-card">
          <div className="status-card-icon"><Icon name="brain" size={17} /></div>
          <div>
            <strong>{apiStatus === 'online' ? 'Memory is active' : apiStatus === 'checking' ? 'Checking memory' : 'Memory unavailable'}</strong>
            <span><i className={`status-dot${apiStatus === 'online' ? ' status-dot-live' : ''}`} /> Hindsight persistent memory</span>
          </div>
          <Icon name="more" size={17} />
        </div>
        <div className="sidebar-footer">
          <span className="user-avatar">A</span>
          <span className="footer-user"><strong>Alex Morgan</strong><small>Sales workspace</small></span>
          <Icon name="more" size={18} />
        </div>
      </aside>

      <main className="main-area" id="home">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span><Icon name="chevron" size={14} /><strong>Sales copilot</strong>
          </div>
          <div className="topbar-actions">
            <span className={`memory-active-pill${apiStatus === 'online' ? '' : ' memory-active-pill-muted'}`}>
              <i className={`status-dot${apiStatus === 'online' ? ' status-dot-live' : ''}`} />
              {apiStatus === 'online' ? 'Hindsight Memory Active' : apiStatus === 'checking' ? 'Checking Hindsight...' : 'Hindsight Memory Offline'}
            </span>
            <button type="button" className="icon-button topbar-more" aria-label="More options"><Icon name="more" /></button>
          </div>
        </header>

        <div className="content-grid">
          <section className="chat-panel" aria-label="DealMind chat">
            <div className="chat-heading">
              <div className="chat-title-lockup">
                <BrandMark small />
                <div>
                  <h1>DealMind</h1>
                  <p>AI Sales Intelligence Agent</p>
                </div>
              </div>
              <button type="button" className="account-chip">
                <span className="mini-avatar">R</span><span>Ravi</span><Icon name="chevron" size={14} />
              </button>
            </div>

            <div className={`conversation${messages.length ? ' conversation-has-messages' : ''}`}>
              {messages.length === 0 ? (
                <div className="welcome-block">
                  <div className="welcome-orb"><Icon name="spark" size={28} /></div>
                  <span className="eyebrow"><i className="status-dot status-dot-live" /> YOUR SALES COPILOT</span>
                  <h2>Your AI sales copilot that remembers <span>every important customer detail.</span></h2>
                  <p>Ask for a meeting briefing, explore a customer concern, or plan your next conversation. DealMind brings relevant context back from persistent memory.</p>
                  <div className="suggestion-label">GET STARTED WITH A PROMPT</div>
                  <div className="prompt-grid">
                    {prompts.map((prompt, index) => (
                      <button className="prompt-card" type="button" key={prompt} onClick={() => sendMessage(prompt)}>
                        <span className={`prompt-icon prompt-icon-${index}`}><Icon name={index === 1 ? 'clock' : index === 2 ? 'bulb' : index === 3 ? 'user' : 'brain'} size={17} /></span>
                        <span>{prompt}</span>
                        <Icon name="arrow" size={15} />
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="message-list">
                  {messages.map((message) => (
                    <article className={`message-row message-${message.role}`} key={message.id}>
                      {message.role === 'assistant' ? <BrandMark small /> : <span className="message-user-avatar">A</span>}
                      <div className="message-content">
                        <div className="message-meta">
                          <strong>{message.role === 'assistant' ? 'DealMind' : 'You'}</strong>
                          {message.role === 'assistant' && <span className="response-tag">AI RESPONSE</span>}
                        </div>
                          {message.role === 'assistant' ? <FormattedResponse content={message.content} /> : <p>{message.content}</p>}
                      </div>
                    </article>
                  ))}
                  {loading && (
                    <article className="message-row message-assistant loading-row">
                      <BrandMark small />
                      <div className="message-content">
                        <div className="message-meta"><strong>DealMind</strong><span className="response-tag">THINKING</span></div>
                        <div className="typing-indicator" aria-label="DealMind is thinking"><i /><i /><i /></div>
                      </div>
                    </article>
                  )}
                  <div ref={endOfMessages} />
                </div>
              )}
            </div>

            <div className="composer-wrap">
              {error && <div className="error-banner" role="alert"><span>!</span>{error}</div>}
              <div className="composer">
                <textarea
                  ref={inputRef}
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  onKeyDown={onComposerKeyDown}
                  placeholder="Ask anything about Ravi..."
                  rows={1}
                  aria-label="Message DealMind"
                  disabled={loading}
                />
                <div className="composer-bottom">
                  <span className="composer-hint"><Icon name="shield" size={14} /> Grounded in customer memory</span>
                  <div className="composer-actions">
                    <span className="enter-hint">↵ <span>to send</span></span>
                    <button className="send-button" type="button" onClick={() => sendMessage()} disabled={!draft.trim() || loading} aria-label="Send message">
                      <Icon name="send" size={17} />
                    </button>
                  </div>
                </div>
              </div>
              <p className="privacy-note">DealMind can make mistakes. Verify important customer details.</p>
            </div>
          </section>

          <aside className="memory-panel" aria-label="Customer memory">
            <div className="memory-panel-header">
              <div className="panel-title-icon"><Icon name="brain" size={19} /></div>
              <div><h2>Persistent Customer Memory</h2></div>
              <button type="button" className="icon-button subtle-icon" aria-label="Memory options"><Icon name="more" /></button>
            </div>

            <p className="memory-explanation">Powered by Hindsight — DealMind remembers useful customer context across conversations.</p>

            <div className="memory-live-card">
              <div className="live-card-top"><span className="live-icon"><Icon name="brain" size={16} /></span><span className="live-label"><i className="status-dot status-dot-live" /> HINDSIGHT MEMORY</span></div>
              <strong>Context that stays<br />between conversations.</strong>
              <p>DealMind recalls relevant customer facts to make every interaction more personal.</p>
              <div className="live-card-footer"><span><Icon name="shield" size={13} /> Persistent &amp; private</span><span className="live-sparkle">✳</span></div>
            </div>

            <div className="memories-section-heading">
              <div><span className="section-eyebrow">WHAT DEALMIND REMEMBERS</span><h3>Relevant memories <span>{memories.length}</span></h3></div>
              <Icon name="clock" size={16} />
            </div>

            {memories.length ? (
              <div className="memory-list">
                {memories.map((memory, index) => (
                  <article className="memory-card" key={`${memory}-${index}`}>
                    <div className="memory-card-top"><span className="memory-bullet"><Icon name="spark" size={13} /></span><span className="memory-category">{getMemoryLabel(memory)}</span></div>
                    <p>{memory}</p>
                    <div className="memory-card-footer"><span className="memory-source-dot" /> Saved in Hindsight</div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="memory-empty">
                <div className="empty-brain"><Icon name="brain" size={20} /></div>
                <strong>No memories recalled yet</strong>
                <p>When you chat with DealMind, relevant memories returned by Hindsight will appear here.</p>
              </div>
            )}

            <div className="memory-panel-bottom">
              <span className="bottom-lock"><Icon name="shield" size={14} /></span>
              <p><strong>Your customer context, remembered.</strong><br />Only relevant facts are surfaced for each conversation.</p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
