document.addEventListener("DOMContentLoaded", () => {
    const deviceTable = document.querySelector(".devices")
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
});