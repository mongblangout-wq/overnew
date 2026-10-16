function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

// 🌟 [수정] linkClass 파라미터 추가 - 아바타는 클래스 없이, 닉네임은 comment-user-link 클래스로 감쌈
function userLinkHTML(data, isAnonymous, innerHTML, linkClass = '') {
    if (isAnonymous) return innerHTML;
    const classAttr = linkClass ? ` class="${linkClass}"` : '';
    return `<a href="/archive/profile/${data.user_id}/"${classAttr}>${innerHTML}</a>`;
}

function createCommentHTML(data, isAnonymous) {
    const avatarClass = isAnonymous ? 'comment-avatar anonymous-placeholder' : 'comment-avatar';
    return `
        <div class="comment-item" data-comment-id="${data.id}">
            ${userLinkHTML(data, isAnonymous, `<div class="${avatarClass}"></div>`)}
            <div class="comment-content">
                <div class="comment-header">
                    ${userLinkHTML(data, isAnonymous, `<span class="comment-user">${escapeHTML(data.display_name)}</span>`, 'comment-user-link')}
                    <span class="comment-date">${escapeHTML(data.created_at)}</span>
                </div>
                <p class="comment-text">${escapeHTML(data.content)}</p>
                <div class="comment-actions">
                    <button type="button" class="action-btn like-btn" data-comment-id="${data.id}">
                        <span>♥</span>0
                    </button>
                    <button type="button" class="action-btn reply-btn" data-comment-id="${data.id}">답글</button>
                </div>
                <div class="reply-list" data-parent-id="${data.id}"></div>
            </div>
        </div>
    `;
}

function createReplyHTML(data, isAnonymous) {
    const avatarClass = isAnonymous ? 'comment-avatar anonymous-placeholder' : 'comment-avatar';
    return `
        <div class="comment-item" data-comment-id="${data.id}">
            ${userLinkHTML(data, isAnonymous, `<div class="${avatarClass}"></div>`)}
            <div class="comment-content">
                <div class="comment-header">
                    ${userLinkHTML(data, isAnonymous, `<span class="comment-user">${escapeHTML(data.display_name)}</span>`, 'comment-user-link')}
                    <span class="comment-date">${escapeHTML(data.created_at)}</span>
                </div>
                <p class="comment-text">${escapeHTML(data.content)}</p>
            </div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('comment-form');
    if (!form) return;

    const commentList = document.getElementById('comment-list');
    const parentIdInput = document.getElementById('parent-id-input');
    const contentInput = form.querySelector('input[name="content"]');
    const cancelReplyBtn = document.getElementById('cancel-reply-btn');
    const isAnonymous = document.body.dataset.roomType === 'anonymous';

    let replyTarget = null;

    function resetReplyMode() {
        replyTarget = null;
        parentIdInput.value = '';
        contentInput.placeholder = 'Add a comment';
        if (cancelReplyBtn) cancelReplyBtn.style.display = 'none';
    }

    if (cancelReplyBtn) {
        cancelReplyBtn.addEventListener('click', () => {
            resetReplyMode();
            contentInput.focus();
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = contentInput.value.trim();
        if (!content) return;

        const formData = new FormData(form);

        try {
            const res = await fetch(form.action, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() },
                body: formData,
            });
            const data = await res.json();

            if (!res.ok) {
                alert(data.error || '댓글 등록에 실패했습니다.');
                return;
            }
            // 새 댓글이 최초 댓글이면, "아직 댓글이 없습니다" 안내문구 제거
            const emptyMsg = commentList.querySelector('p.empty-comment-message');
            if (emptyMsg) emptyMsg.remove();

            if (data.parent_id) {
                const replyList = commentList.querySelector(`.reply-list[data-parent-id="${data.parent_id}"]`);
                if (replyList) {
                    replyList.insertAdjacentHTML('beforeend', createReplyHTML(data, isAnonymous));
                }
            } else {
                commentList.insertAdjacentHTML('beforeend', createCommentHTML(data, isAnonymous));
            }

            contentInput.value = '';
            resetReplyMode();
        } catch (err) {
            console.error('댓글 등록 오류:', err);
            alert('네트워크 연결 오류 또는 서버 문제.');
        }
    });

    commentList.addEventListener('click', async (e) => {
        const replyBtn = e.target.closest('.reply-btn');
        const likeBtn = e.target.closest('.like-btn');

        if (replyBtn) {
            const commentId = replyBtn.dataset.commentId;
            const userSpan = replyBtn.closest('.comment-content').querySelector('.comment-user');
            replyTarget = commentId;
            parentIdInput.value = commentId;
            contentInput.placeholder = `@${userSpan.textContent} 님에게 답글 남기기`;
            if (cancelReplyBtn) cancelReplyBtn.style.display = 'inline-flex';
            contentInput.focus();
            return;
        }

        if (likeBtn) {
            const commentId = likeBtn.dataset.commentId;
            try {
                const res = await fetch(`/discussion/comment/${commentId}/like/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCSRFToken() },
                });
                const data = await res.json();
                likeBtn.innerHTML = `<span>♥</span>${data.like_count}`;
                likeBtn.classList.toggle('active', data.liked);
            } catch (err) {
                console.error('좋아요 처리 오류:', err);
            }
        }
    });
});