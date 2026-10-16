document.addEventListener('DOMContentLoaded', () => {
    const backButton = document.getElementById('back-to-settings');
    const saveButton = document.getElementById('save-profile-btn');
    const nicknameInput = document.getElementById('profile-nickname-input');
    const ageInput = document.getElementById('profile-age-input');
    const topicCheckboxes = document.querySelectorAll('input[name="topics"]');
    const mediaCheckboxes = document.querySelectorAll('input[name="media"]');

    const userDataEl = document.getElementById('user-data');
    const userInfo = userDataEl ? JSON.parse(userDataEl.textContent) : {};

    function getCSRFToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    function loadProfileDataIntoForm() {
        if (nicknameInput) nicknameInput.value = userInfo.nickname || '';
        if (ageInput) ageInput.value = userInfo.age || '';

        const genderRadios = document.querySelectorAll('input[name="gender-selection"]');
        if (userInfo.gender) {
            genderRadios.forEach(radio => {
                if (radio.value === userInfo.gender) radio.checked = true;
            });
        }

        if (Array.isArray(userInfo.topics)) {
            topicCheckboxes.forEach(checkbox => {
                if (userInfo.topics.includes(checkbox.value)) checkbox.checked = true;
            });
        }

        if (Array.isArray(userInfo.media)) {
            mediaCheckboxes.forEach(checkbox => {
                if (userInfo.media.includes(checkbox.value)) checkbox.checked = true;
            });
        }
    }

    async function saveProfileData() {
        const selectedGender = document.querySelector('input[name="gender-selection"]:checked');
        const updatedTopics = Array.from(topicCheckboxes).filter(c => c.checked).map(c => c.value);
        const updatedMedia = Array.from(mediaCheckboxes).filter(c => c.checked).map(c => c.value);

        const payload = {
            nickname: nicknameInput.value.trim(),
            age: ageInput.value.trim(),
            gender: selectedGender ? selectedGender.value : '',
            topics: updatedTopics,
            media: updatedMedia,
        };

        try {
            const response = await fetch('/account/api/profile/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (data.ok) {
                alert('프로필이 성공적으로 수정되었습니다!');
                window.location.replace('/account/settings/');
            } else {
                alert('저장 실패: ' + (data.error || '알 수 없는 서버 오류'));
            }
        } catch (error) {
            console.error('API 요청 오류:', error);
            alert('네트워크 연결 오류 또는 서버 문제.');
        }
    }

    if (saveButton) saveButton.addEventListener('click', saveProfileData);

    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = '/account/settings/';
            }
        });
    }

    loadProfileDataIntoForm();
});