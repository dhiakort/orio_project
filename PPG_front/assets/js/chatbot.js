/**
 * ═══════════════════════════════════════════════════════════════════
 *  ORIO — Assistant Chatbot
 *  • Moteur principal  : Grok (xAI) via API REST
 *  • Moteur de secours : Backend ORIO (/scoring/chatbot/) → Gemini fallback
 *  • Speech API        : Web Speech API (dictée vocale pour les élèves)
 * ═══════════════════════════════════════════════════════════════════
 */

// ── Configuration ────────────────────────────────────────────────
const GROK_API_URL = 'https://api.x.ai/v1/chat/completions';
const GROK_API_KEY = 'xai-REMPLACEZ-PAR-VOTRE-CLE-GROK'; // ⚠️ Remplacez par votre clé xAI
const GROK_MODEL   = 'grok-3-mini';  // ou 'grok-3' pour la version complète

// Contexte système pour Grok — spécifique à ORIO
const SYSTEM_PROMPT = `Tu es l'assistant IA d'ORIO (Orientation et Roadmap pour Innovateurs en Orientation), 
une plateforme d'orientation scolaire et professionnelle pour les élèves algériens.

Ton rôle est d'aider les élèves à :
- Comprendre et suivre leur roadmap personnalisée
- Trouver la filière universitaire qui leur correspond
- Découvrir des métiers adaptés à leur profil (RIASEC, Big Five)
- Se préparer aux examens (bac, concours)
- Connaître le système éducatif algérien (lycée → université → grandes écoles)

Sois bienveillant, encourageant et pédagogique. Réponds toujours en français.
Utilise des emojis avec modération pour rendre la conversation plus agréable.
Si une question n'est pas liée à l'orientation ou aux études, réponds quand même de façon utile.`;

// ── Historique de conversation ────────────────────────────────────
const MAX_HISTORY = 20; // messages max gardés en mémoire
let conversationHistory = [];

// ── État du moteur actif ──────────────────────────────────────────
let activeEngine = 'grok'; // 'grok' | 'fallback'

// ── Éléments DOM ─────────────────────────────────────────────────
let messagesEl, questionEl, sendBtn, voiceBtn, engineBadge, engineLabel,
    statusLabel, voiceStatus, voiceHintText, emptyState, clearBtn, toastEl;

// ── Initialisation ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  requireAuth();

  messagesEl    = document.getElementById('messages');
  questionEl    = document.getElementById('question');
  sendBtn       = document.getElementById('send');
  voiceBtn      = document.getElementById('voiceBtn');
  engineBadge   = document.getElementById('engineBadge');
  engineLabel   = document.getElementById('engineLabel');
  statusLabel   = document.getElementById('statusLabel');
  voiceStatus   = document.getElementById('voiceStatus');
  voiceHintText = document.getElementById('voiceHintText');
  emptyState    = document.getElementById('emptyState');
  clearBtn      = document.getElementById('clearBtn');
  toastEl       = document.getElementById('toast');

  initSpeechAPI();
  initSuggestions();
  initClearBtn();
  loadHistory();

  // Événements
  sendBtn.addEventListener('click', handleSend);
  questionEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  });
  questionEl.addEventListener('input', autoResize);
  questionEl.focus();
});

