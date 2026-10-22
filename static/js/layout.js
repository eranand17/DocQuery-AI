
const btn = document.getElementById("menuToggle");
const sidebar = document.querySelector(".sidebar");

if (btn && sidebar) {
    const overlay = document.createElement("div");
    overlay.className = "sidebar-overlay";
    overlay.hidden = true;
    document.querySelector(".app-layout").appendChild(overlay);

    function closeMenu() {
        sidebar.classList.remove("open");
        overlay.hidden = true;
        btn.setAttribute("aria-expanded", "false");
    }

    btn.addEventListener("click", () => {
        const isOpen = sidebar.classList.toggle("open");
        overlay.hidden = !isOpen;
        btn.setAttribute("aria-expanded", String(isOpen));
    });

    overlay.addEventListener("click", closeMenu);
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") closeMenu();
    });
}
