const golive1 = document.querySelector("#golive1")
const golive2 = document.querySelector("#golive2")
const startButton = document.querySelector("#startButton")
const schedule = document.querySelector("#schedule")

const thumbnailForm = document.querySelector("#thumbnail")
const courtElement = document.querySelector("#courtnum")
const updateThumbnailsBtn = document.querySelector("#thumbupdate")

const number_of_courts = parseInt(courtElement.innerHTML)
const scheduled = courtElement.attributes["data-scheduled"].value
const informationHeader = document.querySelector("h6") 
const tournament_id = informationHeader.attributes["data-id"].value
const tournament_state = informationHeader.attributes["data-state"].value
var UPDATING = false

if (scheduled != "False") {
    schedule.classList.add("disabled")
    schedule.innerHTML = "Scheduled."
} else {
    updateThumbnailsBtn.style.display = 'none'
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
    var data = new FormData()
    var INVALID = false
    const thumbnailInputs = document.querySelectorAll(".collect")
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
schedule.addEventListener("click",async () => {
    if (scheduled != "False") return

    const thumbnailInputs = document.querySelectorAll(".collect")
    let elements_which_I_want_data_from = document.querySelectorAll(".editable")
    let data = new FormData()

    data.append("name", elements_which_I_want_data_from[0].innerHTML)
    data.append("desc", elements_which_I_want_data_from[1].innerHTML)
    data.append("startDate", elements_which_I_want_data_from[2].innerHTML)
    data.append("startTime", elements_which_I_want_data_from[3].innerHTML)
    data.append("location", elements_which_I_want_data_from[4].innerHTML)
    data.append("courts", document.querySelector("#courtnum").innerHTML)
    data.append("id", tournament_id)

    var INVALID = false
    Array.from(thumbnailInputs).forEach(element => {
        let file = element.files[0]
        
        if (file == undefined) {
            element.style.outline = '1px solid red'
            INVALID = true
            alert("Nezadal si thumbnaily")
        } else {
            element.style.outline = ''
        }
        data.append("image", file)
    });
    if (INVALID) return

    const response = await fetch("/dashboard/tournament/schedule", {
        method: "POST",
        body: data
    });
    switch (response.status) {
        case 500:
            alert("server error")
            break;
        case 200:
            alert("Tournament successfully scheduled. Check youtube studio for more informantion.")
            window.location.reload()
            break;
    }
    return
});

document.addEventListener("DOMContentLoaded", () => {
    const goLiveButton1s = document.querySelectorAll(".goLiveButton1")
    const goLiveButton2s = document.querySelectorAll(".goLiveButton2")
    const startStreamBtns = document.querySelectorAll(".startStreamBtn")

    Array.from(goLiveButton1s).forEach(button => {
        button.addEventListener("click", async () => {
            let machine_id = button.attributes["data-machine-id"].value
            let action = button.attributes["data-action"].value
            if (action == "start") {
                button.setAttribute("data-action", "stop")
                button.classList.add("live")
                button.innerHTML = "Stop Live"
                // ready up the second button
                document.querySelector(`.goLiveButton2[data-machine-id="${machine_id}"]`).className = "goLiveButton2 active"
                console.log("starting live 1")
            } else {
                if (document.querySelector(`.goLiveButton2[data-machine-id="${machine_id}"]`).classList.contains("live")) return
                button.setAttribute("data-action", "start")
                button.classList.remove("live")
                button.innerHTML = "Go Live"
                // disable second golive and start stream button
                document.querySelector(`.goLiveButton2[data-machine-id="${machine_id}"]`).className = "goLiveButton2 disabled"
                document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).className = "startStreamBtn disabled"
                console.log("shutting down live 1")
            }
            
            await fetch(`/api/dashboard/${action}_livestream_unicast`, {
                method: "POST",
                headers: {"Content-type": "application/json"},
                body: JSON.stringify({
                    machine_id: machine_id
                })
            });
        });
    });
    Array.from(goLiveButton2s).forEach(button => {
        button.addEventListener("click",async () => {
            if (button.classList.contains("disabled")) return

            let machine_id = button.attributes["data-machine-id"].value
            let action = button.attributes["data-action"].value
            
            if (action == "start") {
                button.setAttribute("data-action", "stop")
                button.classList.replace("active", "live")
                button.innerHTML = "Stop Live"
                // ready up the third button
                document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).className = "startStreamBtn active"
                console.log("starting live 2")
            } else {
                if (document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).classList.contains("live")) return

                button.setAttribute("data-action", "start")
                button.classList.replace("live", "active")
                button.innerHTML = "Go Live"
                // disable start stream button
                document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).className = "startStreamBtn disabled"
                console.log("shutting down live 2")
            }
        });
    });
    Array.from(startStreamBtns).forEach(button => {
        button.addEventListener("click",async () => {
            if (button.classList.contains("disabled")) return

            let machine_id = button.attributes["data-machine-id"].value
            let action = button.attributes["data-action"].value
            
            await fetch(`/api/dashboard/${action}_tournament_unicast`, {
                method: "POST",
                headers: {"Content-type": "application/json"},
                body: JSON.stringify({
                    machine_id: machine_id
                })
            });
            if (action == "start") {
                button.setAttribute("data-action", "stop")
                button.classList.replace("active", "live")
                button.innerHTML = "Stop stream"
                console.log("starting stream")
            } else {
                button.setAttribute("data-action", "start")
                button.classList.replace("live", "active")
                button.innerHTML = "Start stream"
                console.log("stopping stream")
            }
        });
    });
});