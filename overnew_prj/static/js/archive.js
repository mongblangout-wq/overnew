function goToArticleDetail(articleId) {
    if (!articleId) return;
    window.location.href = `/archive/article/${articleId}/`;
}

// ============================================================
// 1. 데이터 영역
// ============================================================

function getCurrentUserId() {
    try {
        const data = JSON.parse(document.getElementById('user-data-json')?.textContent || 'null');
        return data ? data.id : null;
    } catch {
        return null;
    }
}

function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

// ============================================================
// 2. HTML 생성 함수
// ============================================================

function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function formatDateTime(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    if (isNaN(d)) return isoString;
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function createArticleCardHTML(cardData) {
    const topicClassMap = {
        'IT/과학': 'topic-it', '경제': 'topic-economy', '사회': 'topic-society', '정치': 'topic-politics',
        '연예': 'topic-enter', '스포츠': 'topic-sport', '생활/문화': 'topic-culture', '세계': 'topic-world'
    };
    const categoryClass = topicClassMap[cardData.category] || 'topic-default';
    const cardTitle = cardData.title || "제목 정보 없음";
    const jsonString = JSON.stringify(cardData).replace(/'/g, "&#39;").replace(/"/g, "&quot;");

    const thumb = cardData.image
        ? `<img src="${escapeHTML(cardData.image)}" class="card-thumbnail" alt="">`
        : `<div class="card-thumbnail" style="width:100px; height:60px; flex-shrink:0; border-radius:6px; background:#e5e5e5;"></div>`;

    return `
        <a href="#" class="article-card" data-article-json='${jsonString}'>
            <div class="card-text">
                <span class="card-category ${categoryClass}">${escapeHTML(cardData.category)}</span>
                <span class="card-source">${escapeHTML(cardData.source)}</span>
                <h3 class="card-title">${escapeHTML(cardTitle)}</h3>
                <div class="card-stats">
                    <span>👁️ ${cardData.views}</span> <span>♥ ${cardData.likes ?? 0}</span> <span>${escapeHTML(cardData.time)}</span>
                </div>
            </div>
            ${thumb}
        </a>
    `;
}

function createUserListItemHTML(userData) {
    const tagsHTML = userData.tags.map(tag => `<span class="tag">#${tag}</span>`).join(' ');
    const followingClass = userData.isFollowing ? 'followed' : 'not-followed';
    const buttonText = userData.isFollowing ? '언팔로우' : '팔로우';

    return `
        <div class="user-list-item ${followingClass}">
            <a href="/archive/profile/${userData.id}/" class="user-list-item-info">
                <img src="${userData.avatar}" alt="${userData.nickname}" class="card-avatar-small">
                <div class="user-info">
                    <span class="nickname">${userData.nickname}</span>
                    <div class="user-tags">${tagsHTML}</div>
                </div>
            </a>
            <button type="button" class="follow-btn ${followingClass === 'followed' ? 'followed' : ''}" data-user-id="${userData.id}">
                ${buttonText}
            </button>
        </div>`;
}


// ============================================================
// 3. 렌더링 함수
// ============================================================

// [아카이브 메인] 스크랩 탭 렌더링 — 실제 DB 기반
let _myScrapsCache = null;

async function fetchMyScraps() {
    const userId = getCurrentUserId();
    if (!userId) {
        _myScrapsCache = [];
        return;
    }
    try {
        const res = await fetch(`/archive/users/${userId}/scraps/`);
        _myScrapsCache = await res.json();
    } catch (e) {
        console.error('스크랩 목록 로드 실패:', e);
        _myScrapsCache = [];
    }
}

// 🌟 [신규] 북마크 탭 렌더링 — 실제 DB 기반
let _myBookmarksCache = null;

async function fetchMyBookmarks() {
    const userId = getCurrentUserId();
    if (!userId) {
        _myBookmarksCache = [];
        return;
    }
    try {
        const res = await fetch(`/archive/users/${userId}/bookmarks/`);
        _myBookmarksCache = await res.json();
    } catch (e) {
        console.error('북마크 목록 로드 실패:', e);
        _myBookmarksCache = [];
    }
}

async function renderFeed() {
    const tabInput = document.querySelector('input[name="archive-tab"]:checked');
    if (!tabInput) return;

    const currentTab = tabInput.value; // 'scrap' or 'bookmark'
    const currentTopicEl = document.querySelector('#scrap-bookmark-content .keyword-tag.active');
    const currentTopic = currentTopicEl ? currentTopicEl.dataset.topic : 'politics';
    const currentTopicName = currentTopicEl ? currentTopicEl.textContent.trim() : '정치';

    const feedContainer = document.getElementById(`feed-${currentTab}`);
    if (!feedContainer) return;

    feedContainer.innerHTML = '<p style="text-align: center; color: #888; margin-top: 50px;">불러오는 중...</p>';

    let articles = [];

    if (currentTab === 'scrap') {
        if (!_myScrapsCache) await fetchMyScraps();
        articles = _myScrapsCache.filter(s => s.category === currentTopicName).map(s => ({
            id: s.article_id,
            category: s.category,
            source: s.media,
            title: s.title,
            views: s.views,
            likes: s.likes,
            time: formatDateTime(s.scraped_at),
            image: s.image,
        }));
    } else if (currentTab === 'bookmark') {
        // 🌟 [수정] localStorage 대신 실제 DB(Bookmark 모델) 기반으로 불러옴
        if (!_myBookmarksCache) await fetchMyBookmarks();
        articles = _myBookmarksCache.filter(b => b.category === currentTopicName).map(b => ({
            id: b.article_id,
            category: b.category,
            source: b.media,
            title: b.title,
            views: b.views,
            likes: b.likes,
            time: formatDateTime(b.bookmarked_at),
            image: b.image,
        }));
    }

    feedContainer.innerHTML = '';

    if (articles.length === 0) {
        feedContainer.innerHTML = '<p style="text-align: center; color: #888; margin-top: 50px;">이 주제의 기사가 없습니다.</p>';
        return;
    }
    articles.forEach(article => {
        feedContainer.innerHTML += createArticleCardHTML(article);
    });
}

// [아카이브 메인] 팔로잉 탭 (유저 목록) 렌더링 — 실제 DB 기반
let _followingCache = [];

async function fetchFollowingList() {
    const userId = getCurrentUserId();
    if (!userId) {
        _followingCache = [];
        return;
    }
    try {
        const res = await fetch(`/archive/api/users/${userId}/following/`);
        const data = await res.json();
        _followingCache = data.map(u => ({ ...u, isFollowing: true }));
    } catch (e) {
        console.error('팔로잉 목록 로드 실패:', e);
        _followingCache = [];
    }
}

async function searchUsers(query) {
    try {
        const res = await fetch(`/archive/api/users/search/?q=${encodeURIComponent(query)}`);
        return await res.json();
    } catch (e) {
        console.error('유저 검색 실패:', e);
        return [];
    }
}

async function renderFollowingList(searchTerm = "") {
    const listContainer = document.getElementById('following-list');
    if (!listContainer) return;

    let usersToShow;

    if (searchTerm) {
        usersToShow = await searchUsers(searchTerm);
    } else {
        await fetchFollowingList();
        usersToShow = _followingCache;
    }

    listContainer.innerHTML = '';

    if (usersToShow.length === 0) {
        const msg = searchTerm ? '일치하는 사용자가 없습니다.' : '팔로잉 중인 사용자가 없습니다.';
        listContainer.innerHTML = `<p style="text-align: center; color: #888; margin-top: 50px;">${msg}</p>`;
        return;
    }

    usersToShow.forEach(user => {
        listContainer.innerHTML += createUserListItemHTML(user);
    });

    document.querySelectorAll('.follow-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const targetUserId = button.dataset.userId;
            const myUserId = getCurrentUserId();

            try {
                const res = await fetch('/archive/api/follow/toggle/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: JSON.stringify({ follower_id: myUserId, following_id: targetUserId }),
                });
                const data = await res.json();
                if (res.ok) {
                    renderFollowingList(searchTerm);
                } else {
                    alert(data.error || '처리 중 오류가 발생했습니다.');
                }
            } catch (e) {
                console.error('팔로우 토글 실패:', e);
            }
        });
    });
}


