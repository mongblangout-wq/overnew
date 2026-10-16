/* ==========================================================================
   1. 공통 함수 (formatTimeAgo, initializeNotifications, CSRF)
   ========================================================================== */

function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function formatTimeAgo(timestamp) {
    const past = new Date(timestamp);
    const now = new Date();
    const diffSeconds = Math.floor((now - past) / 1000);
    const MINUTE = 60, HOUR = MINUTE * 60, DAY = HOUR * 24, MONTH = DAY * 30;

    if (diffSeconds < MINUTE) return "방금 전";
    if (diffSeconds < HOUR) return `${Math.floor(diffSeconds / MINUTE)}분 전`;
    if (diffSeconds < DAY) return `${Math.floor(diffSeconds / HOUR)}시간 전`;
    if (diffSeconds < MONTH) return `${Math.floor(diffSeconds / DAY)}일 전`;

    const year = String(past.getFullYear()).slice(-2);
    const month = String(past.getMonth() + 1).padStart(2, '0');
    const day = String(past.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
}

function initializeNotifications() {
    let readStates = JSON.parse(localStorage.getItem('read_notifications')) || {};
    document.querySelectorAll('.notification-item').forEach(item => {
        const notifId = item.dataset.notifId;
        const notifTime = item.dataset.time;
        const timestampElement = item.querySelector('.notif-timestamp');

        if (notifTime && timestampElement) {
            timestampElement.textContent = formatTimeAgo(notifTime);
        }
        if (notifId && readStates[notifId]) {
            item.classList.add('read');
        }
        item.addEventListener('click', () => {
            if (!notifId) return;
            item.classList.add('read');
            readStates[notifId] = true;
            localStorage.setItem('read_notifications', JSON.stringify(readStates));
        });
    });
}


/* ==========================================================================
   2. 페이지별 초기화 함수들
   ========================================================================== */

function initSplashPage() {
    setTimeout(() => {
        window.location.href = '/feed/';
    }, 2000);
}

function initEmailVerifyPage() {
    const sendCodeBtn = document.getElementById('send-code-btn');
    const verifyCodeBtn = document.getElementById('verify-code-btn');
    const emailInput = document.getElementById('signup-email');
    const codeInput = document.getElementById('signup-code');

    if (sendCodeBtn) {
        sendCodeBtn.addEventListener('click', async () => {
            const email = emailInput.value.trim();

            if (!email) {
                alert('이메일 주소를 입력해주세요.');
                return;
            }

            try {
                const response = await fetch('/account/api/send-email-code/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });

                const data = await response.json();

                if (data.ok) {
                    alert('✅ 메일을 보냈습니다. (10분 이내 입력)');
                } else {
                    alert('전송 실패: ' + (data.error || '알 수 없는 서버 오류'));
                }
            } catch (error) {
                console.error('API 요청 오류:', error);
                alert('네트워크 연결 오류 또는 서버 문제.');
            }
        });
    }

    if (verifyCodeBtn) {
        verifyCodeBtn.addEventListener('click', async () => {
            const email = emailInput.value.trim();
            const code = codeInput.value.trim();

            if (!email || !code) {
                alert('이메일과 인증번호를 모두 입력해주세요.');
                return;
            }

            try {
                const response = await fetch('/account/api/verify-email-code/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, code: code })
                });

                const data = await response.json();

                if (data.ok) {
                    alert('🎉 이메일 인증이 완료되었습니다! 다음 단계로 이동합니다.');
                    window.location.href = '/account/signup/step1/';
                } else {
                    alert('인증 실패: ' + (data.error || '인증번호가 일치하지 않습니다.'));
                }
            } catch (error) {
                console.error('API 요청 오류:', error);
                alert('네트워크 연결 오류 또는 서버 문제.');
            }
        });
    }
}

function initInfoStep5Page() {
    document.getElementById('next-btn-step5').addEventListener('click', async () => {
        const nickname = document.getElementById('nickname').value.trim();
        const userId = document.getElementById('user-id').value.trim();
        const password = document.getElementById('user-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (!nickname || !userId || !password || !confirmPassword) {
            alert('모든 항목을 입력해주세요.');
            return;
        }
        if (password !== confirmPassword) {
            alert('비밀번호가 일치하지 않습니다. 다시 확인해주세요.');
            return;
        }

        try {
            const response = await fetch('/account/api/signup/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: userId,
                    password: password,
                    nickname: nickname
                })
            });

            const data = await response.json();

            if (data.ok) {
                window.location.href = data.redirect_url || '/account/signup/complete/';
            } else {
                alert('회원가입 실패: ' + (data.error || '알 수 없는 서버 오류'));
            }
        } catch (error) {
            console.error('API 요청 오류:', error);
            alert('네트워크 연결 오류 또는 서버 문제.');
        }
    });
}

