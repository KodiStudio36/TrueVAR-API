const editableCells = document.querySelectorAll(".editable")
const id = document.querySelector("#id").attributes["data-id"].value

Array.from(editableCells).forEach(cell => {
    cell.addEventListener("click", async () => {
        let column = cell.attributes["data-col"].value
        let newValue = null
        if (column == "startTime") {
            newValue = prompt("Zadaj novy cas v tomto formate: (24hodinovy klasicky format) \n\nHH:MM\n\tESC for exit")
        } else if (column == "startDate") {
            newValue = prompt("Zadaj novy datum v tomto formate: \n\nYYYY/MM/DD\n\tESC for exit")
        }
        if (newValue == null) {
            newValue = prompt("Zadaj novu hodnotu.\n\tESC for exit")
        }
        
        if (newValue == null) return
        
        console.log(column, newValue)
        const response = await fetch("/dashboard/tournament/edit", {
            method: "POST",
            headers: {"Content-type": "application/json"},
            body: JSON.stringify({
              column: column,
              value: newValue,
              id: id  
            })
        });

        switch (response.status) {
            case 500:
                alert("Severside error: code 500")
                break;
            case 200:
                alert("Success: 200")
                break;
        }
        window.location.reload()
        return
    });
});