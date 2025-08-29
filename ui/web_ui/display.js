function updateImage() {
    window.pywebview.api.get_image().then(base64img => {
        document.getElementById("display").src = base64img;
    });
}

document.addEventListener("DOMContentLoaded", updateImage);
