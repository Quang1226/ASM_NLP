import { useCallback, useEffect, useState } from 'react';
import {
  ArrowLeft, ArrowRight, BookOpen, Check, ChevronRight, ClipboardList,
  Cpu, Eye, LogOut, Mail, MessageSquareText, Pencil, Plus, Save,
  Search, ShieldCheck, Trash2, X,
} from 'lucide-react';
import { adminAPI } from './api';

const TOKEN_KEY = 'demo_tech_admin_token';

function AdminLogin({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await adminAPI.login(username, password);
      sessionStorage.setItem(TOKEN_KEY, result.access_token);
      onLogin(result.access_token);
    } catch (err) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  return <div className="admin-login-page">
    <a className="admin-back" href="/"><ArrowLeft size={16} /> Back to store</a>
    <div className="admin-login-card">
      <div className="admin-login-glyph"><ShieldCheck size={30} /></div>
      <span className="section-kicker">PRIVATE DEMO WORKSPACE</span>
      <h1>Welcome back.</h1>
      <p>Sign in to review knowledge, contact requests, and conversation history from this local demo.</p>
      <form onSubmit={submit}>
        <label>Username<input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required placeholder="Admin username" /></label>
        <label>Password<input autoComplete="current-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Admin password" /></label>
        {error && <div className="form-error" role="alert">{error}</div>}
        <button disabled={busy} type="submit">{busy ? 'Signing in…' : 'Sign in'} <ArrowRight size={17} /></button>
      </form>
      <small>No default credentials are included. Configure them locally in the backend environment.</small>
    </div>
  </div>;
}

