function toggleDropdown() {
    var dropdownOptions = document.getElementById("dropdownOptions");
    if (dropdownOptions.style.display === "block") {
        dropdownOptions.style.display = "none";
    } else {
        dropdownOptions.style.display = "block";
    }
}

// Add a click event listener to the document
document.addEventListener("click", function (event) {
    var dropdown = document.querySelector(".dropdown");
    if (!dropdown.contains(event.target)) {
        // Clicked outside the dropdown, so close it
        var dropdownOptions = document.getElementById("dropdownOptions");
        dropdownOptions.style.display = "none";
    }
});
