function goToArticleDetail(articleId) {
    if (!articleId) return;
    window.location.href = `/archive/article/${articleId}/`;
}

// ====================
// 추천 탭: 관심사 기반 기사 카드 (DB → API)
// ====================
function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

const MSG_STYLE = 'text-align:center; color:#888; margin-top:40px;';

function createArticleCardHTML(a) {
    const thumb = a.image
        ? `<img src="${escapeHTML(a.image)}" class="card-thumbnail" alt="">`
        : `<div class="card-thumbnail" style="width:100px; height:60px; flex-shrink:0; border-radius:6px; background:#e5e5e5;"></div>`;

    return `
        <a class="article-card" data-article-id="${a.id}">
            <div class="card-text">
                <span class="card-category">${escapeHTML(a.category)}</span>
                <span class="card-source">${escapeHTML(a.source)}</span>
                <h3 class="card-title">${escapeHTML(a.title)}</h3>
                <div class="card-stats">
                    <span>👁️ ${a.views}</span>
                    <span>♥ ${a.likes}</span>
                    <span>${escapeHTML(a.time)}</span>
                </div>
            </div>
            ${thumb}
        </a>
    `;
}

async function renderRecommend(view) {
    const container = document.getElementById(view === 'similar' ? 'feed-similar' : 'feed-opposite');
    container.innerHTML = `<p style="${MSG_STYLE}">불러오는 중...</p>`;

    try {
        const res = await fetch(`/recommend/api/articles/?type=${view}`);
        const data = await res.json();

        if (data.requires_login) {
            container.innerHTML = `<p style="${MSG_STYLE}">로그인이 필요해요. <a href="/account/login/">로그인하기</a></p>`;
            return;
        }
        if (!data.articles || data.articles.length === 0) {
            container.innerHTML = `<p style="${MSG_STYLE}">표시할 기사가 없어요.</p>`;
            return;
        }
        container.innerHTML = data.articles.map(createArticleCardHTML).join('');
    } catch (e) {
        console.error('추천 기사 로드 실패:', e);
        container.innerHTML = `<p style="${MSG_STYLE}">기사를 불러오지 못했어요.</p>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const feedSimilar = document.getElementById('feed-similar');
    const feedOpposite = document.getElementById('feed-opposite');

    function showView(view) {
        feedSimilar.style.display = view === 'similar' ? 'flex' : 'none';
        feedOpposite.style.display = view === 'opposite' ? 'flex' : 'none';
        renderRecommend(view);
    }

    document.getElementById('feed-similar').addEventListener('click', (e) => {
    const card = e.target.closest('[data-article-id]');
    if (card) goToArticleDetail(card.dataset.articleId);
    });
    document.getElementById('feed-opposite').addEventListener('click', (e) => {
        const card = e.target.closest('[data-article-id]');
        if (card) goToArticleDetail(card.dataset.articleId);
    });

    document.querySelectorAll('input[name="view-type"]').forEach(toggle => {
        toggle.addEventListener('change', () => {
            if (toggle.checked) showView(toggle.value);
        });
    });

    showView(document.getElementById('view-opposite').checked ? 'opposite' : 'similar');
});