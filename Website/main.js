const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const chatView = document.querySelector('#chat-view');
const sendButton = document.querySelector('#send-button');
const voiceButton = document.querySelector('#voice-button');
const connection = document.querySelector('#connection');
const connectionStatus = document.querySelector('#connection-status');
const assistantState = document.querySelector('#assistant-state');
const stageMessage = document.querySelector('#stage-message');
const speechToggle = document.querySelector('#speech-toggle');
const voiceProfile = document.querySelector('#voice-profile');
const voiceStatus = document.querySelector('#voice-status');
const appShell = document.querySelector('#app-shell');
const siriStage = document.querySelector('#siri-wave');
const siriMessage = document.querySelector('#siri-message');
const template = document.querySelector('#message-template');

let recognition;
let recognitionRunning = false;
let waitingForCommand = false;
let processingCommand = false;
let wakeWordEnabled = true;
let voiceRepliesEnabled = true;
let selectedVoiceProfile = localStorage.getItem('friday-voice-profile') || 'female';
let restartTimer;

voiceProfile.value = selectedVoiceProfile;

function setStage(state, message) {
  assistantState.textContent = state;
  stageMessage.textContent = message;
}

function showSiri(message = 'What would you like me to do?') {
  siriMessage.textContent = message;
  appShell.classList.add('siri-active');
  siriStage.hidden = false;
}

function hideSiri() {
  appShell.classList.remove('siri-active');
  siriStage.hidden = true;
}

function addMessage(speaker, text, type = 'friday') {
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(`${type}-message`);
  node.querySelector('.message-mark').textContent = type === 'user' ? 'Y' : 'F';
  node.querySelector('.speaker').textContent = speaker.toUpperCase();
  node.querySelector('.bubble').textContent = text;
  chatView.append(node);
  chatView.scrollTop = chatView.scrollHeight;
  return node;
}

function scheduleRecognition(delay = 250) {
  clearTimeout(restartTimer);
  if (!recognition || !wakeWordEnabled || processingCommand || recognitionRunning) return;
  restartTimer = setTimeout(() => {
    try { recognition.start(); } catch { /* A browser may still be closing the previous recognition session. */ }
  }, delay);
}

function returnToWakeMode() {
  waitingForCommand = false;
  hideSiri();
  setStage('ready', 'Say “Hello Friday” to wake me, or type a message below.');
  voiceStatus.textContent = wakeWordEnabled ? 'Listening for “Hello Friday”…' : 'Wake-word listening is paused.';
  scheduleRecognition(350);
}

function speakReply(text) {
  if (!voiceRepliesEnabled || !('speechSynthesis' in window) || !text) {
    returnToWakeMode();
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  const voices = window.speechSynthesis.getVoices();
  const language = /[\u0900-\u097F]/.test(text) ? 'hi' : 'en';
  const femaleNames = /zira|samantha|victoria|karen|moira|ava|aria|jenny|susan|female/i;
  const maleNames = /alex|daniel|david|fred|george|james|microsoft mark|male/i;
  const profileNames = selectedVoiceProfile === 'female' ? femaleNames : maleNames;
  // Browsers do not expose a gender field. Prefer locally installed voices with
  // familiar voice names, then safely fall back to the reply language.
  utterance.voice = voices.find(voice => voice.lang.toLowerCase().startsWith(language) && profileNames.test(voice.name))
    || voices.find(voice => voice.lang.toLowerCase().startsWith(language))
    || voices.find(voice => profileNames.test(voice.name))
    || null;
  utterance.lang = utterance.voice?.lang || (language === 'hi' ? 'hi-IN' : navigator.language || 'en-US');
  utterance.onstart = () => { setStage('speaking', 'Friday is replying through your speakers.'); voiceStatus.textContent = 'Friday is speaking…'; };
  utterance.onend = returnToWakeMode;
  utterance.onerror = returnToWakeMode;
  window.speechSynthesis.speak(utterance);
}

async function checkStatus() {
  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw new Error('Unavailable');
    const data = await response.json();
    connection.classList.add('online');
    connectionStatus.textContent = `${data.name || 'Friday'} online`;
  } catch {
    connection.classList.remove('online');
    connectionStatus.textContent = 'Server offline';
  }
}

