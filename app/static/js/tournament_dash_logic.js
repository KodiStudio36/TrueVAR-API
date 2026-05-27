import { setupEditableCells } from "./tournament_edit.js"

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
const videoids = informationHeader.attributes["data-video-ids"].value.split(" ")
var UPDATING = false

if (scheduled != "False") {
    schedule.classList.add("disabled")
    schedule.innerHTML = "Scheduled."
    document.querySelector("#qr_code_gen").style.display = "initial"
    console.log("scheduled is not false")
} else {
    document.getElementById("visibility").classList.add("editable")
    updateThumbnailsBtn.style.display = 'none'
}
export const editableCells = document.querySelectorAll(".editable")

const main = () => {
    setupEditableCells();
    var element_var = '';
    for (let n = 0; n < number_of_courts; n++) {
        let id = n + 1;
        element_var += `<label for="${id}" class="heading">Thumbnail court ${id}</label>
                        <input type="file" id="image${id}" class="collect">`
    }
    thumbnailForm.innerHTML = element_var
};
document.addEventListener("DOMContentLoaded", main)

updateThumbnailsBtn.addEventListener("click", async () => {
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
    animate(updateThumbnailsBtn, "load")
    const response = await fetch("/dashboard/tournament/thumbnailedit", {
        method: "POST",
        body: data
    });
    const message = await response.json()
    animate(updateThumbnailsBtn, "done", "Update thumbnails")
    switch (response.status) {
        case 200:
            window.location.reload()
            return
        case 500:
            alert(`Server error - ${message["message"]}`)
            window.location.reload()
    }
    UPDATING = false
});

schedule.addEventListener("click", async () => {
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
    data.append("tournament_visibility", document.getElementById("visibility").innerHTML)

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
    animate(schedule, "load")
    const response = await fetch("/dashboard/tournament/schedule", {
        method: "POST",
        body: data
    });
    animate(schedule, "done", "Schedule")
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

            if (document.querySelector(`.goLiveButton2[data-machine-id="${machine_id}"]`).classList.contains("live")) return

            animate(button, "load")
            await fetch(`/api/dashboard/livestream`, {
                method: "POST",
                headers: { "Content-type": "application/json" },
                body: JSON.stringify({
                    machine_id: machine_id,
                    action: action,
                    send_mode: "unicast"
                })
            });
            if (action == "start") {
                await sleep(30000)
                button.setAttribute("data-action", "stop")
                button.classList.add("live")
                animate(button, "done", "Stop Live")
                // ready up the second button
                document.querySelector(`.goLiveButton2[data-machine-id="${machine_id}"]`).className = "goLiveButton2 active"
            } else {
                button.setAttribute("data-action", "start")
                button.classList.remove("live")
                animate(button, "done", "Go Live")
                // disable second golive and start stream button
                document.querySelector(`.goLiveButton2[data-machine-id="${machine_id}"]`).className = "goLiveButton2 disabled"
                document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).className = "startStreamBtn disabled"
            }
            setupButtonBroadcast()
        });
    });
    Array.from(goLiveButton2s).forEach(button => {
        button.addEventListener("click", async () => {
            if (button.classList.contains("disabled")) return
            let machine_id = button.attributes["data-machine-id"].value
            let action = button.attributes["data-action"].value

            if (document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).classList.contains("live")) return

            animate(button, "load")
            await fetch(`/api/dashboard/stream`, {
                method: "POST",
                headers: { "Content-type": "application/json" },
                body: JSON.stringify({
                    machine_id: machine_id,
                    action: action,
                    send_mode: "unicast",
                    tournament_id: tournament_id
                })
            });

            if (action == "start") {
                button.setAttribute("data-action", "stop")
                button.classList.replace("active", "live")
                animate(button, "done", "Stop Live")
                button.innerHTML = "Stop Live"
                // ready up the third button
                document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).className = "startStreamBtn active"
            } else {

                button.setAttribute("data-action", "start")
                button.classList.replace("live", "active")
                animate(button, "done", "Go Live")
                // disable start stream button
                document.querySelector(`.startStreamBtn[data-machine-id="${machine_id}"]`).className = "startStreamBtn disabled"
            }
            setupButtonBroadcast()
        });
    });
    let n = -1;
    Array.from(startStreamBtns).forEach(button => {
        button.addEventListener("click", async () => {
            let court = Number(button.attributes["data-court"].value)
            if (isNaN(court)) {
                alert("Error, this device's court is Not A Number")
                return
            }
            window.open(`https://studio.youtube.com/video/${videoids[court - 1]}/livestreaming`, "_blank")
            // if (button.classList.contains("disabled")) return
            // let machine_id = button.attributes["data-machine-id"].value
            // let action = button.attributes["data-action"].value

            // animate(button, "load")
            // await fetch("/api/dashboard/tournament", {
            //     method: "POST",
            //     headers: { "Content-type": "application/json" },
            //     body: JSON.stringify({
            //         machine_id: machine_id,
            //         action: action,
            //         send_mode: "unicast"
            //     })
            // });

            // if (action == "start") {
            //     button.setAttribute("data-action", "stop")
            //     button.classList.replace("active", "live")
            //     animate(button, "done", "Stop stream")
            // } else {
            //     button.setAttribute("data-action", "start")
            //     button.classList.replace("live", "active")
            //     animate(button, "done", "Start stream")
            // }
            // setupButtonBroadcast()
        });
    });
});

