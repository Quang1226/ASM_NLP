import { useEffect, useRef, useState } from 'react';
import {
  ArrowRight, ArrowUpRight, AudioLines, Bot, Check, ChevronDown, CircleHelp,
  Bug, Cpu, Headphones, Laptop, Mail, Menu, MessageCircle, Minus, RotateCcw,
  Send, ShieldCheck, Sparkles, Truck, X,
} from 'lucide-react';
import { chatAPI } from './api';
import AdminPage from './AdminPage';

const SUGGESTIONS = [
  'How long does delivery take?',
  'How do I request a refund?',
  'Where can I view my invoice?',
];

const initialMessages = [
  { id: 'welcome', sender: 'bot', text: 'Hi! I’m the Demo Tech Store assistant. Ask me about demo orders, delivery, refunds, invoices, payments, or accounts.', time: 'Now' },
];

const CLARIFY_CHIPS = {
  orders: [
    'How can I change an item in my order?',
    'How can I change the shipping address for my demo order?',
    'How do I check my order status?',
  ],
  delivery: [
    'How long does standard delivery take?',
    'What delivery options does the demo store offer?',
    'How do I check my order status?',
  ],
  refunds: [
    'What is the demo refund policy?',
    'How do I request a refund?',
    'How can I track my refund request?',
  ],
  invoices: [
    'Where can I view my demo invoice?',
    'How can I download a copy of my demo invoice?',
    'What should I do if my payment failed?',
  ],
  accounts: [
    'How do I edit my demo account details?',
    'How do I switch to another account?',
    'How can I recover my password?',
  ],
  payments: [
    'What payment methods does the demo store offer?',
    'What should I do if my payment failed?',
    'How do I request a refund?',
  ],
  general: [
    'How do I check my order status?',
    'How long does standard delivery take?',
    'What payment methods does the demo store offer?',
  ],
};

function clarifyChips(intent = '', question = '') {
  const text = `${question} ${intent.replaceAll('_', ' ')}`.toLowerCase();
  if (/invoice|receipt/.test(text)) return CLARIFY_CHIPS.invoices;
  if (/refund|reimburse/.test(text)) return CLARIFY_CHIPS.refunds;
  if (/address|change order|change_order|cancel|order item/.test(text)) return CLARIFY_CHIPS.orders;
  if (/account|password|register|sign.?in|profile/.test(text)) return CLARIFY_CHIPS.accounts;
  if (/payment|pay|checkout|card|charge/.test(text)) return CLARIFY_CHIPS.payments;
  if (/deliver|shipping|parcel|shipment|carrier/.test(text)) return CLARIFY_CHIPS.delivery;
  if (/order|cancel|address/.test(text)) return CLARIFY_CHIPS.orders;
  return CLARIFY_CHIPS.general;
}

function ScoreMeter({ label, value, threshold, kind }) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  const percentage = Math.max(0, Math.min(100, numeric * 100));
  const hasThreshold = threshold != null && Number.isFinite(Number(threshold));
  const meetsThreshold = hasThreshold && numeric >= Number(threshold);
  return <div className="diagnostic-metric">
    <div className="diagnostic-metric-label"><span>{label}</span><strong>{numeric.toFixed(3)}</strong></div>
    <div className="diagnostic-track" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={1} aria-valuenow={Math.max(0, Math.min(1, numeric))}>
      <span className={`diagnostic-fill ${hasThreshold ? (meetsThreshold ? 'is-above' : `is-below ${kind}`) : ''}`} style={{ width: `${percentage}%` }} />
      {hasThreshold && <i className="diagnostic-threshold" style={{ left: `${Math.max(0, Math.min(100, Number(threshold) * 100))}%` }} />}
    </div>
    <small>{hasThreshold ? `G3 threshold: ${Number(threshold).toFixed(3)}` : 'Threshold unavailable'}</small>
  </div>;
}

function DiagnosticsCard({ meta }) {
  return <div className="message-inspector" aria-label="AI diagnostics card">
    <div className="diagnostic-heading"><Bug size={14} /><strong>AI diagnostics</strong><span>{meta.action_taken?.replaceAll('_', ' ')}</span></div>
    <ScoreMeter label="Classifier probability" value={meta.score} threshold={meta.decision_thresholds?.clarify_probability} kind="clarify" />
    <ScoreMeter label="Nearest train cosine" value={meta.nearest_train_cosine} threshold={meta.decision_thresholds?.scope_similarity} kind="scope" />
    <div className="diagnostic-details"><span>Intent</span><strong>{meta.predicted_intent?.replaceAll('_', ' ')}</strong><span>KB</span><strong>{meta.kb_reference}</strong><span>Route</span><strong>{meta.decision_reason?.replaceAll('_', ' ')}</strong></div>
    <p>Classifier probability is for the predicted intent, not the chance that a question is in scope. A human request or hardware repair boundary can override these thresholds.</p>
  </div>;
}

