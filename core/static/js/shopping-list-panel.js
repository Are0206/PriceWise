const shoppingListButton =
    document.getElementById("shoppingListButton");

const shoppingListPanel =
    document.getElementById("shoppingListPanel");

const closeShoppingList =
    document.getElementById("closeShoppingList");

const shoppingListContent =
    document.getElementById("shoppingListContent");


shoppingListButton.addEventListener("click", async () => {

    shoppingListPanel.classList.add("open");

    try {

        const response = await fetch(shoppingListsUrl);

        if (!response.ok) {
            throw new Error("Error loading shopping lists");
        }

        const html = await response.text();

        shoppingListContent.innerHTML = html;

    } catch (error) {

        console.error(error);

        shoppingListContent.innerHTML =
            "<p>Error loading shopping lists.</p>";
    }
});


closeShoppingList.addEventListener("click", () => {

    shoppingListPanel.classList.remove("open");

});