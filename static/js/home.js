function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");

    sidebar.classList.toggle("open");
    overlay.classList.toggle("active");
}

function toggleAdminMode() {
    const userContent = document.getElementById("user-content");
    const adminContent = document.getElementById("admin-content");

    const isAdminVisible = adminContent.style.display === "block";
    adminContent.style.display = isAdminVisible ? "none" : "block";
    userContent.style.display = isAdminVisible ? "block" : "none";
}