golive1.addEventListener("click", async () => {
    if (golive1.classList.contains("disabled") || golive2.classList.contains("live")) return
    let action = golive1.attributes["data-action"].value
    animate(golive1, "load")
    await fetch(`/api/dashboard/livestream`, {
        method: "POST",
        headers: { "Content-type": "application/json" },
        body: JSON.stringify({
            action: action,
            send_mode: "broadcast"
        })
    });
    window.location.reload()
});
golive2.addEventListener("click", async () => {
    if (golive2.classList.contains("disabled") || startButton.classList.contains("live")) return

    let action = golive2.attributes["data-action"].value
    animate(golive2, "load")
    await fetch(`/api/dashboard/stream`, {
        method: "POST",
        headers: { "Content-type": "application/json" },
        body: JSON.stringify({
            action: action,
            send_mode: "broadcast"
        })
    });
    window.location.reload()
});
startButton.addEventListener("click",async () => {
    // if (startButton.classList.contains("disabled")) return



    // open windows

    // let action = startButton.attributes["data-action"].value
    // animate(startButton, "load")
    // await fetch("/api/dashboard/tournament", {
    //     method: "POST",
    //     headers: { "Content-type": "application/json" },
    //     body: JSON.stringify({
    //         action: action,
    //         send_mode: "broadcast"
    //     })
    // });
    // window.location.reload()
});

const animate = (element, action, newInnerHTML = null) => {
    // action can be: "load", "done"
    if (action == "load") {

        if (!element.classList.contains("disabled")) element.classList.add("disabled")
        element.innerHTML = `<div class="loading">0</div>`
    } else if (action == "done") {

        if (element.classList.contains("disabled")) element.classList.remove("disabled")
        element.innerHTML = newInnerHTML
    }
};

const setupButtonUnicast = (machine_id, state) => {
    // STATE can be:
    // 0 : init - first button active, other are disabled
    // 1 : livestream live - first button live, second active, thirt disabled
    // 2 : stream live - first button live, second live, third active
    // 3 : tournament started - first button live, second live, third live

    let row = document.querySelector(`.deviceRow[data-machine-id="${machine_id}"]`)
    let golive1_unicast = row.querySelector(".goLiveButton1")
    let golive2_unicast = row.querySelector(".goLiveButton2")
    let startStream_unicast = row.querySelector(".startStreamBtn")
    switch (state) {
        case "0":
            golive2_unicast.className = "goLiveButton2 disabled"
            startStream_unicast.className = "startStreamBtn disabled"
            break;

        case "1":
            golive1_unicast.setAttribute("data-action", "stop")
            golive1_unicast.innerHTML = "Stop Live"
            golive1_unicast.className = "goLiveButton1 live"
            golive2_unicast.className = "goLiveButton2 active"
            startStream_unicast.className = "startStreamBtn disabled"
            break;

        case "2":
            golive1_unicast.setAttribute("data-action", "stop")
            golive1_unicast.className = "goLiveButton1 live"
            golive1_unicast.innerHTML = "Stop Live"
            golive2_unicast.setAttribute("data-action", "stop")
            golive2_unicast.className = "goLiveButton2 live"
            golive2_unicast.innerHTML = "Stop Live"
            startStream_unicast.className = "startStreamBtn active"
            break;

        case "3":
            golive1_unicast.setAttribute("data-action", "stop")
            golive1_unicast.className = "goLiveButton1 live"
            golive1_unicast.innerHTML = "Stop Live"
            golive2_unicast.setAttribute("data-action", "stop")
            golive2_unicast.className = "goLiveButton2 live"
            golive2_unicast.innerHTML = "Stop Live"
            startStream_unicast.setAttribute("data-action", "stop")
            startStream_unicast.className = "startStreamBtn live"
            startStream_unicast.innerHTML = "Stop Stream"
            break;
    }
};

const golive1_deviceButtons = document.querySelectorAll(".goLiveButton1")
const golive2_deviceButtons = document.querySelectorAll(".goLiveButton2")
const startStream_deviceButtons = document.querySelectorAll(".startStreamBtn")

