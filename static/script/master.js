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

// Get references to the image and file input elements
const companyLogo = document.getElementById('companyLogo');
const imageUpload = document.getElementById('imageUpload');

// Add an event listener to the file input
imageUpload.addEventListener('change', function() {
    const selectedFile = imageUpload.files[0];

    // Check if a file is selected
    if (selectedFile) {
        // Create a FileReader to read the selected file as a data URL
        const reader = new FileReader();

        reader.onload = function(event) {
            // Set the src attribute of the image to the data URL
            companyLogo.src = event.target.result;
        };
        // Read the selected file as a data URL
        reader.readAsDataURL(selectedFile);
    }
    else {
        // If no file is selected, set the src attribute to an empty string to remove the image
        companyLogo.src = '';
    }
    
});

$(document).ready(function () {
  // Function to sort the table
  function sortTable(columnIndex, order) {
    const tableBody = $('.jobDisplay-body');
    const rows = tableBody.find('tr').toArray();

    rows.sort((a, b) => {
      const aValue = $(a).find('td').eq(columnIndex).text();
      const bValue = $(b).find('td').eq(columnIndex).text();

      if (order === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });

    tableBody.empty().append(rows);
  }

  // Click event handler for sorting
  $('.sortable').click(function () {
    const columnIndex = $(this).index();
    const sortOrder = $(this).hasClass('asc') ? 'desc' : 'asc';

    // Remove sorting class from all columns
    $('.sortable').removeClass('asc desc');

    // Add sorting class to the clicked column
    $(this).addClass(sortOrder);

    // Sort the table
    sortTable(columnIndex, sortOrder);
  });
});