// ─────────────────────────────────────────────────────────────────
// GESTION D'ENVOI
// ─────────────────────────────────────────────────────────────────
async function handleSend() {
  const text = questionEl.value.trim();
  if (!text || sendBtn.disabled) return;

  hideEmptyState();
  appendUserMessage(text);
  questionEl.value = '';
  autoResize();
  sendBtn.disabled = true;

  const thinkingEl = appendThinking();

  try {
    let answer, engine;

    // 1) Essaie Grok en premier
    if (GROK_API_KEY && !GROK_API_KEY.includes('REMPLACEZ')) {
      try {
        answer = await callGrok(text);
        engine = 'grok';
      } catch (grokErr) {
        console.warn('[Chatbot] Grok indisponible, bascule sur fallback:', grokErr.message);
        setEngine('fallback');
        answer = await callFallback(text);
        engine = 'fallback';
      }
    } else {
      // Clé Grok non configurée → fallback direct
      setEngine('fallback');
      answer = await callFallback(text);
      engine = 'fallback';
    }

    removeThinking(thinkingEl);
    appendBotMessage(answer, engine);

    // Ajouter à l'historique
    conversationHistory.push({ role: 'user', content: text });
    conversationHistory.push({ role: 'assistant', content: answer });
    if (conversationHistory.length > MAX_HISTORY * 2) {
      conversationHistory = conversationHistory.slice(-MAX_HISTORY * 2);
    }
    saveHistory();

  } catch (err) {
    removeThinking(thinkingEl);
    appendErrorMessage('❌ Une erreur est survenue : ' + err.message);
  } finally {
    sendBtn.disabled = false;
    questionEl.focus();
  }
}

