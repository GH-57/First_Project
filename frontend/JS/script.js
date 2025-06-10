// HTML 문서가 모두 로드된 후에 스크립트가 실행되도록 합니다.
document.addEventListener('DOMContentLoaded', function () {

    // 필요한 HTML 요소들을 가져옵니다.
    const moodButtons = document.querySelectorAll('.mood-btn');
    const verseEl = document.getElementById('verse');
    const contentEl = document.getElementById('content');
    const commentEl = document.getElementById('comment');

    // 각 기분 버튼에 클릭 이벤트 리스너를 추가합니다.
    moodButtons.forEach(button => {
        button.addEventListener('click', function () {
            const selectedMood = this.textContent; // 클릭된 버튼의 텍스트(예: '기쁨')를 가져옵니다.

            // 백엔드 API에 요청을 보냅니다.
            fetch('http://127.0.0.1:8000/recommend-proverb', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mood: selectedMood }), // 데이터를 JSON 형식으로 변환하여 보냅니다.
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('네트워크 응답이 올바르지 않습니다.');
                }
                return response.json(); // 응답을 JSON으로 파싱합니다.
            })
            .then(data => {
                // 성공적으로 데이터를 받으면 화면에 표시합니다.
                verseEl.textContent = data.verse;
                contentEl.textContent = `"${data.content}"`;
                commentEl.textContent = data.comment;
            })
            .catch(error => {
                // 에러가 발생하면 콘솔에 에러를 출력하고 사용자에게 알립니다.
                console.error('Fetch 에러:', error);
                verseEl.textContent = '오류 발생';
                contentEl.textContent = '데이터를 불러오는 데 실패했습니다. 서버가 켜져 있는지 확인해주세요.';
                commentEl.textContent = '';
            });
        });
    });
});