function ChatWidget({ openSignal }) {
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('idle');
  const [showContact, setShowContact] = useState(false);
  const [contact, setContact] = useState({ name: '', contact_value: '', note: '', consent: false });
  const [contactFeedback, setContactFeedback] = useState('');
  const [showInspector, setShowInspector] = useState(false);
  const bottomRef = useRef(null);
  const idRef = useRef(0);
  const sessionPromiseRef = useRef(null);

  useEffect(() => {
    if (openSignal > 0) { setOpen(true); setMinimized(false); }
  }, [openSignal]);

  useEffect(() => {
    if (!open || sessionId) return;
    let cancelled = false;
    setStatus('connecting');
    sessionPromiseRef.current ||= chatAPI.start();
    sessionPromiseRef.current.then((data) => {
      if (!cancelled) { setSessionId(data.session_id); setStatus('ready'); }
    }).catch(() => { if (!cancelled) { setStatus('unavailable'); sessionPromiseRef.current = null; } });
    return () => { cancelled = true; };
  }, [open, sessionId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, busy, open, showInspector]);

  const addMessage = (sender, text, meta = null) => {
    idRef.current += 1;
    setMessages((current) => [...current, {
      id: idRef.current, sender, text, meta,
      time: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    }]);
  };

  const sendMessage = async (providedText) => {
    const text = (providedText ?? input).trim();
    if (!text || busy || !sessionId) return;
    setInput('');
    setBusy(true);
    addMessage('user', text);
    try {
      const response = await chatAPI.message(sessionId, text);
      addMessage('bot', response.message_text, response);
    } catch (error) {
      addMessage('bot', 'I could not reach the demo assistant. Please try again in a moment.');
    } finally {
      setBusy(false);
    }
  };

  const newChat = async () => {
    setMessages(initialMessages);
    setSessionId(null);
    sessionPromiseRef.current = null;
    setStatus('idle');
    setInput('');
    setShowContact(false);
    setContactFeedback('');
  };

  const submitContact = async (event) => {
    event.preventDefault();
    setContactFeedback('');
    if (!sessionId) return;
    try {
      const result = await chatAPI.contact({ session_id: sessionId, ...contact });
      setContactFeedback(result.message);
      setContact({ name: '', contact_value: '', note: '', consent: false });
    } catch (error) {
      setContactFeedback(error.message);
    }
  };

  return (
    <div className="widget-layer">
      {!open && (
        <div className="chat-launcher-wrap">
          <div className="launcher-note">Need a hand with your tech order? <span>Ask our demo assistant.</span></div>
          <button className="chat-launcher" aria-label="Open support chat" onClick={() => setOpen(true)}>
            <MessageCircle size={28} strokeWidth={2.1} />
            <span className="launcher-spark"><Sparkles size={13} /></span>
          </button>
        </div>
      )}

      {open && (
        <section className={`chat-panel ${minimized ? 'is-minimized' : ''}`} aria-label="Demo Tech Store chat">
          <header className="chat-panel-head">
            <div className="assistant-mark"><Bot size={23} /></div>
            <div className="assistant-heading">
              <strong>Tech Store Assistant</strong>
              <span><i className={status === 'ready' ? 'status-dot' : 'status-dot muted'} />{status === 'ready' ? 'Demo support · Online' : status === 'connecting' ? 'Connecting…' : 'Demo support'}</span>
            </div>
            <button className={`icon-button diagnostics-toggle ${showInspector ? 'is-active' : ''}`} title={showInspector ? 'Hide AI diagnostics' : 'Show AI diagnostics'} aria-label={showInspector ? 'Hide AI diagnostics' : 'Show AI diagnostics'} aria-pressed={showInspector} onClick={() => setShowInspector(!showInspector)}><Bug size={17} /></button>
            <button className="icon-button" title={minimized ? 'Expand' : 'Minimize'} aria-label={minimized ? 'Expand chat' : 'Minimize chat'} onClick={() => setMinimized(!minimized)}><Minus size={18} /></button>
            <button className="icon-button" title="Close" aria-label="Close chat" onClick={() => { setOpen(false); setMinimized(false); }}><X size={18} /></button>
          </header>

          {!minimized && <>
            <div className="chat-disclosure"><ShieldCheck size={14} /> Course project demo. No real orders or agents are connected.</div>
            <div className="chat-scroll" role="log" aria-live="polite">
              <div className="chat-date">Today</div>
              {messages.map((message, index) => <div key={message.id} className={`message-row ${message.sender}`}>
                {message.sender === 'bot' && <span className="message-avatar"><Bot size={15} /></span>}
                <div className="message-stack">
                  <div className="message-bubble">{message.text}</div>
                  <div className="message-meta"><span>{message.time}</span>{message.meta?.action_taken && <span className={`action-tag action-${message.meta.action_taken}`}>{message.meta.action_taken.replaceAll('_', ' ')}</span>}</div>
                  {showInspector && message.meta && <DiagnosticsCard meta={message.meta} />}
                  {index === messages.length - 1 && message.meta?.action_taken === 'clarify' && message.meta?.decision_reason !== 'missing_active_kb_entry' && <div className="context-chips" aria-label="Suggested follow-up questions">
                    {clarifyChips(message.meta.predicted_intent, messages.slice(0, index).reverse().find((item) => item.sender === 'user')?.text).map((suggestion) => <button key={suggestion} onClick={() => sendMessage(suggestion)} disabled={!sessionId || busy}>{suggestion}<ArrowUpRight size={13} /></button>)}
                  </div>}
                </div>
              </div>)}
              {busy && <div className="message-row bot"><span className="message-avatar"><Bot size={15} /></span><div className="typing"><i /><i /><i /></div></div>}
              <div ref={bottomRef} />
            </div>
            {messages.length === 1 && <div className="quick-prompts">{SUGGESTIONS.map((text) => <button key={text} onClick={() => sendMessage(text)} disabled={!sessionId || busy}>{text}<ArrowUpRight size={13} /></button>)}</div>}
            {showContact && <form className="contact-form" onSubmit={submitContact}>
              <div className="contact-form-top"><strong>Leave contact details</strong><button type="button" className="text-button" onClick={() => setShowContact(false)}>Close</button></div>
              <p>Saved locally for this course demo. No real team is notified.</p>
              <input required maxLength={80} placeholder="Your name" value={contact.name} onChange={(e) => setContact({ ...contact, name: e.target.value })} />
              <input required maxLength={120} placeholder="Email or phone" value={contact.contact_value} onChange={(e) => setContact({ ...contact, contact_value: e.target.value })} />
              <textarea maxLength={500} placeholder="Short note (optional)" value={contact.note} onChange={(e) => setContact({ ...contact, note: e.target.value })} />
              <label className="consent"><input type="checkbox" checked={contact.consent} onChange={(e) => setContact({ ...contact, consent: e.target.checked })} /> I agree to save these details in the local demo.</label>
              <button className="contact-submit" type="submit" disabled={!contact.consent}>Save contact</button>
              {contactFeedback && <small role="status">{contactFeedback}</small>}
            </form>}
            {status === 'unavailable' && <p className="chat-error">Demo API unavailable. Start the backend, then reopen chat.</p>}
            <form className="chat-composer" onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
              <input aria-label="Type your message" placeholder={status === 'ready' ? 'Ask a question…' : 'Connecting to demo…'} value={input} onChange={(e) => setInput(e.target.value)} disabled={status !== 'ready' || busy} maxLength={1000} />
              <button type="submit" aria-label="Send message" disabled={!input.trim() || !sessionId || busy}><Send size={17} /></button>
            </form>
            <div className="chat-foot">
              <button onClick={newChat}><RotateCcw size={13} /> New chat</button>
              <button onClick={() => setShowContact(!showContact)}><Mail size={13} /> Leave contact</button>
            </div>
          </>}
        </section>
      )}
    </div>
  );
}

