document.addEventListener("DOMContentLoaded", function() {
    const gallery = document.getElementById("avatar-gallery");
    const hiddenInput = document.getElementById("selected-avatar");

    
    if (!gallery || !hiddenInput) {
        return; 
    }

    gallery.addEventListener("click", function(e) {
        if (e.target.classList.contains("avatar-option")) {
            if (e.target.classList.contains("selected")) {
                e.target.classList.remove("selected");
                hiddenInput.value = "";
            } else {
                document.querySelectorAll(".avatar-option").forEach(img => img.classList.remove("selected"));
                e.target.classList.add("selected");
                hiddenInput.value = e.target.dataset.value;
            }
        }
    });
});