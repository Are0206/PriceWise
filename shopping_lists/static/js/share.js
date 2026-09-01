document.addEventListener('DOMContentLoaded', () => {
    const copyButton = document.querySelector('.share-label-columns button');
    const linkInput = document.getElementById('share-link-input');

    if (copyButton && linkInput) {
        copyButton.addEventListener('click', () => {
            linkInput.select();
            linkInput.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(linkInput.value);
        });
    }
});