function initSignupCompletePage() {
    setTimeout(() => {
        window.location.href = '/';
    }, 3000);
}

function initLoginPage() {
    const togglePassword = document.querySelector('.input-icon');
    const passwordInput = document.getElementById('user-password');
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', () => {
            const currentType = passwordInput.getAttribute('type');
            const newType = (currentType === 'password') ? 'text' : 'password';
            passwordInput.setAttribute('type', newType);
        });
    }

    const loginForm = document.getElementById('login-form');
    const userIdInput = document.getElementById('user-id');

    if (loginForm && userIdInput && passwordInput) {
        loginForm.addEventListener('submit', (event) => {
            const id = userIdInput.value.trim();
            const password = passwordInput.value.trim();

            if (id === '' || password === '') {
                event.preventDefault();
                alert('ID와 비밀번호를 모두 입력해주세요.');
            }
        });
    }
}

function initSettingsLoggedInPage() {
    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.preventDefault();
            window.history.back();
        });
    }

    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('정말 로그아웃 하시겠습니까?')) {
                window.location.href = '/account/logout/';
            }
        });
    }

    const profileEditBtn = document.getElementById('profile-edit-btn');
    if (profileEditBtn) {
        profileEditBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/account/profile/edit/';
        });
    }

    const notificationsBtn = document.getElementById('notifications-btn');
    if (notificationsBtn) {
        notificationsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/account/notifications/';
        });
    }

    const deleteAccountBtn = document.getElementById('delete-account-btn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (confirm('정말로 계정을 탈퇴하시겠습니까?\n모든 정보가 삭제되며 이 작업은 되돌릴 수 없습니다.')) {
                try {
                    const response = await fetch('/account/api/account/delete/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCSRFToken(),
                        },
                    });
                    const data = await response.json();

                    if (data.ok) {
                        alert('계정이 성공적으로 삭제되었습니다.');
                        window.location.href = '/account/login/';
                    } else {
                        alert('탈퇴 실패: ' + (data.error || '알 수 없는 서버 오류'));
                    }
                } catch (error) {
                    console.error('API 요청 오류:', error);
                    alert('네트워크 연결 오류 또는 서버 문제.');
                }
            }
        });
    }
}

function initSettingsLoggedOutPage() {
    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.preventDefault();
            window.history.back();
        });
    }
}


/* ==========================================================================
   3. 메인 라우터
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
    const bodyId = document.body.id;

    if (bodyId === 'page-splash') {
        initSplashPage();
    } else if (bodyId === 'page-email-verify') {
        initEmailVerifyPage();
    } else if (bodyId === 'page-info-step5') {
        initInfoStep5Page();
    } else if (bodyId === 'page-login') {
        initLoginPage();
    } else if (bodyId === 'page-notifications') {
        // initNotificationPage();
    } else if (bodyId === 'page-settings-logged-in') {
        initSettingsLoggedInPage();
    } else if (bodyId === 'page-settings-logged-out') {
        initSettingsLoggedOutPage();
    } else if (bodyId === 'page-signup-complete') {
        initSignupCompletePage();
    }
});