// ============================================================
// 4. 프로필 상세 페이지 로직 (profile-detail.html)
// ============================================================
function initProfileDetailPage() {
    const followBtn = document.getElementById('profile-follow-btn');
    const profileNicknameEl = document.getElementById('profile-nickname');
    const profileTagsEl = document.getElementById('profile-tags');
    const profileFollowersEl = document.getElementById('profile-followers');

    const profileData = JSON.parse(document.getElementById('profile-data-json')?.textContent || 'null');
    if (!profileData) return;

    const { myUserId, targetUserId, targetNickname, targetTopics, targetFollowers } = profileData;
    let isFollowing = profileData.isFollowing;

    profileNicknameEl.textContent = targetNickname;
    if (profileTagsEl) {
        profileTagsEl.textContent = targetTopics.length
            ? targetTopics.map(t => `#${t}`).join(' ')
            : '#관심분야_없음';
    }
    // 팔로워 수 (팔로우/언팔로우하면 바로 증감해서 보여줌)
    let followerCount = targetFollowers;
    const renderFollowerCount = () => {
        if (profileFollowersEl) profileFollowersEl.textContent = `팔로워: ${followerCount}명 ›`;
    };
    renderFollowerCount();
    if (profileFollowersEl) profileFollowersEl.classList.add('clickable');

    const updateFollowButton = () => {
        followBtn.textContent = isFollowing ? '언팔로우' : '팔로우';
        followBtn.classList.toggle('followed', isFollowing);
        followBtn.classList.toggle('not-followed', !isFollowing);
    };
    updateFollowButton();

    followBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/archive/api/follow/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({ follower_id: myUserId, following_id: targetUserId }),
            });
            if (res.ok) {
                isFollowing = !isFollowing;
                updateFollowButton();
                followerCount += isFollowing ? 1 : -1;
                renderFollowerCount();
                if (followersPanelOpen) loadFollowers();
            }
        } catch (e) {
            console.error('팔로우 토글 실패:', e);
        }
    });

    // ----- 이 사람을 팔로우하는 사람들(팔로워) 목록 패널 -----
    const followersPanel = document.getElementById('followers-panel');
    const followersList = document.getElementById('followers-list');
    const followersCloseBtn = document.getElementById('followers-close-btn');
    let followersPanelOpen = false;

    function createFollowerItemHTML(u) {
        const tagsHTML = (u.tags || []).map(t => `<span class="tag">#${escapeHTML(t)}</span>`).join(' ');
        const stateClass = u.isFollowing ? 'followed' : 'not-followed';
        // 나 자신에게는 팔로우 버튼을 보여주지 않음
        const btnHTML = u.isMe ? '' : `
            <button type="button" class="follow-btn ${u.isFollowing ? 'followed' : ''}" data-user-id="${u.id}">
                ${u.isFollowing ? '언팔로우' : '팔로우'}
            </button>`;
        return `
            <div class="user-list-item ${stateClass}">
                <a href="/archive/profile/${u.id}/" class="user-list-item-info">
                    <img src="${escapeHTML(u.avatar)}" alt="" class="card-avatar-small">
                    <div class="user-info">
                        <span class="nickname">${escapeHTML(u.nickname)}${u.isMe ? ' (나)' : ''}</span>
                        <div class="user-tags">${tagsHTML}</div>
                    </div>
                </a>
                ${btnHTML}
            </div>`;
    }

    async function loadFollowers() {
        if (!followersList) return;
        followersList.innerHTML = '<p class="followers-empty">불러오는 중...</p>';
        try {
            const res = await fetch(`/archive/api/users/${targetUserId}/followers/`);
            const data = await res.json();
            if (!res.ok || !Array.isArray(data)) throw new Error('잘못된 응답');
            followersList.innerHTML = data.length
                ? data.map(createFollowerItemHTML).join('')
                : '<p class="followers-empty">아직 팔로워가 없어요.</p>';
        } catch (e) {
            console.error('팔로워 목록 로드 실패:', e);
            followersList.innerHTML = '<p class="followers-empty">팔로워를 불러오지 못했어요.</p>';
        }
    }

    function setFollowersPanel(open) {
        followersPanelOpen = open;
        if (followersPanel) followersPanel.style.display = open ? 'block' : 'none';
        if (open) loadFollowers();
    }

    if (profileFollowersEl && followersPanel) {
        profileFollowersEl.addEventListener('click', () => setFollowersPanel(!followersPanelOpen));
    }
    if (followersCloseBtn) {
        followersCloseBtn.addEventListener('click', () => setFollowersPanel(false));
    }

    // 목록 안의 팔로우/언팔로우 버튼
    if (followersList) {
        followersList.addEventListener('click', async (e) => {
            const btn = e.target.closest('.follow-btn');
            if (!btn) return;
            try {
                const res = await fetch('/archive/api/follow/toggle/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: JSON.stringify({ follower_id: myUserId, following_id: btn.dataset.userId }),
                });
                if (res.ok) loadFollowers();
            } catch (err) {
                console.error('팔로우 토글 실패:', err);
            }
        });
    }

    // 스크랩 목록 로드 (실제 DB)
    let targetScraps = [];

    async function loadTargetScraps() {
        try {
            const res = await fetch(`/archive/users/${targetUserId}/scraps/`);
            targetScraps = await res.json();
        } catch (e) {
            console.error('스크랩 로드 실패:', e);
            targetScraps = [];
        }
    }

    const categoryNameMap = {
        politics: '정치', economy: '경제', society: '사회', culture: '생활/문화',
        it: 'IT/과학', world: '세계', enter: '연예', sport: '스포츠'
    };

    const tabInputs = document.querySelectorAll('input[name="profile-tab"]');
    const keywordTags = document.querySelectorAll('.keyword-list .keyword-tag');

    function renderProfileFeed() {
        const currentTab = document.querySelector('input[name="profile-tab"]:checked').value;
        const activeTag = document.querySelector('.keyword-list .keyword-tag.active');
        const currentTopic = activeTag ? activeTag.dataset.topic : 'politics';
        const currentTopicName = categoryNameMap[currentTopic];

        const listContainer = document.getElementById(currentTab === 'scrap' ? 'profile-scrap-list' : 'profile-bookmark-list');
        if (!listContainer) return;
        listContainer.innerHTML = '';

        if (currentTab === 'bookmark') {
            listContainer.innerHTML = '<p style="text-align: center; color: #888; margin-top: 20px;">북마크 기능은 준비 중입니다.</p>';
            return;
        }

        const filtered = targetScraps.filter(s => s.category === currentTopicName);

        if (filtered.length === 0) {
            listContainer.innerHTML = '<p style="text-align: center; color: #888; margin-top: 20px;">이 주제의 기사가 없습니다.</p>';
            return;
        }

        filtered.forEach(s => {
            listContainer.innerHTML += createArticleCardHTML({
                id: s.article_id,
                category: s.category,
                source: s.media,
                title: s.title,
                views: s.views,
                likes: s.likes,
                time: formatDateTime(s.scraped_at),
                image: s.image,
            });
        });
    }

    tabInputs.forEach(input => {
        input.addEventListener('change', () => {
            document.getElementById('content-scrap').style.display = (input.value === 'scrap') ? 'block' : 'none';
            document.getElementById('content-bookmark').style.display = (input.value === 'bookmark') ? 'block' : 'none';
            renderProfileFeed();
        });
    });

    keywordTags.forEach(tag => {
        tag.addEventListener('click', () => {
            keywordTags.forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
            renderProfileFeed();
        });
    });

    loadTargetScraps().then(renderProfileFeed);
}


