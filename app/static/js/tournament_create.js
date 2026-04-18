const courtsInput = document.querySelector("#courts")
const secondForm = document.querySelector(".imageInputs")
const streamCheckbox = document.querySelector("#stream")

// var ktora trackuje ci je treba poslat thumbnaily do backendu
var thumbnails = false
var WORKING = false

document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("form").addEventListener("submit",async (e) => {
        e.preventDefault()
        if (WORKING) return
        WORKING = true
        const formData = new FormData()
        const fields = ["name", "desc", "startDate", "startTime", "location", "courts"]
        
        for (let i = 0; i < fields.length; i++) {
            formData.append(fields[i], document.querySelectorAll(".getmethoseDATA")[i].value)
        }
        
        // logger
        // for (const [key, value] of formData.entries()) {
            //     console.log(key, value);
            // }
            const response = await fetch("/dashboard/tournament/create", {
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
                window.location.href = "/dashboard/"
                break;
            case 500:
                alert("Server error")
                break;
        }
        return 0
        });
        courtsInput.addEventListener("input", secondFormRender)
        streamCheckbox.addEventListener("change", secondFormRender)
});

const secondFormRender = () => {
    let value = parseInt(courtsInput.value)

    if (value == 0 || isNaN(value) || !streamCheckbox.checked) {
        secondForm.style.display = 'none'
        return
    }

    if (value > 5000) {
        secondForm.innerHTML = "Moc vela courtov"
        return
    }

    let elements = ''
    for (let i = 0; i < value; i++) {
        elements = elements + `<label for="image1">Choose thumbnail for court ${i + 1}</label>
                               <input type="file" id="image${i + 1}" accept="image/*">`
    }

    secondForm.style.display = 'flex'
    secondForm.innerHTML = elements
    return 0
}