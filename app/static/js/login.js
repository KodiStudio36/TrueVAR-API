document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("form").addEventListener("submit", async (e) => {
        e.preventDefault()
        let data = {
            email: document.querySelector("input").value,
            password: document.querySelectorAll("input")[1].value
        }
        console.log(data)
        const response = await fetch("/dashboard/auth/login", {
            method: "POST",
            headers: { "Content-type": "application/json" },
            body: JSON.stringify(data)
        });
        console.log(`Response: ${response.status}`)
        data = await response.json()
        switch (response.status) {
            case 400:
                alert(data["message"])
                break;
            case 401:
                alert(data["message"])
                document.querySelectorAll("input")[1].style.outline = "red"
                break;
            case 200:
                window.location.href = "/dashboard"
                break;
        }
        return 0
    });
});