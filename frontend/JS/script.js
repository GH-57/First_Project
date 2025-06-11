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

  // 버튼 및 링크
  const showSignup = document.getElementById("show-signup");
  const showLogin = document.getElementById("show-login");
  const logoutBtn = document.getElementById("logout-btn");

  // 히스토리 모달 관련
  const historyBtn = document.getElementById("history-btn");
  const historyModal = document.getElementById("history-modal");
  const closeBtn = document.querySelector(".close-btn");
  const historyDisplay = document.getElementById("history-display");

  const API_BASE_URL = "http://127.0.0.1:8000";

  // --- 초기화 및 화면 전환 로직 ---

  // 페이지 로드 시 토큰 확인 및 화면 전환
  function initialize() {
    const token = localStorage.getItem("authToken");
    if (token) {
      showScreen("chat");
    } else {
      showScreen("login");
    }
  }

  function showScreen(screenId) {
    screens.forEach((screen) => {
      screen.classList.remove("active");
    });
    document.getElementById(`${screenId}-screen`).classList.add("active");
  }

  // --- 이벤트 리스너 ---

  // 회원가입 화면으로 전환
  showSignup.addEventListener("click", (e) => {
    e.preventDefault();
    showScreen("signup");
  });

  // 로그인 화면으로 전환
  showLogin.addEventListener("click", (e) => {
    e.preventDefault();
    showScreen("login");
  });

  // 회원가입 폼 제출
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

  // 로그인 폼 제출
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    // FastAPI의 OAuth2PasswordRequestForm은 form-data를 사용합니다.
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
      initialize(); // 채팅 화면으로 전환
    } catch (error) {
      alert(`로그인 실패: ${error.message}`);
    }
  });

  // 로그아웃
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("authToken");
    initialize(); // 로그인 화면으로 전환
  });

  // 메시지 전송
  messageForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const prompt = messageInput.value.trim();
    if (!prompt) return;

    displayMessage("user", prompt);
    messageInput.value = "";

    const loadingMessage = displayMessage("ai", "답변을 생성 중입니다...");
    loadingMessage.classList.add("loading-message");

    try {
      const proverbData = await callApi("/chat", "POST", { prompt });
      const proverbText = `[${proverbData.verse}] ${proverbData.content}`;
      const commentText = proverbData.comment;
      loadingMessage.innerHTML = `<p>${proverbText}</p><p>${commentText}</p>`;
      loadingMessage.classList.remove("loading-message");
    } catch (error) {
      console.error("Error:", error);
      loadingMessage.querySelector("p").textContent = "오류가 발생했습니다.";
      loadingMessage.classList.remove("loading-message");
    }
  });

  // --- 히스토리 모달 관련 기능 ---
  historyBtn.addEventListener("click", async () => {
    historyModal.classList.add("active");
    await fetchAndDisplayHistory();
  });

  closeBtn.addEventListener("click", () =>
    historyModal.classList.remove("active")
  );
  window.addEventListener("click", (e) => {
    if (e.target == historyModal) historyModal.classList.remove("active");
  });

  async function fetchAndDisplayHistory() {
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

  // --- 메시지 표시 함수 ---
  function displayMessage(sender, text) {
    const messageContainer = document.createElement("div");
    messageContainer.classList.add("message", `${sender}-message`);
    const messageText = document.createElement("p");
    messageText.textContent = text;
    messageContainer.appendChild(messageText);
    messageDisplay.appendChild(messageContainer);
    messageDisplay.scrollTop = messageDisplay.scrollHeight;
    return messageContainer;
  }

  // 앱 시작
  initialize();
});