// ============================================================
// 5. 기사 스크랩 기능 (create-scrap.html)
// ============================================================
function initScrapFeature() {
    const topicButtons = document.querySelectorAll('.topic-grid-button');
    const sourceInput = document.getElementById('article-source');
    const linkInput = document.getElementById('article-link');
    const submitBtn = document.getElementById('submit-scrap-btn');
    const clearSourceBtn = document.getElementById('clear-source-btn');
    const clearLinkBtn = document.getElementById('clear-link-btn');
    const backButton = document.getElementById('back-button');

    let selectedTopic = null;

    const categoryNameMap = {
        politics: '정치', economy: '경제', society: '사회', culture: '생활/문화',
        it: 'IT/과학', world: '세계', enter: '연예', sport: '스포츠'
    };

    topicButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            topicButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTopic = btn.dataset.topic;
        });
    });

    if (clearSourceBtn) clearSourceBtn.addEventListener('click', () => sourceInput.value = '');
    if (clearLinkBtn) clearLinkBtn.addEventListener('click', () => linkInput.value = '');
    if (backButton) backButton.addEventListener('click', (e) => {
        e.preventDefault();
        window.history.back();
    });

    function getCSRFToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    if (submitBtn) {
        submitBtn.addEventListener('click', async () => {
            const sourceValue = sourceInput.value.trim();
            const linkValue = linkInput.value.trim();

            if (!selectedTopic) { alert('기사의 분야(토픽)를 1개 선택해주세요.'); return; }
            if (!linkValue) { alert('기사 링크를 입력해주세요.'); return; }

            const userInfo = JSON.parse(document.getElementById('user-data-json')?.textContent || 'null');
            const userId = userInfo ? userInfo.id : null;

            if (!userId) {
                alert('로그인 정보를 확인할 수 없습니다. 다시 로그인해주세요.');
                return;
            }

            try {
                const response = await fetch('/archive/articles/upload/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        url: linkValue,
                        news_category: categoryNameMap[selectedTopic],
                        media_name: sourceValue || '출처 미상',
                    }),
                });
                const data = await response.json();

                if (data.article_id) {
                    alert('기사가 스크랩되었습니다!');
                    window.location.href = '/archive/';
                } else {
                    alert('스크랩 실패: ' + (data.error || '알 수 없는 서버 오류'));
                }
            } catch (error) {
                console.error('API 요청 오류:', error);
                alert('네트워크 연결 오류 또는 서버 문제.');
            }
        });
    }
}


