import { useState, useEffect } from 'react';
import {
  Key, Cpu, Search, Layers, ShieldCheck, CheckCircle2,
  AlertCircle, Eye, EyeOff, Loader2, Save, RotateCcw,
  Sparkles, Sliders, Database, Trash2
} from 'lucide-react';
import styles from './SettingsPanel.module.css';
import { getSettings, updateSettings, testApiKey, clearKnowledgeBase } from '../../api/client';

const PROVIDER_OPTIONS = [
  { id: 'gemini', name: 'Google Gemini', desc: 'Gemini 2.0 Flash & 1.5 Pro multimodal models' },
  { id: 'groq', name: 'Groq Cloud', desc: 'Ultra-low latency Llama 3.3 & open models' },
  { id: 'openai', name: 'OpenAI', desc: 'GPT-4o, GPT-4o-mini and reasoning models' },
  { id: 'anthropic', name: 'Anthropic', desc: 'Claude 3.5 Sonnet & Haiku models' },
];

const MODEL_PRESETS = {
  gemini: [
    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash (Recommended · Fast)' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Deep Reasoning)' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
  ],
  groq: [
    { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile (Recommended)' },
    { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant (Ultra-fast)' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B (32k Context)' },
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o (Omni flagship)' },
    { value: 'gpt-4o-mini', label: 'GPT-4o-mini (Fast & efficient)' },
  ],
  anthropic: [
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (State of the art)' },
    { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Fast)' },
  ],
};

export default function SettingsPanel({ onSettingsUpdated }) {
  const [activeTab, setActiveTab] = useState('llm'); // 'llm' | 'retrieval' | 'storage'
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null); // { type: 'success' | 'error', message: string }

  // Form state
  const [config, setConfig] = useState({
    chat_provider: 'gemini',
    temperature: 0.3,
    gemini_api_key: '',
    gemini_model: 'gemini-2.0-flash',
    groq_api_key: '',
    groq_model: 'llama-3.3-70b-versatile',
    openai_api_key: '',
    openai_model: 'gpt-4o',
    anthropic_api_key: '',
    anthropic_model: 'claude-3-5-sonnet-20241022',
    top_k: 5,
    rerank_enabled: true,
    chunk_size: 1000,
    chunk_overlap: 200,
    system_prompt_mode: 'default',
  });

  // Masked status tracking
  const [keyStatus, setKeyStatus] = useState({
    gemini: false,
    groq: false,
    openai: false,
    anthropic: false,
  });

  // Password visibility
  const [showKeys, setShowKeys] = useState({
    gemini: false,
    groq: false,
    openai: false,
    anthropic: false,
  });

  // Test connection state per provider
  const [testState, setTestState] = useState({}); // { [provider]: { loading: bool, success: bool, message: string } }

  // Clearing state
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    fetchCurrentSettings();
  }, []);

  const fetchCurrentSettings = async () => {
    try {
      setLoading(true);
      const res = await getSettings();
      setConfig((prev) => ({
        ...prev,
        chat_provider: res.chat_provider || 'gemini',
        temperature: res.temperature ?? 0.3,
        gemini_model: res.gemini_model || 'gemini-2.0-flash',
        groq_model: res.groq_model || 'llama-3.3-70b-versatile',
        openai_model: res.openai_model || 'gpt-4o',
        anthropic_model: res.anthropic_model || 'claude-3-5-sonnet-20241022',
        gemini_api_key: res.gemini_api_key_masked || '',
        groq_api_key: res.groq_api_key_masked || '',
        openai_api_key: res.openai_api_key_masked || '',
        anthropic_api_key: res.anthropic_api_key_masked || '',
        top_k: res.top_k || 5,
        rerank_enabled: res.rerank_enabled ?? true,
        chunk_size: res.chunk_size || 1000,
        chunk_overlap: res.chunk_overlap || 200,
        system_prompt_mode: res.system_prompt_mode || 'default',
      }));
      setKeyStatus({
        gemini: res.has_gemini_key,
        groq: res.has_groq_key,
        openai: res.has_openai_key,
        anthropic: res.has_anthropic_key,
      });
    } catch (err) {
      setFeedback({ type: 'error', message: `Failed to load settings: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field, value) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const toggleShowKey = (provider) => {
    setShowKeys((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleTestKey = async (provider) => {
    const apiKey = config[`${provider}_api_key`];
    const model = config[`${provider}_model`];

    setTestState((prev) => ({
      ...prev,
      [provider]: { loading: true, success: null, message: 'Validating key...' },
    }));

    try {
      const res = await testApiKey({ provider, api_key: apiKey, model });
      setTestState((prev) => ({
        ...prev,
        [provider]: { loading: false, success: res.success, message: res.message },
      }));
      if (res.success) {
        setKeyStatus((prev) => ({ ...prev, [provider]: true }));
      }
    } catch (err) {
      setTestState((prev) => ({
        ...prev,
        [provider]: { loading: false, success: false, message: err.message },
      }));
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setFeedback(null);
    try {
      await updateSettings(config);
      setFeedback({ type: 'success', message: 'Settings and active AI providers updated successfully!' });
      if (onSettingsUpdated) {
        onSettingsUpdated();
      }
      setTimeout(() => setFeedback(null), 4000);
    } catch (err) {
      setFeedback({ type: 'error', message: `Save error: ${err.message}` });
    } finally {
      setSaving(false);
    }
  };

  const handleClearIndex = async () => {
    if (!window.confirm('Are you sure you want to clear all indexed vectors and documents? This cannot be undone.')) {
      return;
    }
    setClearing(true);
    try {
      const res = await clearKnowledgeBase();
      if (res.success) {
        setFeedback({ type: 'success', message: 'Knowledge base index cleared.' });
        if (onSettingsUpdated) onSettingsUpdated();
      } else {
        setFeedback({ type: 'error', message: res.message });
      }
    } catch (err) {
      setFeedback({ type: 'error', message: `Failed to clear index: ${err.message}` });
    } finally {
      setClearing(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.panel} style={{ alignItems: 'center', justifyContent: 'center' }}>
        <Loader2 size={32} className="spin" color="var(--primary)" />
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.headerRow}>
          <div>
            <h1 className={styles.pageTitle}>System Settings</h1>
            <p className={styles.pageSub}>Configure custom LLM models, API credentials, and retrieval pipeline</p>
          </div>
          <div className={styles.headerActions}>
            <button className={styles.saveBtn} onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div className={`${styles.feedbackBanner} ${feedback.type === 'success' ? styles.feedbackSuccess : styles.feedbackError}`}>
            {feedback.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className={styles.navTabs}>
          <button
            className={`${styles.navTab} ${activeTab === 'llm' ? styles.active : ''}`}
            onClick={() => setActiveTab('llm')}
          >
            <Cpu size={16} />
            <span>AI Models & API Keys</span>
          </button>
          <button
            className={`${styles.navTab} ${activeTab === 'retrieval' ? styles.active : ''}`}
            onClick={() => setActiveTab('retrieval')}
          >
            <Search size={16} />
            <span>RAG & Search Engine</span>
          </button>
          <button
            className={`${styles.navTab} ${activeTab === 'storage' ? styles.active : ''}`}
            onClick={() => setActiveTab('storage')}
          >
            <Database size={16} />
            <span>Index & Maintenance</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={styles.scrollArea}>
        {/* TAB 1: LLM & API KEYS */}
        {activeTab === 'llm' && (
          <>
            {/* Active Provider Selection */}
            <div className={styles.sectionCard}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitleWrap}>
                  <div className={styles.cardIcon}><Cpu size={20} /></div>
                  <div>
                    <div className={styles.cardTitle}>Active LLM Provider</div>
                    <div className={styles.cardSub}>Select the primary language model engine for chat responses</div>
                  </div>
                </div>
              </div>

              <div className={styles.providerGrid}>
                {PROVIDER_OPTIONS.map((p) => {
                  const isConfigured = keyStatus[p.id] || (config[`${p.id}_api_key`] && config[`${p.id}_api_key`].length > 5);
                  return (
                    <div
                      key={p.id}
                      className={`${styles.providerCard} ${config.chat_provider === p.id ? styles.active : ''}`}
                      onClick={() => handleFieldChange('chat_provider', p.id)}
                    >
                      <div className={styles.providerCardHeader}>
                        <span className={styles.providerName}>{p.name}</span>
                        <span className={`${styles.providerStatus} ${isConfigured ? styles.statusConfigured : styles.statusUnset}`}>
                          {isConfigured ? 'Ready' : 'No Key'}
                        </span>
                      </div>
                      <p className={styles.providerDesc}>{p.desc}</p>
                    </div>
                  );
                })}
              </div>

              {/* Model & Generation Controls */}
              <div className={styles.formGrid}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>
                    <span>Active Model</span>
                    <span className={styles.labelHint}>Engine for {config.chat_provider.toUpperCase()}</span>
                  </label>
                  <select
                    className={styles.select}
                    value={config[`${config.chat_provider}_model`] || ''}
                    onChange={(e) => handleFieldChange(`${config.chat_provider}_model`, e.target.value)}
                  >
                    {(MODEL_PRESETS[config.chat_provider] || []).map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>
                    <span>Temperature</span>
                    <span className={styles.labelHint}>{config.temperature} ({config.temperature <= 0.3 ? 'Deterministic & Precise' : 'Creative'})</span>
                  </label>
                  <div className={styles.rangeWrap}>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      className={styles.rangeInput}
                      value={config.temperature}
                      onChange={(e) => handleFieldChange('temperature', parseFloat(e.target.value))}
                    />
                    <div className={styles.rangeMarkers}>
                      <span>0.0 (Code / Factual)</span>
                      <span>0.5 (Balanced)</span>
                      <span>1.0 (Creative)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* API Keys Configuration Card */}
            <div className={styles.sectionCard}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitleWrap}>
                  <div className={styles.cardIcon}><Key size={20} /></div>
                  <div>
                    <div className={styles.cardTitle}>Custom API Keys</div>
                    <div className={styles.cardSub}>Add your personal API credentials for any supported LLM provider</div>
                  </div>
                </div>
              </div>

              {/* Google Gemini Key */}
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <span>Google Gemini API Key</span>
                  <span className={styles.labelHint}>Get key from Google AI Studio</span>
                </label>
                <div className={styles.inputWrap}>
                  <input
                    type={showKeys.gemini ? 'text' : 'password'}
                    placeholder="AIzaSy..."
                    className={`${styles.input} ${styles.inputWithBtn}`}
                    value={config.gemini_api_key}
                    onChange={(e) => handleFieldChange('gemini_api_key', e.target.value)}
                  />
                  <div className={styles.inputActions}>
                    <button
                      type="button"
                      className={styles.iconToggleBtn}
                      onClick={() => toggleShowKey('gemini')}
                      title="Toggle key visibility"
                    >
                      {showKeys.gemini ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                    <button
                      type="button"
                      className={styles.testBtn}
                      onClick={() => handleTestKey('gemini')}
                      disabled={testState.gemini?.loading}
                    >
                      {testState.gemini?.loading ? <Loader2 size={13} className="spin" /> : <ShieldCheck size={13} />}
                      <span>Test</span>
                    </button>
                  </div>
                </div>
                {testState.gemini?.message && (
                  <div style={{ fontSize: '12px', marginTop: '4px', color: testState.gemini.success ? '#4ade80' : '#f87171' }}>
                    {testState.gemini.message}
                  </div>
                )}
              </div>

              {/* Groq Key */}
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <span>Groq API Key</span>
                  <span className={styles.labelHint}>Get key from console.groq.com</span>
                </label>
                <div className={styles.inputWrap}>
                  <input
                    type={showKeys.groq ? 'text' : 'password'}
                    placeholder="gsk_..."
                    className={`${styles.input} ${styles.inputWithBtn}`}
                    value={config.groq_api_key}
                    onChange={(e) => handleFieldChange('groq_api_key', e.target.value)}
                  />
                  <div className={styles.inputActions}>
                    <button
                      type="button"
                      className={styles.iconToggleBtn}
                      onClick={() => toggleShowKey('groq')}
                    >
                      {showKeys.groq ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                    <button
                      type="button"
                      className={styles.testBtn}
                      onClick={() => handleTestKey('groq')}
                      disabled={testState.groq?.loading}
                    >
                      {testState.groq?.loading ? <Loader2 size={13} className="spin" /> : <ShieldCheck size={13} />}
                      <span>Test</span>
                    </button>
                  </div>
                </div>
                {testState.groq?.message && (
                  <div style={{ fontSize: '12px', marginTop: '4px', color: testState.groq.success ? '#4ade80' : '#f87171' }}>
                    {testState.groq.message}
                  </div>
                )}
              </div>

              {/* OpenAI Key */}
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <span>OpenAI API Key</span>
                  <span className={styles.labelHint}>Get key from platform.openai.com</span>
                </label>
                <div className={styles.inputWrap}>
                  <input
                    type={showKeys.openai ? 'text' : 'password'}
                    placeholder="sk-..."
                    className={`${styles.input} ${styles.inputWithBtn}`}
                    value={config.openai_api_key}
                    onChange={(e) => handleFieldChange('openai_api_key', e.target.value)}
                  />
                  <div className={styles.inputActions}>
                    <button
                      type="button"
                      className={styles.iconToggleBtn}
                      onClick={() => toggleShowKey('openai')}
                    >
                      {showKeys.openai ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                    <button
                      type="button"
                      className={styles.testBtn}
                      onClick={() => handleTestKey('openai')}
                      disabled={testState.openai?.loading}
                    >
                      {testState.openai?.loading ? <Loader2 size={13} className="spin" /> : <ShieldCheck size={13} />}
                      <span>Test</span>
                    </button>
                  </div>
                </div>
                {testState.openai?.message && (
                  <div style={{ fontSize: '12px', marginTop: '4px', color: testState.openai.success ? '#4ade80' : '#f87171' }}>
                    {testState.openai.message}
                  </div>
                )}
              </div>

              {/* Anthropic Key */}
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <span>Anthropic API Key</span>
                  <span className={styles.labelHint}>Get key from console.anthropic.com</span>
                </label>
                <div className={styles.inputWrap}>
                  <input
                    type={showKeys.anthropic ? 'text' : 'password'}
                    placeholder="sk-ant-..."
                    className={`${styles.input} ${styles.inputWithBtn}`}
                    value={config.anthropic_api_key}
                    onChange={(e) => handleFieldChange('anthropic_api_key', e.target.value)}
                  />
                  <div className={styles.inputActions}>
                    <button
                      type="button"
                      className={styles.iconToggleBtn}
                      onClick={() => toggleShowKey('anthropic')}
                    >
                      {showKeys.anthropic ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                    <button
                      type="button"
                      className={styles.testBtn}
                      onClick={() => handleTestKey('anthropic')}
                      disabled={testState.anthropic?.loading}
                    >
                      {testState.anthropic?.loading ? <Loader2 size={13} className="spin" /> : <ShieldCheck size={13} />}
                      <span>Test</span>
                    </button>
                  </div>
                </div>
                {testState.anthropic?.message && (
                  <div style={{ fontSize: '12px', marginTop: '4px', color: testState.anthropic.success ? '#4ade80' : '#f87171' }}>
                    {testState.anthropic.message}
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* TAB 2: RAG & SEARCH ENGINE */}
        {activeTab === 'retrieval' && (
          <div className={styles.sectionCard}>
            <div className={styles.cardHeader}>
              <div className={styles.cardTitleWrap}>
                <div className={styles.cardIcon}><Search size={20} /></div>
                <div>
                  <div className={styles.cardTitle}>Retrieval & RAG Pipeline</div>
                  <div className={styles.cardSub}>Fine-tune hybrid search, neural reranking, and citation depth</div>
                </div>
              </div>
            </div>

            {/* Neural Cross-Encoder Reranker Toggle */}
            <div className={styles.toggleRow}>
              <div className={styles.toggleInfo}>
                <span className={styles.toggleLabel}>Neural Cross-Encoder Reranking</span>
                <span className={styles.toggleSub}>Applies deep cross-attention to score retrieved candidates before LLM ingestion</span>
              </div>
              <label className={styles.switch}>
                <input
                  type="checkbox"
                  checked={config.rerank_enabled}
                  onChange={(e) => handleFieldChange('rerank_enabled', e.target.checked)}
                />
                <span className={styles.slider} />
              </label>
            </div>

            <div className={styles.formGrid} style={{ marginTop: '16px' }}>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <span>Top-K Sources Retrieved</span>
                  <span className={styles.labelHint}>{config.top_k} code snippets</span>
                </label>
                <div className={styles.rangeWrap}>
                  <input
                    type="range"
                    min="2"
                    max="10"
                    step="1"
                    className={styles.rangeInput}
                    value={config.top_k}
                    onChange={(e) => handleFieldChange('top_k', parseInt(e.target.value, 10))}
                  />
                  <div className={styles.rangeMarkers}>
                    <span>2 (Concise)</span>
                    <span>5 (Default)</span>
                    <span>10 (Comprehensive)</span>
                  </div>
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <span>Assistant Persona</span>
                  <span className={styles.labelHint}>Formatting style</span>
                </label>
                <select
                  className={styles.select}
                  value={config.system_prompt_mode}
                  onChange={(e) => handleFieldChange('system_prompt_mode', e.target.value)}
                >
                  <option value="default">Standard Code Architect (Balanced)</option>
                  <option value="concise">Concise Technical Lead (Short & Direct)</option>
                  <option value="deep">Deep Code Auditor (Comprehensive Explanations)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: INDEX & STORAGE */}
        {activeTab === 'storage' && (
          <>
            <div className={styles.sectionCard}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitleWrap}>
                  <div className={styles.cardIcon}><Layers size={20} /></div>
                  <div>
                    <div className={styles.cardTitle}>Document Ingestion & Chunking</div>
                    <div className={styles.cardSub}>Tune text segmentation parameters for AST and generic parsing</div>
                  </div>
                </div>
              </div>

              <div className={styles.formGrid}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>
                    <span>Chunk Size (characters)</span>
                    <span className={styles.labelHint}>{config.chunk_size} chars</span>
                  </label>
                  <input
                    type="number"
                    min="300"
                    max="3000"
                    step="100"
                    className={styles.input}
                    value={config.chunk_size}
                    onChange={(e) => handleFieldChange('chunk_size', parseInt(e.target.value, 10) || 1000)}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>
                    <span>Chunk Overlap (characters)</span>
                    <span className={styles.labelHint}>{config.chunk_overlap} chars</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="500"
                    step="50"
                    className={styles.input}
                    value={config.chunk_overlap}
                    onChange={(e) => handleFieldChange('chunk_overlap', parseInt(e.target.value, 10) || 200)}
                  />
                </div>
              </div>
            </div>

            {/* Danger Zone */}
            <div className={styles.dangerCard}>
              <div className={styles.dangerTitle}>Danger Zone</div>
              <p className={styles.pageSub} style={{ marginBottom: '16px' }}>
                Reset the index and delete all indexed repositories and files from vector storage.
              </p>
              <button
                className={styles.dangerBtn}
                onClick={handleClearIndex}
                disabled={clearing}
              >
                {clearing ? 'Clearing Index...' : 'Clear Knowledge Base Index'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