// ─────────────────────────────────────────────────────────────────
// MOTEUR 1 : GROK (xAI)
// ─────────────────────────────────────────────────────────────────
async function callGrok(userMessage) {
  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    ...conversationHistory.slice(-MAX_HISTORY * 2),
    { role: 'user', content: userMessage }
  ];

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout

  try {
    const res = await fetch(GROK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GROK_API_KEY}`
      },
      body: JSON.stringify({
        model: GROK_MODEL,
        messages,
        temperature: 0.7,
        max_tokens: 1024,
        stream: false
      }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error?.message || `Grok HTTP ${res.status}`);
    }

    const data = await res.json();
    const content = data?.choices?.[0]?.message?.content;
    if (!content) throw new Error('Réponse Grok vide');

    setEngine('grok');
    return content.trim();

  } catch (err) {
    clearTimeout(timeout);
    throw err;
  }
}

// ─────────────────────────────────────────────────────────────────
// MOTEUR 2 : BACKEND ORIO (fallback)
// ─────────────────────────────────────────────────────────────────
async function callFallback(userMessage) {
  // D'abord tente le backend ORIO
  try {
    const res = await apiFetch('/scoring/chatbot/', {
      method: 'POST',
      body: JSON.stringify({ question: userMessage })
    });

    if (!res) throw new Error('Session expirée');

    const contentType = res.headers.get('content-type') || '';

    if (!res.ok) {
      let msg;
      try {
        const d = contentType.includes('json') ? await res.json() : {};
        msg = d.error || d.message || `Erreur ${res.status}`;
      } catch { msg = `Erreur serveur ${res.status}`; }
      throw new Error(msg);
    }

    const data = await res.json();

    // Format flexible : { answer } ou { matches } ou { response }
    if (data.answer?.trim())    return data.answer.trim();
    if (data.response?.trim())  return data.response.trim();
    if (data.matches?.length) {
      return data.matches.map(m => {
        let txt = `📍 **Étape ${m.etape}** : ${m.titre}`;
        if (m.description) txt += `\n${m.description}`;
        if (m.actions?.length) txt += '\n\n✅ Actions :\n' + m.actions.map((a, i) => `${i+1}. ${a}`).join('\n');
        return txt;
      }).join('\n\n---\n\n');
    }

    throw new Error('Réponse backend vide');

  } catch (backendErr) {
    console.warn('[Chatbot] Backend indisponible, utilisation de la réponse locale:', backendErr.message);
    // Dernier recours : réponse intelligente locale
    return localFallbackAnswer(userMessage);
  }
}

// ─────────────────────────────────────────────────────────────────
// MOTEUR 3 : RÉPONSES LOCALES (dernier recours)
// ─────────────────────────────────────────────────────────────────
function localFallbackAnswer(question) {
  const q = question.toLowerCase();
  const user = getUser();
  const name = user?.first_name ? `, **${user.first_name}**` : '';

  const responses = [
    {
      keywords: ['roadmap', 'étape', 'plan', 'prochaine'],
      answer: `📍 Pour consulter votre roadmap personnalisée${name}, rendez-vous dans la section **Roadmap** de votre tableau de bord.\n\nVotre roadmap est construite sur la base de vos résultats aux tests RIASEC et Big Five. Elle vous guide étape par étape vers votre orientation idéale.`
    },
    {
      keywords: ['riasec', 'test', 'profil', 'intérêt'],
      answer: `🎯 Le test **RIASEC** évalue vos intérêts professionnels selon 6 dimensions :\n\n• **R** – Réaliste (travail manuel)\n• **I** – Investigateur (recherche, sciences)\n• **A** – Artistique (créativité)\n• **S** – Social (aide, enseignement)\n• **E** – Entreprenant (leadership)\n• **C** – Conventionnel (organisation)\n\nVos résultats vous aident à trouver la filière qui vous correspond vraiment ! 🎓`
    },
    {
      keywords: ['bac', 'examen', 'préparer', 'révision'],
      answer: `📚 Conseils pour se préparer au bac${name} :\n\n1. **Planifiez** votre révision avec un emploi du temps réaliste\n2. **Priorisez** les matières coefficientées\n3. **Faites des annales** des années précédentes\n4. **Dormez suffisamment** — le cerveau consolide les souvenirs pendant le sommeil\n5. **Évitez le bachotage** la veille — relisez juste vos fiches\n\n💪 Vous êtes capable d'y arriver !`
    },
    {
      keywords: ['filière', 'université', 'choisir', 'orientation'],
      answer: `🏛️ Pour choisir votre filière universitaire en Algérie${name}, considérez :\n\n• **Vos intérêts** (résultats RIASEC et Big Five)\n• **Vos notes** par matière au bac\n• **Les débouchés** professionnels de la filière\n• **La proximité** des établissements\n\n🔹 Filières populaires : Médecine, Informatique, Droit, Sciences économiques, Génie civil, Architecture...\n\nConsultez votre roadmap ORIO pour une recommandation personnalisée !`
    },
    {
      keywords: ['compétence', 'améliorer', 'progresser', 'apprendre'],
      answer: `📈 Pour améliorer vos compétences${name} :\n\n• **Régularité** > intensité : 30 min/jour vaut mieux que 4h le week-end\n• **Pratique active** : exercices, projets concrets\n• **Demandez de l'aide** : professeurs, camarades, tutoriels en ligne\n• **Suivez votre progression** dans ORIO via la section Compétences\n\n🌟 Chaque effort compte !`
    },
    {
      keywords: ['inscription', 'préinscription', 'progres', 'université algérie'],
      answer: `📋 Le processus d'inscription universitaire en Algérie :\n\n1. Obtenir le bac\n2. Se pré-inscrire sur **progres.mesrs.dz** (portail officiel)\n3. Choisir vos vœux de filières par ordre de préférence\n4. Attendre l'orientation automatique basée sur votre moyenne et vos choix\n5. Confirmer votre inscription à l'université assignée\n\n📅 Les délais varient chaque année — suivez l'actualité du Ministère de l'Enseignement Supérieur.`
    }
  ];

  for (const r of responses) {
    if (r.keywords.some(kw => q.includes(kw))) {
      return r.answer;
    }
  }

  return `🤖 Je suis l'assistant ORIO${name}. Je suis actuellement en **mode hors ligne** car les serveurs sont temporairement indisponibles.\n\nVoici ce que je peux vous aider à faire normalement :\n• 📍 Consulter votre roadmap personnalisée\n• 🎯 Analyser votre profil RIASEC\n• 🎓 Choisir une filière universitaire\n• 📚 Préparer vos examens\n\nVeuillez réessayer dans quelques instants lorsque la connexion sera rétablie.`;
}

// ─────────────────────────────────────────────────────────────────
// WEB SPEECH API (DICTÉE VOCALE)
// ─────────────────────────────────────────────────────────────────
let recognition = null;
let isListening = false;

