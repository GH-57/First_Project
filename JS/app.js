function sendQuestion() {
  const input = document.getElementById("question");
  const question = input.value;

  fetch("http://127.0.0.1:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: question })
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById("response").innerText = data.reply;
    input.value = ""; // input 초기화
  });
}
