let currentPage = 0;
const pages = document.querySelectorAll('.page');
const slider = document.querySelector('.slider');

function nextPage() {
    if (currentPage < pages.length - 1) {
        currentPage++;
        updateSlider();
    }
}

function updateSlider() {
    slider.style.transform = `translateX(-${currentPage * 100}%)`;
}

document.getElementById('configureLink').addEventListener('click', function(event) {
    event.preventDefault();
    alert('Configure email recipients here.');
});

function copyToClipboard() {
    const textField = document.querySelector('.copy-text');
    textField.select();
    navigator.clipboard.writeText(textField.value).then(() => {
        alert('Link copied to clipboard!');
    });
}

function goToPage4() {
    const selectedOption = document.getElementById("actionChoice").value;
    alert("You selected: " + selectedOption);
   
    document.getElementById("page3").style.display = "none";
    document.getElementById("page4").style.display = "block";
}

function submitForm() {
    const branchName = document.getElementById("branch_name").value;
    const numCommits = document.getElementById("number_of_commits").value;
    const runButton = document.querySelector(".btn"); 
    const errorMessage = document.getElementById("error-message");

    
    if (!branchName || !numCommits) {
        alert("Please enter all required details.");
        return;
    }

    runButton.style.display = "none";  

    fetch("/run", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `branch_name=${encodeURIComponent(branchName)}&number_of_commits=${encodeURIComponent(numCommits)}`
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.detail || "Error occurred!");
            });
        }
        return response.json();
    })
    .then(data => {
    
        document.getElementById("suggestedTest").value = data.testcases.join("\n");
        document.getElementById("suggestedRecipe").value = data.recipes.join("\n");

        document.getElementById("page2").style.display = "block"; 
    })
    .catch(error => {
        console.error("Error:", error);
        errorMessage.style.display = "block";
        errorMessage.textContent = error.message;
        runButton.style.display = "block";
    });
}

document.getElementById("runForm").addEventListener("submit", function(event) {
    event.preventDefault();
    submitForm();
});
