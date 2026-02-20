document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("form").addEventListener("submit",async (e) => {
        e.preventDefault()
        let data = {
            name: document.querySelector("input").value,
            startDate: document.querySelectorAll("input")[1].value,
            startTime: document.querySelectorAll("input")[2].value,
            location: document.querySelectorAll("input")[3].value,
            courts: document.querySelectorAll("input")[4].value,
            stream: document.querySelectorAll("input")[5].checked
        }
        console.log(data)
        const response = await fetch("/dashboard/tournament/create", {
            method: "POST",
            headers: {"Content-type" : "application/json"},
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
                alert("Success")
                window.location.href = "/dashboard/"
                break;
        }
        return 0
    });
});