async function sendMessage(message) {
  if (!message || processingCommand) return;
  processingCommand = true;
  waitingForCommand = false;
  clearTimeout(restartTimer);
  if (recognitionRunning) recognition.stop();
  window.speechSynthesis?.cancel();
  hideSiri();
  addMessage('You', message, 'user');
  input.value = '';
  sendButton.disabled = true;
  setStage('thinking', 'Friday is working on that…');
  const typing = addMessage('Friday', 'Friday is thinking…');
  typing.classList.add('typing');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message}) });
    const data = await response.json();
    typing.remove();
    const reply = data.reply || data.error || 'Something went wrong.';
    addMessage('Friday', reply);
    processingCommand = false;
    if (data.reply) speakReply(reply); else returnToWakeMode();
  } catch {
    typing.remove();
    addMessage('Friday', 'I can’t reach the Friday server. Start it with: python3 web_server.py');
    processingCommand = false;
    setStage('offline', 'Start the local Friday server to use commands.');
    checkStatus();
    returnToWakeMode();
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

function wakeFriday(transcript) {
  const wakePattern = /\b(?:hello|hey)\s+friday\b/i;
  const match = transcript.match(wakePattern);
  if (!match) return false;
  const command = transcript.slice((match.index || 0) + match[0].length).replace(/^[,!.?\s]+/, '').trim();
  waitingForCommand = true;
  showSiri(command ? 'I heard your command.' : 'What would you like me to do?');
  voiceStatus.textContent = command ? 'Sending your command…' : 'Friday is listening for your command…';
  if (command) sendMessage(command);
  return true;
}

function setupSpeechRecognition() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    voiceButton.disabled = true;
    voiceButton.title = 'Speech input is supported in Chrome and Edge';
    voiceStatus.textContent = 'Wake-word listening works in Chrome or Edge.';
    return;
  }
  recognition = new Recognition();
  recognition.lang = navigator.language || 'en-US';
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onstart = () => {
    recognitionRunning = true;
    voiceButton.classList.add('listening');
    voiceButton.classList.remove('paused');
    if (waitingForCommand) {
      showSiri('What would you like me to do?');
      voiceStatus.textContent = 'Friday is listening for your command…';
    } else {
      voiceStatus.textContent = 'Listening for “Hello Friday”…';
    }
  };
  recognition.onresult = event => {
    const transcript = event.results[event.results.length - 1][0].transcript.trim();
    if (waitingForCommand) {
      if (transcript) sendMessage(transcript);
      return;
    }
    wakeFriday(transcript);
  };
  recognition.onerror = event => {
    recognitionRunning = false;
    voiceButton.classList.remove('listening');
    if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
      wakeWordEnabled = false;
      voiceButton.setAttribute('aria-pressed', 'false');
      voiceButton.classList.add('paused');
      voiceStatus.textContent = 'Allow microphone access once, then tap the microphone to enable wake-word listening.';
      return;
    }
    if (event.error !== 'no-speech' && event.error !== 'aborted') voiceStatus.textContent = `Speech input error: ${event.error}. Retrying…`;
  };
  recognition.onend = () => {
    recognitionRunning = false;
    voiceButton.classList.remove('listening');
    if (wakeWordEnabled && !processingCommand) scheduleRecognition(waitingForCommand ? 120 : 300);
  };
  scheduleRecognition(500);
}

form.addEventListener('submit', event => { event.preventDefault(); sendMessage(input.value.trim()); });
voiceButton.addEventListener('click', () => {
  if (!recognition) return;
  wakeWordEnabled = !wakeWordEnabled;
  voiceButton.setAttribute('aria-pressed', String(wakeWordEnabled));
  voiceButton.classList.toggle('paused', !wakeWordEnabled);
  if (!wakeWordEnabled) {
    clearTimeout(restartTimer);
    recognition.stop();
    waitingForCommand = false;
    hideSiri();
    voiceStatus.textContent = 'Wake-word listening is paused.';
  } else {
    voiceStatus.textContent = 'Starting wake-word listening…';
    scheduleRecognition(0);
  }
});
document.querySelector('#quick-actions').addEventListener('click', event => { if (event.target.matches('button')) sendMessage(event.target.dataset.prompt); });
document.querySelector('#new-chat').addEventListener('click', () => { window.speechSynthesis?.cancel(); chatView.innerHTML = ''; addMessage('Friday', 'New conversation started. What would you like to do?'); processingCommand = false; returnToWakeMode(); input.focus(); });
speechToggle.addEventListener('click', () => { voiceRepliesEnabled = !voiceRepliesEnabled; speechToggle.setAttribute('aria-pressed', String(voiceRepliesEnabled)); speechToggle.textContent = voiceRepliesEnabled ? 'Voice replies: On' : 'Voice replies: Off'; if (!voiceRepliesEnabled) window.speechSynthesis?.cancel(); });
voiceProfile.addEventListener('change', () => {
  selectedVoiceProfile = voiceProfile.value;
  localStorage.setItem('friday-voice-profile', selectedVoiceProfile);
  voiceStatus.textContent = `${selectedVoiceProfile[0].toUpperCase()}${selectedVoiceProfile.slice(1)} voice selected.`;
  window.speechSynthesis?.cancel();
});
setupSpeechRecognition();
checkStatus();
