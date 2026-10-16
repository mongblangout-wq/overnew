const CODE_TO_CATEGORY_NAME = {
    politics: '정치',
    economy: '경제',
    society: '사회',
    culture: '생활/문화',
    it: 'IT/과학',
    world: '세계',
};

document.addEventListener('DOMContentLoaded', () => {
    const keywordList = document.getElementById('keyword-list');
    const feed = document.getElementById('discussion-feed');
    if (!keywordList || !feed) return;

    const cards = feed.querySelectorAll('.discussion-card');

    function filterByTopic(topic) {
        const categoryName = CODE_TO_CATEGORY_NAME[topic];
        cards.forEach(card => {
            card.style.display = (card.dataset.category === categoryName) ? '' : 'none';
        });
    }

    keywordList.querySelectorAll('.keyword-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            keywordList.querySelectorAll('.keyword-tag').forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
            filterByTopic(tag.dataset.topic);
        });
    });

    // 첫 진입 시 기본 active 태그(정치) 기준으로 필터링
    const initialTag = keywordList.querySelector('.keyword-tag.active');
    if (initialTag) filterByTopic(initialTag.dataset.topic);
});