function initSpeechAPI() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    voiceBtn.classList.add('no-support');
    voiceBtn.title = 'La reconnaissance vocale n\'est pas supportée par ce navigateur. Utilisez Chrome.';
    voiceHintText.textContent = 'Dictée non disponible (utilisez Chrome ou Edge)';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = 'fr-FR';
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  let finalTranscript = '';
  let interimTranscript = '';

  recognition.onstart = () => {
    isListening = true;
    voiceBtn.classList.add('listening');
    voiceBtn.title = 'Cliquez pour arrêter la dictée';
    voiceStatus.textContent = '🔴 Écoute en cours…';
    voiceStatus.classList.add('active');
    voiceHintText.style.display = 'none';
    finalTranscript = questionEl.value.trim();
    showToast('🎤 Dictée activée — parlez maintenant…', '');
  };

  recognition.onresult = (event) => {
    interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalTranscript += (finalTranscript ? ' ' : '') + t;
      else interimTranscript += t;
    }
    questionEl.value = finalTranscript + (interimTranscript ? ' ' + interimTranscript : '');
    autoResize();
  };

  recognition.onerror = (event) => {
    const msgs = {
      'no-speech':     'Aucune parole détectée. Réessayez.',
      'audio-capture': 'Microphone introuvable. Vérifiez votre micro.',
      'not-allowed':   'Permission refusée. Autorisez le microphone dans votre navigateur.',
      'network':       'Problème réseau pour la reconnaissance vocale.',
    };
    showToast('❌ ' + (msgs[event.error] || 'Erreur microphone : ' + event.error), 'error');
    stopListening();
  };

  recognition.onend = () => {
    stopListening();
    if (finalTranscript.trim()) {
      questionEl.value = finalTranscript.trim();
      autoResize();
      showToast('✅ Dictée terminée !', 'success');
    }
  };

  voiceBtn.addEventListener('click', toggleVoice);
}

function toggleVoice() {
  if (voiceBtn.classList.contains('no-support')) return;
  if (isListening) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

function stopListening() {
  isListening = false;
  voiceBtn.classList.remove('listening');
  voiceBtn.title = 'Dicter votre question (pour les élèves en difficulté d\'écriture)';
  voiceStatus.textContent = '';
  voiceStatus.classList.remove('active');
  voiceHintText.style.display = '';
}

// ─────────────────────────────────────────────────────────────────
// UI HELPERS
// ─────────────────────────────────────────────────────────────────
function getTimeString() {
  return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

function hideEmptyState() {
  if (emptyState) {
    emptyState.style.animation = 'fadeOut 0.3s ease forwards';
    setTimeout(() => emptyState.remove(), 300);
    emptyState = null;
  }
}

function appendUserMessage(text) {
  const user = getUser();
  const initial = user?.first_name ? user.first_name[0].toUpperCase() : 'U';
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `
    <div class="msg-row">
      <div class="msg-avatar">${initial}</div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
    </div>
    <div class="msg-meta" style="justify-content:flex-end;padding-right:42px;">
      <span class="msg-time">${getTimeString()}</span>
    </div>`;
  messagesEl.appendChild(div);
  scrollDown();
}

function appendBotMessage(text, engine = 'grok') {
  const div = document.createElement('div');
  div.className = 'msg bot';
  const engineTag = engine === 'grok'
    ? '<span class="msg-engine">Grok AI</span>'
    : '<span class="msg-engine fallback">⚡ Fallback</span>';

  div.innerHTML = `
    <div class="msg-row">
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">${formatMarkdown(text)}</div>
    </div>
    <div class="msg-meta" style="padding-left:42px;">
      <span class="msg-time">${getTimeString()}</span>
      ${engineTag}
    </div>`;
  messagesEl.appendChild(div);
  scrollDown();
}

function appendErrorMessage(text) {
  const div = document.createElement('div');
  div.className = 'msg error';
  div.innerHTML = `
    <div class="msg-row">
      <div class="msg-avatar" style="background:rgba(239,68,68,0.2);">⚠️</div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
    </div>
    <div class="msg-meta" style="padding-left:42px;">
      <span class="msg-time">${getTimeString()}</span>
    </div>`;
  messagesEl.appendChild(div);
  scrollDown();
}

function appendThinking() {
  const div = document.createElement('div');
  div.className = 'msg bot thinking';
  div.innerHTML = `
    <div class="msg-row">
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
      </div>
    </div>`;
  messagesEl.appendChild(div);
  scrollDown();
  return div;
}

function removeThinking(el) {
  if (el && el.parentNode) el.remove();
}

function scrollDown() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function autoResize() {
  questionEl.style.height = 'auto';
  questionEl.style.height = Math.min(questionEl.scrollHeight, 140) + 'px';
}

function setEngine(engine) {
  activeEngine = engine;
  if (engine === 'grok') {
    engineBadge.className = 'engine-badge grok';
    engineLabel.textContent = 'Grok AI';
    engineBadge.querySelector('.eng-dot').style.background = '#6366f1';
    statusLabel.textContent = 'En ligne · Grok AI';
  } else {
    engineBadge.className = 'engine-badge fallback';
    engineLabel.textContent = 'Mode Secours';
    engineBadge.querySelector('.eng-dot').style.background = '#fbbf24';
    statusLabel.textContent = 'Mode secours actif';
  }
}

// Formatage Markdown basique → HTML
function formatMarkdown(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="background:rgba(255,255,255,0.1);padding:1px 5px;border-radius:4px;">$1</code>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .replace(/\n---\n/g, '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0;">')
    .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
}

// Toast notification
let _toastTimer;
function showToast(msg, type = '') {
  toastEl.textContent = msg;
  toastEl.className = 'show ' + type;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => toastEl.className = '', 3000);
}

// ─────────────────────────────────────────────────────────────────
// SUGGESTIONS
// ─────────────────────────────────────────────────────────────────
function initSuggestions() {
  document.querySelectorAll('.suggestion-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      questionEl.value = btn.dataset.q;
      autoResize();
      questionEl.focus();
      handleSend();
    });
  });
}

