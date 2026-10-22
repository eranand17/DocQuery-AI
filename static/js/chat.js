
const chat = document.getElementById("messages-container");

function scrollToLatest() {
    if (chat) {
        chat.scrollTop = chat.scrollHeight;
    }
}

if (chat) {
    scrollToLatest();

    window.addEventListener("load", scrollToLatest);

    const observer = new MutationObserver(scrollToLatest);
    observer.observe(chat, { childList: true, subtree: true });
}
