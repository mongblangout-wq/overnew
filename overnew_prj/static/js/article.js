function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.addEventListener('DOMContentLoaded', () => {
    // ---------------------------
    // 1. 뒤로가기 버튼
    // ---------------------------
    const backBtn = document.getElementById('back-button');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = '/feed/';
            }
        });
    }

    // ---------------------------
    // 2. 좋아요 버튼
    // ---------------------------
    const likeBtn = document.getElementById('like-btn');
    if (likeBtn) {
        likeBtn.addEventListener('click', async () => {
            const articleId = likeBtn.dataset.articleId;
            if (!articleId) return;

            likeBtn.disabled = true;
            try {
                const res = await fetch(`/archive/api/articles/${articleId}/like/toggle/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCSRFToken() },
                });

                if (res.status === 403 || res.status === 401) {
                    alert('로그인이 필요해요.');
                    window.location.href = '/account/login/';
                    return;
                }

                const data = await res.json();
                likeBtn.dataset.liked = data.liked ? 'true' : 'false';
                likeBtn.classList.toggle('active', data.liked);
                // 참고: 피드 카드의 하트 카운트는 like_count가 DB에서 바로 계산되므로
                // 피드로 돌아가면 자동으로 최신 값이 보입니다.
            } catch (e) {
                console.error('좋아요 처리 실패:', e);
            } finally {
                likeBtn.disabled = false;
            }
        });
    }

    // ---------------------------
    // 3. 북마크 버튼
    // ---------------------------
    const bookmarkBtn = document.getElementById('bookmark-btn');
    if (bookmarkBtn) {
        bookmarkBtn.addEventListener('click', async () => {
            const articleId = bookmarkBtn.dataset.articleId;
            if (!articleId) return;

            bookmarkBtn.disabled = true;
            try {
                const res = await fetch(`/archive/api/articles/${articleId}/bookmark/toggle/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCSRFToken() },
                });

                if (res.status === 403 || res.status === 401) {
                    alert('로그인이 필요해요.');
                    window.location.href = '/account/login/';
                    return;
                }

                const data = await res.json();
                bookmarkBtn.dataset.bookmarked = data.bookmarked ? 'true' : 'false';
                bookmarkBtn.classList.toggle('active', data.bookmarked);
            } catch (e) {
                console.error('북마크 처리 실패:', e);
            } finally {
                bookmarkBtn.disabled = false;
            }
        });
    }

    // ---------------------------
    // 4. 토론방 선택 버튼
    // ---------------------------
    const discussBtn = document.getElementById('discuss-btn');
    if (discussBtn) {
        discussBtn.addEventListener('click', () => {
            const articleId = discussBtn.dataset.articleId;
            if (!articleId) return;
            window.location.href = `/discussion/${articleId}/`;
        });
    }
});