const products = [
  { icon: Laptop, label: 'Laptops', detail: 'Power for everything', className: 'product-laptop' },
  { icon: Headphones, label: 'Audio', detail: 'Listen differently', className: 'product-audio' },
  { icon: Cpu, label: 'Components', detail: 'Built to perform', className: 'product-parts' },
];

function Storefront() {
  const [openSignal, setOpenSignal] = useState(0);
  const openChat = () => setOpenSignal((n) => n + 1);
  return <>
    <div className="store-shell">
      <div className="announcement"><Sparkles size={13} /> An interactive NLP course project <span>·</span> Everything here is simulated</div>
      <header className="site-header">
        <a className="brand" href="/"><span className="brand-glyph"><Cpu size={21} /></span><span>Demo<span className="brand-accent">Tech</span>Store</span></a>
        <nav className="site-nav" aria-label="Main navigation"><a href="#products">Explore</a><a href="#how-it-works">How it works</a><a href="#support">Support</a></nav>
        <div className="nav-actions"><a className="admin-link" href="/admin">Admin</a><button className="nav-chat" onClick={openChat}>Ask the assistant <ArrowUpRight size={15} /></button></div>
      </header>
      <main>
        <section className="hero">
          <div className="hero-copy"><div className="eyebrow"><span /> SMARTER SUPPORT, SIMPLER SHOPPING</div>
            <h1>Tech questions?<br /><em>We’re here to help.</em></h1>
            <p>Explore a simulated technology store and try an intent-aware assistant built to guide, clarify, and know its limits.</p>
            <div className="hero-actions"><button className="primary-button" onClick={openChat}>Chat with the assistant <ArrowRight size={17} /></button><a className="secondary-button" href="#how-it-works">See how it works <ChevronDown size={17} /></a></div>
            <div className="hero-proof"><div className="proof-icon"><ShieldCheck size={19} /></div><div><strong>Designed for clear answers</strong><span>Grounded in a reviewed demo knowledge base</span></div></div>
          </div>
          <div className="hero-art" aria-hidden="true"><div className="art-grid" /><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" /><div className="device-shadow" /><div className="device-screen"><div className="screen-top"><span /><span /><span /></div><div className="screen-content"><div className="screen-line large" /><div className="screen-line" /><div className="screen-line short" /><div className="screen-chip"><Sparkles size={19} /> How can I help you today?</div><div className="screen-answer"><div className="screen-answer-icon"><Bot size={18} /></div><div><span /><span /></div></div></div></div><div className="device-base" /><div className="float-card shipping"><Truck size={19} /><span><strong>Delivery</strong><small>3–5 business days*</small></span></div><div className="float-card support"><MessageCircle size={19} /><span><strong>Helpful guidance</strong><small>Whenever you need it</small></span></div><div className="art-glow" /></div>
        </section>
        <section className="category-section" id="products"><div className="section-heading"><div><span className="section-kicker">EXPLORE THE DEMO STORE</span><h2>Find your next favorite thing.</h2></div><p>Products shown here are visual examples. No purchases are processed in this demo.</p></div><div className="product-grid">{products.map(({ icon: Icon, label, detail, className }) => <button key={label} className={`product-card ${className}`} onClick={openChat}><div className="product-visual"><Icon size={70} strokeWidth={1.2} /></div><div className="product-details"><div><strong>{label}</strong><span>{detail}</span></div><ArrowUpRight size={20} /></div></button>)}</div></section>
        <section className="support-section" id="how-it-works"><div className="support-copy"><div className="support-icon"><AudioLines size={27} /></div><span className="section-kicker">SUPPORT THAT THINKS FIRST</span><h2>A helpful answer starts<br />with the right question.</h2><p>The assistant recognizes 27 customer intents, looks up approved demo guidance, and asks for clarity when a request is uncertain. It does not access real orders or connect a live agent.</p><div className="support-features"><span><Check size={15} /> Intent-aware replies</span><span><Check size={15} /> Clear scope boundaries</span><span><Check size={15} /> No paid AI API required</span></div><button className="text-link" onClick={openChat}>Try a question <ArrowRight size={17} /></button></div><div className="support-demo" id="support"><div className="demo-heading"><span><Bot size={17} /> Tech Store Assistant</span><i>DEMO</i></div><div className="demo-user">How long will my monitor take to arrive?</div><div className="demo-bot"><span className="demo-bot-icon"><Bot size={15} /></span><p>After dispatch, standard delivery is estimated at 3–5 business days in this demo. I can’t track a live parcel.</p></div><div className="demo-typing"><span /><span /><span /></div></div></section>
      </main>
      <footer className="site-footer"><div className="footer-brand"><Cpu size={20} /> Demo Tech Store</div><p>Course project demonstration · No real transactions or support connections.</p><a href="/admin">Admin workspace <ArrowUpRight size={13} /></a></footer>
    </div>
    <ChatWidget openSignal={openSignal} />
  </>;
}

export default function App() {
  return window.location.pathname.startsWith('/admin') ? <AdminPage /> : <Storefront />;
}
