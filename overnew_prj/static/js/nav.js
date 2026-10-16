document.addEventListener('DOMContentLoaded', () => {
    const navContainer = document.querySelector('.bottom-nav');
    if (!navContainer) return;

    const mainPages = [
        '/feed/',
        '/archive/',
        '/recommend/',
        '/discussion/'
    ];

    const currentPath = window.location.pathname;
    const isMainPage = mainPages.some(page => currentPath.includes(page));

    if (!isMainPage) {
        navContainer.style.display = 'none';
        return;
    }

    const navItems = [
        { label: '피드', icon: '◆', href: '/feed/' },
        { label: '아카이브', icon: '●', href: '/archive/' },
        { label: '추천', icon: '▲', href: '/recommend/' },
        { label: '커뮤니티', icon: '◐', href: '/discussion/' },
    ];

    navContainer.innerHTML = navItems.map(item => {
        const isActive = item.href === '/'
            ? currentPath === '/'
            : currentPath.startsWith(item.href);

        return `
            <a href="${item.href}" class="nav-item ${isActive ? 'active' : ''}">
                <div class="nav-icon-wrapper"><span class="nav-icon">${item.icon}</span></div>
                <span class="nav-label">${item.label}</span>
            </a>
        `;
    }).join('');

    const menuBtn = document.getElementById("settings-menu-btn");
    if (menuBtn) {
        menuBtn.addEventListener("click", () => {
            // 🚨 [수정]: '/account/settings/' 경로를 사용합니다.
            window.location.href = "/account/settings/";
        });
    }

    // 알람 버튼 이벤트 (알림 페이지)
    const alarmBtn = document.getElementById("notifications-btn");
    if (alarmBtn) {
        alarmBtn.addEventListener("click", () => {
            // 🚨 [수정]: '/account/notifications/' 경로를 사용합니다.
            window.location.href = "/account/notifications/";
        });

        // 🌟 안 읽은 알림 개수 배지
        fetch('/account/api/notifications/unread-count/')
            .then(res => res.json())
            .then(data => {
                if (!data.count) return;
                const badge = document.createElement('span');
                badge.className = 'notif-badge';
                badge.textContent = data.count > 99 ? '99+' : data.count;
                alarmBtn.appendChild(badge);
            })
            .catch(() => {});
    }
});