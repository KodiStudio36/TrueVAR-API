
var REMOVE_ID = null;

document.addEventListener("DOMContentLoaded", () => {
    // live updating of devices
    const deviceTable = document.querySelector(".devices")
    const trashButtons = document.querySelectorAll(".trashIcon")
    const promoteIcons = document.querySelectorAll(".promote")
    const cancelButton = document.getElementById("cancel")
    const removeButton = document.getElementById("remove")
    const you_sureContainer = document.querySelector(".yousureCon")
    const youSureHeading = you_sureContainer.querySelector(".displaytournament")

    if (deviceTable != undefined) {
        Array.from(deviceTable.querySelectorAll("td")).forEach(cell => {
            cell.addEventListener("click", async () => {
                let license_id = cell.attributes["data-id"].value
                let column = cell.attributes["data-col"].value

                let value = prompt("Give me a new value\nType:\n\t press ESC for exit\n\t type 'null' for null")
                if (value == null) return null;
                
                await fetch("/dashboard/devices/edit", {
                    method: "POST",
                    headers: { "Content-type" : "application/json" },
                    body: JSON.stringify({
                        license_key: license_id,
                        column: column,
                        value: value
                    })
                });
                window.location.reload()
            });
        });
    }
    Array.from(trashButtons).forEach(trash => {
        trash.addEventListener("click", () => {
            let remove_id = trash.attributes["data-id"].value
            let remove_name = trash.attributes["data-name"].value
            REMOVE_ID = remove_id
            youSureHeading.innerHTML = remove_name
            you_sureContainer.style.display = 'flex'
        });
    });
    Array.from(promoteIcons).forEach(icon => {
        icon.addEventListener("click",async () => {
            let id = icon.attributes["data-id"].value

            const response = await fetch("/dashboard/tournament/promote", {
                method: "POST",
                headers: {"Content-type": "application/json"},
                body: JSON.stringify({
                    id: id
                })
            });
            switch (response.status) {
                case 200:
                    alert("success")
                    break;
                case 500:
                    alert("Server Error")
                    break;
            }
            window.location.reload()
        });
    });
    cancelButton.addEventListener("click", () => {
        you_sureContainer.style.display = 'none'
    });
    removeButton.addEventListener("click",async () => {
        const response = await fetch(`/dashboard/tournament/delete/${REMOVE_ID}`, {
            method: "DELETE",
        });
        switch (response.status) {
            case 200:
                alert("success")
                window.location.reload()
                break;
            case 500:
                alert("Server Error")
                break;
        }
        you_sureContainer.style.display = 'none'
    });
});