// ─────────────────────────────────────────────────────────────────
// CLEAR CONVERSATION
// ─────────────────────────────────────────────────────────────────
function initClearBtn() {
  clearBtn.addEventListener('click', () => {
    if (!confirm('Effacer toute la conversation ?')) return;
    conversationHistory = [];
    saveHistory();
    messagesEl.innerHTML = '';
    // Re-insert empty state
    const es = document.createElement('div');
    es.id = 'emptyState';
    es.className = 'empty-state';
    es.innerHTML = `
      <div class="empty-state-icon">🧠</div>
      <div class="empty-state-title">Conversation effacée</div>
      <div class="empty-state-sub">Posez une nouvelle question pour commencer.</div>
    `;
    emptyState = es;
    messagesEl.appendChild(es);
    setEngine('grok');
    showToast('🗑️ Conversation effacée', '');
  });
}

// ─────────────────────────────────────────────────────────────────
// PERSISTANCE (localStorage)
// ─────────────────────────────────────────────────────────────────
const HISTORY_KEY = 'orio_chat_history';
const MAX_PERSISTED = 40; // messages max sauvegardés

function saveHistory() {
  try {
    const toSave = conversationHistory.slice(-MAX_PERSISTED);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(toSave));
  } catch (e) { /* ignore quota errors */ }
}

function loadHistory() {
  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (!stored) return;
    const hist = JSON.parse(stored);
    if (!Array.isArray(hist) || hist.length === 0) return;

    conversationHistory = hist;

    // Affiche les messages précédents dans l'UI
    hideEmptyState();
    hist.forEach(msg => {
      if (msg.role === 'user') appendUserMessage(msg.content);
      else if (msg.role === 'assistant') appendBotMessage(msg.content, 'grok');
    });

    // Ajouter un séparateur de session
    const sep = document.createElement('div');
    sep.style.cssText = 'text-align:center;font-size:11px;color:rgba(255,255,255,0.2);padding:8px 0;';
    sep.textContent = '── Nouvelle session ──';
    messagesEl.appendChild(sep);
    scrollDown();
  } catch (e) {
    localStorage.removeItem(HISTORY_KEY);
  }
}