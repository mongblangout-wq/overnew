function goToArticleDetail(articleId) {
    if (!articleId) return;
    window.location.href = `/archive/article/${articleId}/`;
}

// ====================
// 카테고리 색상 매핑
// ====================
const topicClassMap = {
    'IT/과학': 'topic-it',
    '경제': 'topic-economy',
    '사회': 'topic-society',
    '정치': 'topic-politics',
    '연예': 'topic-enter',
    '스포츠': 'topic-sport',
    '생활/문화': 'topic-culture',
    '세계': 'topic-world'
};

// ====================
// 카드 생성
// ====================
function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function thumbHTML(image) {
    return image
        ? `<img src="${escapeHTML(image)}" class="card-thumbnail" alt="">`
        : `<div class="card-thumbnail" style="width:100px; height:60px; flex-shrink:0; border-radius:6px; background:#e5e5e5;"></div>`;
}

function createHotCardHTML(a) {
    const categoryClass = topicClassMap[a.category] || 'topic-default';
    return `
        <a class="article-card" data-article-id="${a.id}">
            <div class="card-text">
                <span class="card-category ${categoryClass}">${escapeHTML(a.category)}</span>
                <span class="card-source">${escapeHTML(a.source)}</span>
                <h3 class="card-title">${escapeHTML(a.title)}</h3>
                <div class="card-stats">
                    <span>👁️ ${a.views}</span>
                    <span>♥ ${a.likes}</span>
                    <span>${escapeHTML(a.time)}</span>
                </div>
            </div>
            ${thumbHTML(a.image)}
        </a>
    `;
}

function createFollowingCardHTML(item) {
    const { user, article: a } = item;
    const categoryClass = topicClassMap[a.category] || 'topic-default';
    return `
        <div class="following-card-group">
            <div class="follower-header">
                <strong>${escapeHTML(user.nickname)}</strong>님이 열람한 기사
            </div>
            <a class="article-card" data-article-id="${a.id}">
                <div class="card-text">
                    <span class="card-category ${categoryClass}">${escapeHTML(a.category)}</span>
                    <span class="card-source">${escapeHTML(a.source)}</span>
                    <h3 class="card-title">${escapeHTML(a.title)}</h3>
                    <div class="card-stats">
                        <span>👁️ ${a.views}</span> <span>${escapeHTML(a.time)}</span>
                    </div>
                </div>
                ${thumbHTML(a.image)}
            </a>
        </div>
    `;
}

const MSG_STYLE = 'text-align:center; color:#888; margin-top:40px;';

// ====================
// 피드 렌더링 (API 연동)
// ====================
async function renderFeedPage(view, topic) {
    const feedHot = document.getElementById('feed-hot');
    const feedFollowing = document.getElementById('feed-following');
    const container = view === 'hot' ? feedHot : feedFollowing;

    container.innerHTML = `<p style="${MSG_STYLE}">불러오는 중...</p>`;

    try {
        if (view === 'hot') {
            const params = topic ? `?topic=${encodeURIComponent(topic)}` : '';
            const res = await fetch(`/feed/api/hot/${params}`);
            const data = await res.json();

            if (!data.articles || data.articles.length === 0) {
                container.innerHTML = `<p style="${MSG_STYLE}">이 주제의 기사 없음</p>`;
                return;
            }
            container.innerHTML = data.articles.map(createHotCardHTML).join('');
        } else {
            const params = topic ? `?topic=${encodeURIComponent(topic)}` : '';
            const res = await fetch(`/feed/api/following/${params}`);
            const data = await res.json();

            if (data.requires_login) {
                container.innerHTML = `<p style="${MSG_STYLE}">로그인이 필요해요. <a href="/account/login/">로그인하기</a></p>`;
                return;
            }
            if (!data.results || data.results.length === 0) {
                container.innerHTML = `<p style="${MSG_STYLE}">이 주제의 기사 없음</p>`;
                return;
            }
            container.innerHTML = data.results.map(createFollowingCardHTML).join('');
        }
    } catch (e) {
        console.error('피드 로드 실패:', e);
        container.innerHTML = `<p style="${MSG_STYLE}">기사를 불러오지 못했어요.</p>`;
    }
}

// ====================
// DOMContentLoaded
// ====================
document.addEventListener('DOMContentLoaded', () => {
    const keywordList = document.getElementById('keyword-list-container');
    let currentView = document.getElementById('view-hot').checked ? 'hot' : 'following';
    let currentTopic = 'politics';

    document.getElementById('feed-hot').style.display = currentView === 'hot' ? 'flex' : 'none';
    document.getElementById('feed-following').style.display = currentView === 'following' ? 'flex' : 'none';
    keywordList.style.display = 'flex';
    renderFeedPage(currentView, currentTopic);

    document.getElementById('view-hot').addEventListener('change', () => {
        currentView = 'hot';
        document.getElementById('feed-hot').style.display = 'flex';
        document.getElementById('feed-following').style.display = 'none';
        keywordList.style.display = 'flex';
        renderFeedPage(currentView, currentTopic);
    });

    document.getElementById('view-following').addEventListener('change', () => {
        currentView = 'following';
        document.getElementById('feed-hot').style.display = 'none';
        document.getElementById('feed-following').style.display = 'flex';
        keywordList.style.display = 'flex';
        renderFeedPage(currentView, currentTopic);
    });

    document.querySelectorAll('.keyword-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            currentTopic = tag.dataset.topic;
            document.querySelectorAll('.keyword-tag').forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
            renderFeedPage(currentView, currentTopic);
        });
    });

    document.getElementById('settings-menu-btn').addEventListener('click', () => {
        window.location.href = '/account/settings/';
    });

    document.getElementById('feed-hot').addEventListener('click', (e) => {
        const card = e.target.closest('[data-article-id]');
        if (card) goToArticleDetail(card.dataset.articleId);
    });
    document.getElementById('feed-following').addEventListener('click', (e) => {
        const card = e.target.closest('[data-article-id]');
        if (card) goToArticleDetail(card.dataset.articleId);
    });
});