document.addEventListener("DOMContentLoaded", async () => {

    let rows = document.querySelectorAll(".deviceRow")
    Array.from(rows).forEach(element => {
        let machine_id = element.attributes["data-machine-id"].value
        let device_state = element.attributes["data-device-state"].value

        setupButtonUnicast(machine_id, device_state)
    });
    setupButtonBroadcast();

    // video is sa asignuje na vsetky golive start stream buttons
    for (let i = 0; i < videoids.length; i++) {
        if (startStream_deviceButtons[i] == undefined) return
        startStream_deviceButtons[i].setAttribute("data-video-id", videoids[i])
    }
});

const setupButtonBroadcast = () => {

    if (Array.from(golive1_deviceButtons).length <= 0) {
        golive1.classList = "disabled"
        golive1.setAttribute("data-action", "start")
        golive1.innerHTML = "Go Live"
        golive2.className = "disabled"
        golive2.setAttribute("data-action", "start")
        golive2.innerHTML = "Go Live"
        startButton.className = "disabled"
        startButton.setAttribute("data-action", "start")
        startButton.innerHTML = "Start Stream"
        return
    }

    let goliveButtons_1_Live = true
    let goliveButtons_2_live = true
    let startStreambuttons_live = true

    Array.from(golive1_deviceButtons).forEach(button => {
        if (!button.classList.contains("live")) goliveButtons_1_Live = false
    });
    Array.from(golive2_deviceButtons).forEach(button => {
        if (!button.classList.contains("live")) goliveButtons_2_live = false
    });
    Array.from(startStream_deviceButtons).forEach(button => {
        if (!button.classList.contains("live")) startStreambuttons_live = false
    });

    if (goliveButtons_1_Live) {
        golive1.classList = "live"
        golive1.setAttribute("data-action", "stop")
        golive1.innerHTML = "Stop Live"
        golive2.className = ""
        golive2.setAttribute("data-action", "start")
        golive2.innerHTML = "Go Live"
        startButton.className = "disabled"
        startButton.setAttribute("data-action", "start")
        startButton.innerHTML = "Start Stream"
    }
    if (goliveButtons_2_live) {
        golive1.className = "live"
        golive1.setAttribute("data-action", "stop")
        golive1.innerHTML = "Stop Live"
        golive2.className = "live"
        golive2.setAttribute("data-action", "stop")
        golive2.innerHTML = "Stop Live"
        startButton.className = ""
        startButton.setAttribute("data-action", "start")
        startButton.innerHTML = "Start Stream"
    }
    if (startStreambuttons_live) {
        golive1.className = "live"
        golive1.setAttribute("data-action", "stop")
        golive1.innerHTML = "Stop Live"
        golive2.className = "live"
        golive2.setAttribute("data-action", "stop")
        golive2.innerHTML = "Stop Live"
        startButton.className = "live"
        startButton.setAttribute("data-action", "stop")
        startButton.innerHTML = "Stop Stream"
    }
    if (!goliveButtons_1_Live && !goliveButtons_2_live && !startStreambuttons_live) {
        golive2.className = "disabled"
        startButton.className = "disabled"
        golive1.className = ""
        golive1.innerHTML = "Go Live"
        golive1.setAttribute("data-action", "start")
    }
};

const sleep = async (ms) => {
    await new Promise((resolve, reject) => {
        setTimeout(() => {
            resolve()
        }, ms)
    })
};

const messageTextArea = document.querySelector("textarea");

document.querySelector("#message_livestream_broadcast").addEventListener("click", async () => {
    if (messageTextArea.value === "") return;

    console.log("message:", messageTextArea.value)
    await fetch("/api/message/broadcast", {
        method: "POST",
        headers: { "Content-type": "application/json" },
        body: JSON.stringify({
            message: messageTextArea.value,
            tournament_id: tournament_id
        })
    });
    alert("Sprava odoslana")
});

document.querySelector("#qr_code_gen").addEventListener("click", () => {
    downloadQR(tournament_id)
});
async function downloadQR(tournament_id) {

    const response = await fetch(
        `/dashboard/tournament/playlist-qr/${tournament_id}`
    );

    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `playlist_${tournament_id}.pdf`;

    document.body.appendChild(a);
    a.click();
    a.remove();
}

const archivedButton = document.querySelector("#archive")
if (informationHeader.attributes["data-state"].value == "init") {
    archivedButton.addEventListener("click", async () => {
        console.log(tournament_id)
        const response = await fetch("/dashboard/tournament/archive", {
            method: "POST",
            headers: { "Content-type": "application/json" },
            body: JSON.stringify({
                id: tournament_id
            })
        });

        switch (response.status) {
            case 500:
                alert("Archiving this tournament failed, server response: 500");
                break;
            case 200:
                alert("Tournament archived. 200");
                break;
        }
        window.location.reload()
    })
} else {
    archivedButton.classList.add("disabled")
    archivedButton.innerHTML = "Tournament archived."
}
