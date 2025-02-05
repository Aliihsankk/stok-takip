// Tab geçişleri
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';
}

// Sayfa yüklendiğinde varsayılan tab'ı göster
document.addEventListener('DOMContentLoaded', () => {
    showTab('kayit');
});