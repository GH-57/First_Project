document.addEventListener("DOMContentLoaded", () => {
  // 화면 요소
  const loginScreen = document.getElementById("login-screen");
  const signupScreen = document.getElementById("signup-screen");
  const chatScreen = document.getElementById("chat-screen");
  const screens = [loginScreen, signupScreen, chatScreen];

  // 폼 요소
  const loginForm = document.getElementById("login-form");
  const signupForm = document.getElementById("signup-form");
  const messageForm = document.getElementById("message-form");

  // 채팅 관련 요소
  const messageInput = document.getElementById("message-input");
  const messageDisplay = document.getElementById("message-display");
  const chatWindow = document.querySelector(".chat-window");
  // ▼▼▼ 전송 버튼을 제어하기 위해 요소를 가져옵니다. ▼▼▼
  const submitButton = messageForm.querySelector("button");

  // 버튼 및 링크
  const showSignup = document.getElementById("show-signup");
  const showLogin = document.getElementById("show-login");
  const logoutBtn = document.getElementById("logout-btn");

  // 히스토리 모달 관련
  const historyBtn = document.getElementById("history-btn");
  const historyModal = document.getElementById("history-modal");
  const closeBtn = document.querySelector(".close-btn");
  const historyDisplay = document.getElementById("history-display");
  const historyModalTitle = historyModal.querySelector("h2");

  const API_BASE_URL = "http://127.0.0.1:8000";

  // --- 초기화 및 화면 전환 로직 ---

  async function initialize() {
    const token = localStorage.getItem("authToken");
    if (token) {
      showScreen("chat");
      await restoreChatHistory();
    } else {
      showScreen("login");
    }
  }

  function showScreen(screenId) {
    screens.forEach((screen) => screen.classList.remove("active"));
    document.getElementById(`${screenId}-screen`).classList.add("active");
  }

  // --- 이벤트 리스너 ---

  showSignup.addEventListener("click", (e) => {
    e.preventDefault();
    showScreen("signup");
  });
  showLogin.addEventListener("click", (e) => {
    e.preventDefault();
    showScreen("login");
  });

  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("signup-email").value;
    const nickname = document.getElementById("signup-nickname").value;
    const password = document.getElementById("signup-password").value;
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, nickname }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      alert("회원가입 성공! 로그인 페이지로 이동합니다.");
      showScreen("login");
    } catch (error) {
      alert(`회원가입 실패: ${error.message}`);
    }
  });

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      localStorage.setItem("authToken", data.access_token);
      localStorage.setItem("userNickname", data.nickname);

      resetChatWindow();
      await initialize();
    } catch (error) {
      alert(`로그인 실패: ${error.message}`);
    }
  });

  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("userNickname");
    resetChatWindow();
    initialize();
  });

  messageForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const prompt = messageInput.value.trim();
    if (!prompt) return;

    // ▼▼▼ 수정된 부분: 메시지 전송 시작 시 입력창과 버튼을 비활성화 ▼▼▼
    messageInput.disabled = true;
    submitButton.disabled = true;
    submitButton.textContent = "전송 중...";

    displayMessage("user", prompt);
    scrollToBottom();

    const loadingMessage = displayMessage("ai", "답변을 생성 중입니다...");
    loadingMessage.classList.add("loading-message");
    scrollToBottom();

    try {
      const proverbData = await callApi("/chat", "POST", { prompt });
      loadingMessage.querySelector(
        ".message-bubble"
      ).innerHTML = `<p>[${proverbData.verse}] ${proverbData.content}</p><p>${proverbData.comment}</p>`;
      loadingMessage.classList.remove("loading-message");
    } catch (error) {
      console.error("Error:", error);
      loadingMessage.querySelector(".message-bubble p").textContent =
        "오류가 발생했습니다.";
      loadingMessage.classList.remove("loading-message");
    } finally {
      // ▼▼▼ 수정된 부분: API 호출이 성공하든 실패하든, 끝나면 다시 활성화 ▼▼▼
      messageInput.disabled = false;
      submitButton.disabled = false;
      submitButton.textContent = "전송";
      messageInput.value = ""; // 입력창 초기화
      messageInput.focus(); // 사용자가 바로 다음 입력을 할 수 있도록 포커스 이동
      scrollToBottom();
    }
  });

  // --- 히스토리 모달 관련 기능 ---
  historyBtn.addEventListener("click", async () => {
    const nickname = localStorage.getItem("userNickname");
    historyModalTitle.textContent = nickname
      ? `${nickname}님의 대화기록`
      : "나의 대화기록";
    historyModal.classList.add("active");
    await fetchAndDisplayHistoryModal();
  });

  closeBtn.addEventListener("click", () =>
    historyModal.classList.remove("active")
  );
  window.addEventListener("click", (e) => {
    if (e.target == historyModal) historyModal.classList.remove("active");
  });

  async function fetchAndDisplayHistoryModal() {
    historyDisplay.innerHTML = "<p>기록을 불러오는 중입니다...</p>";
    try {
      const historyData = await callApi("/history", "GET");
      if (historyData.length === 0) {
        historyDisplay.innerHTML = "<p>아직 대화 기록이 없습니다.</p>";
        return;
      }
      historyDisplay.innerHTML = "";
      historyData.forEach((item) => {
        const historyItem = document.createElement("div");
        historyItem.className = "history-item";
        const localDate = new Date(item.timestamp).toLocaleString("ko-KR");
        historyItem.innerHTML = `
                    <div class="prompt"><strong>나:</strong> ${item.prompt}</div>
                    <div class="response"><strong>AI:</strong> [${item.response.verse}] ${item.response.content}</div>
                    <div class="timestamp">${localDate}</div>`;
        historyDisplay.appendChild(historyItem);
      });
    } catch (error) {
      historyDisplay.innerHTML = `<p>기록 로딩 실패: ${error.message}</p>`;
    }
  }

  // --- 공통 API 호출 함수 ---
  async function callApi(endpoint, method, body = null) {
    const token = localStorage.getItem("authToken");
    if (!token) throw new Error("로그인이 필요합니다.");
    const headers = { Authorization: `Bearer ${token}` };
    const options = { method, headers };
    if (body) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "API 호출에 실패했습니다.");
    }
    return response.json();
  }

  // --- 메시지 표시 및 창 관리 함수 ---
  function displayMessage(sender, text) {
    const messageContainer = document.createElement("div");
    messageContainer.classList.add("message", `${sender}-message`);
    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble");
    const messageText = document.createElement("p");
    messageText.textContent = text;
    bubble.appendChild(messageText);
    messageContainer.appendChild(bubble);
    messageDisplay.appendChild(messageContainer);
    return messageContainer;
  }

  function resetChatWindow() {
    messageDisplay.innerHTML = `
            <div class="message ai-message">
                <div class="message-bubble">
                    <p>안녕하세요! 오늘 기분은 어떠신가요? 제게 이야기해주시면, 당신을 위한 잠언 말씀을 찾아드릴게요.</p>
                </div>
            </div>`;
  }

  async function restoreChatHistory() {
    try {
      const historyData = await callApi("/history", "GET");
      if (historyData.length === 0) {
        resetChatWindow();
        return;
      }
      messageDisplay.innerHTML = "";
      historyData.forEach((item) => {
        displayMessage("user", item.prompt);
        const aiMessageContainer = displayMessage("ai", "");
        aiMessageContainer.querySelector(
          ".message-bubble"
        ).innerHTML = `<p>[${item.response.verse}] ${item.response.content}</p><p>${item.response.comment}</p>`;
      });
      setTimeout(() => {
        scrollToBottom(true);
      }, 0);
    } catch (error) {
      console.error("기록 복원 실패:", error);
      resetChatWindow();
    }
  }

  function scrollToBottom(isInstant = false) {
    const behavior = isInstant ? "instant" : "smooth";
    chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: behavior });
  }

  // 앱 시작
  initialize();
});