// ============================================================
// 6. 메인 실행 (DOMContentLoaded - 통합)
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    const tabInputs = document.querySelectorAll('input[name="archive-tab"]');
    const isArchivePage = tabInputs.length > 0;
    const submitBtn = document.getElementById('submit-scrap-btn');
    const isScrapPage = !!submitBtn;
    const isProfileDetailPage = document.title.includes('프로필');


    // --- B. 뒤로 가기 시 탭 상태 강제 복원 ---
    const storedTab = sessionStorage.getItem('activeArchiveTab'); // 1. 저장된 탭을 가져옴

    let activeArchiveTab = document.querySelector('input[name="archive-tab"]:checked');

    // 2. 세션에 저장된 탭이 있고, 현재 체크된 탭과 다르다면 강제 체크
    if (isArchivePage && storedTab && activeArchiveTab && activeArchiveTab.value !== storedTab) {
        activeArchiveTab.checked = false;

        const targetInput = document.querySelector(`input[name="archive-tab"][value="${storedTab}"]`);
        if (targetInput) {
            targetInput.checked = true;
            activeArchiveTab = targetInput;
        }
    }
    // ----------------------------------------------------

    if (isArchivePage && activeArchiveTab) {
        const scrapBookmarkContent = document.getElementById('scrap-bookmark-content');
        const followingContent = document.getElementById('following-content');
        const fab = document.querySelector('.floating-action-button');
        const currentTabValue = activeArchiveTab.value;

        if (currentTabValue === 'following') {
            if (scrapBookmarkContent) scrapBookmarkContent.style.display = 'none';
            if (followingContent) followingContent.style.display = 'block';
            if (fab) fab.style.display = 'none';
            if (typeof renderFollowingList === 'function') renderFollowingList(document.getElementById('search-user')?.value || "");
        } else {
            if (scrapBookmarkContent) scrapBookmarkContent.style.display = 'block';
            if (followingContent) followingContent.style.display = 'none';
            if (fab) fab.style.display = 'flex';

            const feedScrap = document.getElementById('feed-scrap');
            const feedBookmark = document.getElementById('feed-bookmark');
            if (feedScrap) feedScrap.style.display = (currentTabValue === 'scrap') ? 'flex' : 'none';
            if (feedBookmark) feedBookmark.style.display = (currentTabValue === 'bookmark') ? 'flex' : 'none';

            if (typeof renderFeed === 'function') renderFeed();
        }
    }

    // --- C. 페이지별 초기화 ---
    if (isScrapPage) initScrapFeature();
    if (isProfileDetailPage) initProfileDetailPage();

    // --- D. 아카이브 탭 전환 ---
    if (isArchivePage) {
        const scrapBookmarkContent = document.getElementById('scrap-bookmark-content');
        const followingContent = document.getElementById('following-content');
        const fab = document.querySelector('.floating-action-button');

        tabInputs.forEach(input => {
            input.addEventListener('change', () => {
                // 3. 탭 변경 시 현재 상태를 세션에 저장
                sessionStorage.setItem('activeArchiveTab', input.value);

                if (input.value === 'following') {
                    if (scrapBookmarkContent) scrapBookmarkContent.style.display = 'none';
                    if (followingContent) followingContent.style.display = 'block';
                    if (fab) fab.style.display = 'none';
                    renderFollowingList();
                } else {
                    if (scrapBookmarkContent) scrapBookmarkContent.style.display = 'block';
                    if (followingContent) followingContent.style.display = 'none';
                    if (fab) fab.style.display = 'flex';

                    const feedScrap = document.getElementById('feed-scrap');
                    const feedBookmark = document.getElementById('feed-bookmark');
                    if (feedScrap) feedScrap.style.display = (input.value === 'scrap') ? 'flex' : 'none';
                    if (feedBookmark) feedBookmark.style.display = (input.value === 'bookmark') ? 'flex' : 'none';
                    renderFeed();
                }
            });
        });

        const keywordTags = document.querySelectorAll('#scrap-bookmark-content .keyword-tag');
        keywordTags.forEach(tag => {
            tag.addEventListener('click', () => {
                keywordTags.forEach(t => t.classList.remove('active'));
                tag.classList.add('active');
                renderFeed();
            });
        });

        const searchInput = document.getElementById('search-user');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                renderFollowingList(e.target.value);
            });
        }
    }

    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.preventDefault();
            window.history.back();
        });
    }

    // 🚨 [핵심 추가] 기사 클릭 핸들러 (메인 & 프로필 공통)
    function handleArchiveArticleClick(e) {
    const card = e.target.closest('.article-card');
    if (e.target.closest('.bookmark-btn') || !card) return;

    e.preventDefault();

    const articleData = card.dataset.articleJson ? JSON.parse(card.dataset.articleJson) : null;
    const articleId = articleData?.id;
    goToArticleDetail(articleId);
}

    // 🚨 [리스너 등록] 아카이브 메인 페이지
    const feedScrap = document.getElementById('feed-scrap');
    const feedBookmark = document.getElementById('feed-bookmark');
    if (feedScrap) feedScrap.addEventListener('click', handleArchiveArticleClick);
    if (feedBookmark) feedBookmark.addEventListener('click', handleArchiveArticleClick);

    // 🚨 [리스너 등록] 프로필 상세 페이지 (여기가 중요!)
    const profileScrap = document.getElementById('profile-scrap-list');
    const profileBookmark = document.getElementById('profile-bookmark-list');
    if (profileScrap) profileScrap.addEventListener('click', handleArchiveArticleClick);
    if (profileBookmark) profileBookmark.addEventListener('click', handleArchiveArticleClick);

}); // DOMContentLoaded 종료