function KnowledgePanel({ token, onUnauthorized }) {
  const [entries, setEntries] = useState([]);
  const [query, setQuery] = useState('');
  const [editing, setEditing] = useState(null);
  const [draft, setDraft] = useState({ intent: '', response: '', active: true });
  const [showCreate, setShowCreate] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { setEntries(await adminAPI.call('/knowledge', token)); }
    catch (error) { if (error.status === 401) onUnauthorized(); else setFeedback(error.message); }
    finally { setLoading(false); }
  }, [token, onUnauthorized]);

  useEffect(() => { load(); }, [load]);

  const save = async (event) => {
    event.preventDefault();
    setFeedback('');
    try {
      if (editing) {
        await adminAPI.call(`/knowledge/${editing}`, token, { method: 'PUT', body: JSON.stringify({ response: draft.response, active: draft.active }) });
      } else {
        await adminAPI.call('/knowledge', token, { method: 'POST', body: JSON.stringify({ intent: draft.intent, response: draft.response }) });
      }
      setFeedback('Knowledge saved. New answers are available to the demo chat.');
      setEditing(null); setShowCreate(false); setDraft({ intent: '', response: '', active: true });
      load();
    } catch (error) { if (error.status === 401) onUnauthorized(); else setFeedback(error.message); }
  };

  const remove = async (item) => {
    if (!window.confirm(`Delete ${item.kb_reference}? The chat will ask for clarification if no active answer remains.`)) return;
    try {
      await adminAPI.call(`/knowledge/${item.id}`, token, { method: 'DELETE' });
      setFeedback('Knowledge entry deleted.');
      load();
    } catch (error) { if (error.status === 401) onUnauthorized(); else setFeedback(error.message); }
  };

  const filtered = entries.filter((item) => `${item.intent} ${item.kb_reference} ${item.response}`.toLowerCase().includes(query.toLowerCase()));
  const intents = [...new Set(entries.map((item) => item.intent))].sort();
  return <section className="admin-panel">
    <div className="panel-heading"><div><span className="section-kicker">CONTENT LIBRARY</span><h2>Knowledge base</h2><p>Review and customize demo responses for each trained intent.</p></div><button className="admin-primary" onClick={() => { setShowCreate(true); setEditing(null); setDraft({ intent: intents[0] || '', response: '', active: true }); }}><Plus size={17} /> Add answer</button></div>
    <div className="admin-toolbar"><label className="search-box"><Search size={18} /><input placeholder="Search intents, references, responses…" value={query} onChange={(e) => setQuery(e.target.value)} /></label><span>{filtered.length} entries</span></div>
    {feedback && <div className="admin-feedback" role="status">{feedback}</div>}
    {loading ? <p className="empty-state">Loading knowledge…</p> : <div className="knowledge-grid">{filtered.map((item) => <article className="knowledge-card" key={item.id}>
      <div className="knowledge-card-head"><span className="intent-pill">{item.intent.replaceAll('_', ' ')}</span><span className={item.active ? 'kb-status' : 'kb-status inactive'}>{item.active ? 'Active' : 'Inactive'}</span></div>
      <strong>{item.kb_reference}</strong><p>{item.response}</p>
      <div className="knowledge-card-foot"><small>{item.is_seed ? 'Original draft' : 'Custom answer'} · {item.action}</small><div><button title="Edit" onClick={() => { setEditing(item.id); setShowCreate(false); setDraft({ intent: item.intent, response: item.response, active: item.active }); }}><Pencil size={16} /></button><button title="Delete" onClick={() => remove(item)}><Trash2 size={16} /></button></div></div>
    </article>)}</div>}
    {(editing || showCreate) && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) { setEditing(null); setShowCreate(false); } }}><div className="admin-modal" role="dialog" aria-modal="true" aria-label={editing ? 'Edit knowledge' : 'Add knowledge'}><div className="modal-head"><div><span className="section-kicker">KNOWLEDGE EDITOR</span><h3>{editing ? 'Edit answer' : 'Add an answer'}</h3></div><button className="icon-button" onClick={() => { setEditing(null); setShowCreate(false); }}><X size={20} /></button></div><form onSubmit={save}>
      <label>Trained intent<select value={draft.intent} disabled={Boolean(editing)} onChange={(e) => setDraft({ ...draft, intent: e.target.value })}>{intents.map((intent) => <option key={intent}>{intent}</option>)}</select></label>
      <label>Response<textarea rows={7} required maxLength={2000} value={draft.response} onChange={(e) => setDraft({ ...draft, response: e.target.value })} placeholder="Write a clear, simulated answer…" /></label>
      {editing && <label className="toggle-row"><input type="checkbox" checked={draft.active} onChange={(e) => setDraft({ ...draft, active: e.target.checked })} /> Active in chat</label>}
      <div className="modal-actions"><button type="button" className="admin-outline" onClick={() => { setEditing(null); setShowCreate(false); }}>Cancel</button><button className="admin-primary" type="submit"><Save size={16} /> Save answer</button></div>
    </form></div></div>}
  </section>;
}

