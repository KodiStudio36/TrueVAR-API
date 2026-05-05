var WORKING = false

document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("form").addEventListener("submit",async (e) => {
        e.preventDefault()
        if (WORKING) return
        WORKING = true
        const formData = new FormData()
        const fields = ["name", "desc", "startDate", "startTime", "location", "courts", "discipline"]
        
        for (let i = 0; i < fields.length; i++) {
            formData.append(fields[i], document.querySelectorAll(".getmethoseDATA")[i].value)
        }

        // logger
        // for (const [key, value] of formData.entries()) {
            //     console.log(key, value);
            // }

        const response = await fetch("/dashboard/public/tournament/create", {
            method: "POST",
            body: formData
        });
        console.log(`Response: ${response.status}`)
        data = await response.json()
        WORKING = false
        switch (response.status) {
            case 400:
                alert(data["message"])
                break;
            case 200:
                alert("Success")
                window.location.href = "/"
                break;
            case 500:
                alert("Server error")
                break;
        }
        return 0
        });
});