export function initInfiniteScroll({
    endpoint,
    containerId,
    renderItem,
    perPage = 14,
    triggerOffset = 200
}) {
    let currentPage = 1;
    let loading = false;
    let hasMore = true;

    const container = document.getElementById(containerId);
    const loadingIndicator = document.getElementById("loading");

    async function loadMore() {
        if (loading || !hasMore) return;
        loading = true;
        if (loadingIndicator) loadingIndicator.style.display = "block";

        try {
            const res = await fetch(`${endpoint}?page=${currentPage}&per_page=${perPage}`);
            const data = await res.json();

            data.players.forEach(player => {
                const element = renderItem(player);
                container.appendChild(element);
            });

            hasMore = data.has_more;
            currentPage++;
        } catch (err) {
            console.error("Infinite scroll error:", err);
        }

        loading - false;
        if (loadingIndicator) loadingIndicator.style.display = hasMore ? "block" : "none";
    }

    window.addEventListener("scroll", () => {
        const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - triggerOffset;
        if (nearBottom) loadMore();
    });

    //Initial load
    document.addEventListener("DOMContentLoaded", loadMore);
}