document.addEventListener("DOMContentLoaded", function() {
    const dateField = document.getElementById("id_datetime");

    if (dateField) {
        dateField.addEventListener("change", function() {
            this.blur();  // closes the picker
            console.log("✅ Date selected, picker closed.");
        });
    } else {
        console.error("❌ Date field not found!");
    }
});
