/**
 * 티스토리 쿠키 추출 — 안드로이드 크롬 주소창에 붙여넣기
 *
 * 사용법:
 *   1. 안드로이드 크롬에서 galaxys21-pwuser.tistory.com 접속 (로그인된 상태)
 *   2. 주소창에 아래 코드 전체를 복사해서 붙여넣기 (앞에 javascript: 붙여서)
 *   3. 팝업된 JSON을 전체 복사
 *   4. Termux에서: termux-clipboard-get > /root/work/.tistory_cookies_raw.json
 *
 * 또는 간단히:
 *   1. 크롬 주소창에: javascript:alert(document.cookie)
 *   2. 팝업된 문자열을 Termux 클립보드로 복사
 */

// 방법 1: 전체 JSON (Playwright storage_state 형식으로 변환 가능)
(function() {
  const cookies = document.cookie.split('; ').map(c => {
    const [name, ...rest] = c.split('=');
    return {
      name: name.trim(),
      value: rest.join('='),
      domain: '.tistory.com',
      path: '/',
      httpOnly: false,
      secure: true,
      sameSite: 'Lax'
    };
  });

  const output = JSON.stringify({cookies: cookies, origins: []}, null, 2);

  // 방법 A: 화면에 출력
  const pre = document.createElement('pre');
  pre.textContent = output;
  pre.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#fff;z-index:99999;overflow:auto;padding:20px;font-size:12px;';
  document.body.appendChild(pre);

  // 방법 B: 클립보드에 복사 시도
  try {
    navigator.clipboard.writeText(output);
    pre.textContent = '✅ 클립보드에 복사됨!\n\n' + output;
  } catch(e) {
    pre.textContent = '⚠️ 클립보드 복사 실패. 수동으로 복사하세요.\n\n' + output;
  }
})();
