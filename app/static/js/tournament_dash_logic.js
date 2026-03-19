const golive1 = document.querySelector("#golive1")
const golive2 = document.querySelector("#golive2")
const startButton = document.querySelector("#startButton")
const schedule = document.querySelector("#schedule")

const thumbnailForm = document.querySelector("#thumbnail")
const courtElement = document.querySelector("#courtnum")
const updateThumbnailsBtn = document.querySelector("#thumbupdate")

const number_of_courts = parseInt(courtElement.innerHTML)
const scheduled = courtElement.attributes["data-scheduled"].value
const tournament_id = document.querySelector("h6").attributes["data-id"].value
var UPDATING = false

if (scheduled) {
    schedule.innerHTML = "Scheduled."
}

const main = () => {
    var element_var = '';
    for (let n = 0; n < number_of_courts; n++) {
        let id = n + 1;
        element_var += `<label for="${id}" class="heading">Thumbnail court ${id}</label>
                        <input type="file" id="image${id}" class="collect">`
    }
    thumbnailForm.innerHTML = element_var
};
document.addEventListener("DOMContentLoaded", main)

updateThumbnailsBtn.addEventListener("click",async () => {
    if (UPDATING == true || !scheduled) return
    UPDATING = true
    const thumbnailInputs = document.querySelectorAll(".collect")
    var data = new FormData()
    var INVALID = false
    Array.from(thumbnailInputs).forEach(element => {
        let file = element.files[0]
        
        if (file == undefined) {
            element.style.outline = '1px solid red'
            INVALID = true
        } else {
            element.style.outline = ''
        }
        data.append("image", file)
    });
    if (INVALID) {
        UPDATING = false
        return
    }
    data.append("tournament_id", tournament_id)
    const response = await fetch("/dashboard/tournament/thumbnailedit", {
        method: "POST",
        body: data
    });
    const message = await response.json()
    switch (response.status) {
        case 200:
            alert("Thumbanils successfully updated.")
            window.location.reload()
            return
        case 500:
            alert(`Server error - ${message["message"]}`)
            window.location.reload()
    }
    UPDATING = false
});


golive1.addEventListener("click", () => {});
golive2.addEventListener("click", () => {});
startButton.addEventListener("click", () => {});
schedule.addEventListener("click", () => {
    if (scheduled) return
});