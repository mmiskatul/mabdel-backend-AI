const state = {
  token: "",
  socket: null,
  sessionId: null,
  recognition: null,
  isListening: false,
};

const qs = {
  authType: document.getElementById("authType"),
  autoSpeak: document.getElementById("autoSpeak"),
  email: document.getElementById("email"),
  password: document.getElementById("password"),
  token: document.getElementById("token"),
  loginButton: document.getElementById("loginButton"),
  connectButton: document.getElementById("connectButton"),
  disconnectButton: document.getElementById("disconnectButton"),
  sessionId: document.getElementById("sessionId"),
  socketState: document.getElementById("socketState"),
  stageText: document.getElementById("stageText"),
  messageInput: document.getElementById("messageInput"),
  sendButton: document.getElementById("sendButton"),
  listenButton: document.getElementById("listenButton"),
  stopSpeakButton: document.getElementById("stopSpeakButton"),
  messages: document.getElementById("messages"),
  log: document.getElementById("log"),
};

function log(message, data) {
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  qs.log.textContent += data ? `${line}\n${JSON.stringify(data, null, 2)}\n\n` : `${line}\n`;
  qs.log.scrollTop = qs.log.scrollHeight;
}

function renderMessage(role, text) {
  const node = document.createElement("article");
  node.className = `message ${role}`;
  node.innerHTML = `<small>${role}</small><div>${text}</div>`;
  qs.messages.appendChild(node);
  qs.messages.scrollTop = qs.messages.scrollHeight;
}

function setListening(active) {
  state.isListening = active;
  qs.listenButton.classList.toggle("is-listening", active);
  qs.stageText.textContent = active ? "listening" : qs.stageText.textContent;
}

function autosizeComposer() {
  qs.messageInput.style.height = "auto";
  qs.messageInput.style.height = `${Math.min(qs.messageInput.scrollHeight, 160)}px`;
}

async function login() {
  const authType = qs.authType.value;
  const payload = {
    email: qs.email.value.trim(),
    password: qs.password.value,
  };
  const response = await fetch(`/api/v1/auth/${authType}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    log("Login failed", data);
    alert(data.detail || "Login failed");
    return;
  }
  state.token = data.access_token;
  qs.token.value = data.access_token;
  log("Login successful", { authType });
  renderMessage("system", `${authType} authenticated. Connect the socket to start the session.`);
}

function getSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1/agent/ws/new?token=${encodeURIComponent(state.token)}`;
}

function connectSocket() {
  if (!state.token) {
    alert("Login first.");
    return;
  }
  if (state.socket && state.socket.readyState <= 1) {
    return;
  }

  state.socket = new WebSocket(getSocketUrl());
  qs.socketState.textContent = "connecting";
  qs.stageText.textContent = "connecting";

  state.socket.onopen = () => {
    qs.socketState.textContent = "open";
    qs.stageText.textContent = "connected";
    log("Socket connected");
  };

  state.socket.onclose = () => {
    qs.socketState.textContent = "closed";
    qs.stageText.textContent = "idle";
    log("Socket closed");
  };

  state.socket.onerror = () => {
    qs.socketState.textContent = "error";
    qs.stageText.textContent = "error";
    log("Socket error");
  };

  state.socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    log("Socket event", payload);
    if (payload.type === "session_ready") {
      state.sessionId = payload.session_id;
      qs.sessionId.textContent = payload.session_id;
      qs.stageText.textContent = "ready";
      renderMessage("system", `Session ready: ${payload.session_id}`);
      return;
    }
    if (payload.type === "agent_status") {
      qs.stageText.textContent = payload.stage || "processing";
      renderMessage("system", `Agent status: ${payload.stage}`);
      return;
    }
    if (payload.type === "assistant_message") {
      qs.stageText.textContent = "responded";
      renderMessage("assistant", payload.text || "");
      if (qs.autoSpeak.value === "on" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(new SpeechSynthesisUtterance(payload.text || ""));
      }
      return;
    }
    if (payload.type === "error") {
      qs.stageText.textContent = "error";
      renderMessage("system", payload.detail || "Unknown error");
    }
  };
}

function disconnectSocket() {
  if (state.socket) {
    state.socket.close();
    state.socket = null;
  }
  qs.stageText.textContent = "idle";
  qs.sessionId.textContent = "not connected";
}

function sendMessage() {
  const text = qs.messageInput.value.trim();
  if (!text) {
    return;
  }
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    alert("Connect the socket first.");
    return;
  }
  state.socket.send(JSON.stringify({ type: "user_message", text }));
  qs.stageText.textContent = "sending";
  renderMessage("user", text);
  qs.messageInput.value = "";
  autosizeComposer();
}

function startListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser.");
    return;
  }
  if (!state.recognition) {
    state.recognition = new SpeechRecognition();
    state.recognition.lang = "en-US";
    state.recognition.continuous = false;
    state.recognition.interimResults = false;
    state.recognition.onstart = () => {
      setListening(true);
      log("Speech recognition started");
    };
    state.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      qs.messageInput.value = transcript;
      autosizeComposer();
      log("Speech captured", { transcript });
      sendMessage();
    };
    state.recognition.onerror = (event) => {
      setListening(false);
      qs.stageText.textContent = "error";
      log("Speech recognition error", event);
    };
    state.recognition.onend = () => {
      setListening(false);
      if (qs.stageText.textContent === "listening") {
        qs.stageText.textContent = "idle";
      }
    };
  }
  state.recognition.start();
}

qs.loginButton.addEventListener("click", login);
qs.connectButton.addEventListener("click", connectSocket);
qs.disconnectButton.addEventListener("click", disconnectSocket);
qs.sendButton.addEventListener("click", sendMessage);
qs.listenButton.addEventListener("click", startListening);
qs.stopSpeakButton.addEventListener("click", () => {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
});

qs.messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

qs.messageInput.addEventListener("input", autosizeComposer);

renderMessage("system", "Login, connect the socket, then speak with the mic or type a message below.");
autosizeComposer();
