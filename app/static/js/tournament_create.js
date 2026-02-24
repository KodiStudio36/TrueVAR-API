const courtsInput = document.querySelector("#courts")
const secondForm = document.querySelector(".imageInputs")
const streamCheckbox = document.querySelector("#stream")

// var ktora trackuje ci je treba poslat thumbnaily do backendu
var thumbnails = false

document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("form").addEventListener("submit",async (e) => {
        e.preventDefault()
        const formData = new FormData()
        const fields = ["name", "startDate", "startTime", "location", "courts"]

        for (let i = 0; i < fields.length; i++) {
            formData.append(fields[i], document.querySelectorAll("input")[i].value)
        }
        formData.append("stream", streamCheckbox.checked)

        if (streamCheckbox.checked) {
            let courts = parseInt(courtsInput.value)
            if (isNaN(courts)) return

            for (let i = 0; i < courts; i++) {
                let file = document.querySelector(`#image${i + 1}`).files[0]
                if (file == undefined) {
                    alert("Neuploadol si vsetky images")
                    return
                }
                formData.append("image", file)
            }
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
        switch (response.status) {
            case 400:
                alert(data["message"])
                break;
            case 200:
                alert("Success")
                window.location.href = "/dashboard/"
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