function LeadsPanel({ token, onUnauthorized }) {
  const [leads, setLeads] = useState([]);
  const [history, setHistory] = useState(null);
  const [feedback, setFeedback] = useState('');

  const load = useCallback(async () => {
    try { setLeads(await adminAPI.call('/leads', token)); }
    catch (error) { if (error.status === 401) onUnauthorized(); else setFeedback(error.message); }
  }, [token, onUnauthorized]);

  useEffect(() => { load(); const id = setInterval(load, 10000); return () => clearInterval(id); }, [load]);

  const viewHistory = async (lead) => {
    try { setHistory({ lead, messages: await adminAPI.call(`/history/${lead.session_id}`, token) }); }
    catch (error) { if (error.status === 401) onUnauthorized(); else setFeedback(error.message); }
  };

  const remove = async (lead) => {
    if (!window.confirm(`Delete the saved contact for ${lead.name}?`)) return;
    try { await adminAPI.call(`/leads/${lead.id}`, token, { method: 'DELETE' }); load(); }
    catch (error) { if (error.status === 401) onUnauthorized(); else setFeedback(error.message); }
  };

  return <section className="admin-panel"><div className="panel-heading"><div><span className="section-kicker">OPT-IN CONTACTS</span><h2>Contact requests</h2><p>Only details submitted through the chat contact form are shown here.</p></div><button className="admin-outline" onClick={load}>Refresh</button></div>
    {feedback && <div className="admin-feedback">{feedback}</div>}
    <div className="lead-table-wrap"><table className="lead-table"><thead><tr><th>Contact</th><th>Details</th><th>Submitted</th><th>Action</th></tr></thead><tbody>{leads.map((lead) => <tr key={lead.id}><td><strong>{lead.name}</strong><small>Session {lead.session_id.slice(0, 8)}…</small></td><td><span>{lead.contact_value}</span><small>{lead.note || 'No note'}</small></td><td>{new Date(lead.consent_at).toLocaleString()}</td><td><div className="lead-actions"><button onClick={() => viewHistory(lead)}><Eye size={16} /> View chat</button><button title="Delete contact" onClick={() => remove(lead)}><Trash2 size={16} /></button></div></td></tr>)}</tbody></table>{leads.length === 0 && <div className="empty-state"><Mail size={31} /><strong>No contact requests yet</strong><p>Customers only appear after they choose to submit the form in chat.</p></div>}</div>
    {history && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setHistory(null); }}><div className="admin-modal history-modal" role="dialog" aria-modal="true" aria-label="Chat history"><div className="modal-head"><div><span className="section-kicker">CONVERSATION HISTORY</span><h3>{history.lead.name}</h3></div><button className="icon-button" onClick={() => setHistory(null)}><X size={20} /></button></div><div className="history-list">{history.messages.length ? history.messages.map((message) => <div className={`history-bubble ${message.sender}`} key={message.id}><small>{message.sender === 'bot' ? 'Assistant' : 'Customer'} · {new Date(message.created_at).toLocaleTimeString()}</small><p>{message.message_text}</p>{message.action && <span>{message.action.replaceAll('_', ' ')}</span>}</div>) : <p className="empty-state">No messages in this session.</p>}</div><div className="modal-actions"><button className="admin-primary" onClick={() => setHistory(null)}>Close</button></div></div></div>}
  </section>;
}

export default function AdminPage() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY));
  const [tab, setTab] = useState('knowledge');
  const [diagnostics, setDiagnostics] = useState(null);
  const logout = useCallback(() => { sessionStorage.removeItem(TOKEN_KEY); setToken(null); }, []);

  useEffect(() => {
    if (!token) return;
    adminAPI.call('/diagnostics', token).then(setDiagnostics).catch((error) => { if (error.status === 401) logout(); });
  }, [token, logout]);

  if (!token) return <AdminLogin onLogin={setToken} />;
  return <div className="admin-shell"><aside className="admin-sidebar"><a href="/" className="admin-brand"><span className="brand-glyph"><Cpu size={20} /></span><span>Demo<span>Tech</span>Store</span></a><div className="workspace-label">WORKSPACE</div><nav><button className={tab === 'knowledge' ? 'active' : ''} onClick={() => setTab('knowledge')}><BookOpen size={19} /> Knowledge base <ChevronRight size={15} /></button><button className={tab === 'leads' ? 'active' : ''} onClick={() => setTab('leads')}><ClipboardList size={19} /> Contact requests <ChevronRight size={15} /></button></nav><div className="sidebar-bottom"><span><ShieldCheck size={17} /> Local demo only</span><button onClick={() => { adminAPI.call('/logout', token, { method: 'POST' }).catch(() => {}); logout(); }}><LogOut size={17} /> Sign out</button></div></aside><div className="admin-main"><header className="admin-topbar"><div><span className="section-kicker">DEMO MANAGEMENT</span><strong>{tab === 'knowledge' ? 'Knowledge base' : 'Contact requests'}</strong></div><div className="topbar-right"><span className="admin-version"><i /> {diagnostics?.model_version || 'Local demo'}</span><a href="/" target="_blank" rel="noreferrer">View store <ArrowRight size={15} /></a></div></header><main>{tab === 'knowledge' ? <KnowledgePanel token={token} onUnauthorized={logout} /> : <LeadsPanel token={token} onUnauthorized={logout} />}</main></div></div>;
}
