const shoppingListButton =
    document.getElementById("shoppingListButton");

const shoppingListPanel =
    document.getElementById("shoppingListPanel");

const closeShoppingList =
    document.getElementById("closeShoppingList");

const shoppingListContent =
    document.getElementById("shoppingListContent");


const params = new URLSearchParams(window.location.search);

if (shoppingListPanel && params.get("open_lists") === "true") {
    openShoppingListPanel();
}


// The button and panel only exist for logged-in users.
shoppingListButton?.addEventListener("click", () => {
    openShoppingListPanel();
});

async function openShoppingListPanel() {

    shoppingListPanel.classList.add("open");
    // While closed the panel is inert, so Tab cannot reach its hidden links.
    shoppingListPanel.inert = false;
    shoppingListButton?.setAttribute("aria-expanded", "true");
    closeShoppingList.focus();

    try {

        const response = await fetch(shoppingListsUrl);

        if (!response.ok) {
            throw new Error("Error loading shopping lists");
        }

        const html = await response.text();

        shoppingListContent.innerHTML = html;

        // The lists slide in after the panel, a beat behind each other.
        if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
            gsap.from(shoppingListContent.querySelectorAll('.shopping-list-items li'), {
                x: 16, autoAlpha: 0, duration: 0.35, ease: 'expo.out', stagger: 0.03, clearProps: 'all',
            });
        }

    } catch (error) {

        console.error(error);

        shoppingListContent.innerHTML =
            "<p class=\"empty-state\">No se pudieron cargar tus listas. Intenta de nuevo.</p>";
    }
}

function closeShoppingListPanel() {
    if (!shoppingListPanel.classList.contains("open")) return;
    shoppingListPanel.classList.remove("open");
    shoppingListPanel.inert = true;
    shoppingListButton?.setAttribute("aria-expanded", "false");
    shoppingListButton?.focus();
}

closeShoppingList?.addEventListener("click", closeShoppingListPanel);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeShoppingListPanel();
});
