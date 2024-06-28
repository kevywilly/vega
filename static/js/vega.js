const post = (url, data, callback = null) => {
    payload = JSON.stringify(data);
    $.ajax({
        method: "POST",
        url: url,
        data: payload,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: callback
    });
}

const get = (url, callback = null) => {
    $.ajax({
        method: "GET",
        url: url,
        contentType: "application/json; charset=utf-8",
        success: callback,
    });
}



const offsetsElem = document.getElementById("offsets")
const positionsElem = document.getElementById("positions")
const anglesElem = document.getElementById("angles")

const handleControlPanelChange = (value) => {
    console.log(value)
    post(`/api/move/${value}`)
}

const controlPanel = new ControlPanel(
    id="controlPanel",
    {onChange: handleControlPanelChange}
);

const heightSlider = new Slider(
    "heightSlider",
    {
        min: 0,
        max: 100,
        step: 5,
        title: "Height (%)",
        name: "height",
        vertical: true,
        onChange: (v) => {}
    }
)
const pitchSlider = new Slider(
    "pitchSlider",
    {
        min: -50,
        max: 50,
        step: 5,
        value: 0,
        title: "Tilt (pitch)",
        name: "pitch",
        vertical: true,
        onChange: (v) => handleUpdateTilt("pitch", v)
    }
);

const yawSlider = new Slider(
    "yawSlider",
    {
        min: -50,
        max: 50,
        step: 5,
        value: 0,
        title: "Tilt (yaw)",
        name: "yaw",
        vertical: true,
        onChange: (v) => handleUpdateTilt("yaw", v)
    }
);

const display4x3Table = (elem, data) => {
    let h = "";
    for(i=0;i<4;i++) {
        h = h + `<div class="font-bold">Leg ${i}</div>`;
        for(j=0;j<3;j++) {
            h = h + `<div>${data[i][j]}</div>`;
        }
    }
    elem.innerHTML = h;
}

const displayStats = (data) => {
    $('#displayHeading').text(data.heading);
    $('#displayPitch').text(data.pitch);
    $('#displayYaw').text(data.yaw);
    $('#displayVoltage').text(data.voltage);

    display4x3Table(positionsElem, data.positions)
    display4x3Table(anglesElem, data.angles)
    display4x3Table(offsetsElem, data.offsets)

    pitchSlider.setValue(data.tilt.pitch)
    yawSlider.setValue(data.tilt.yaw)
    heightSlider.setValue(data.height_pct)
}




const getStats = () => {
    get("api/stats", (data) => {
        displayStats(data);
    });
}



const handleUpdateTilt = (name, value) => {
    post(`/api/tilt/${name}/${value}`, null)
}



const getTilt = () => {
    get("/api/tilt", (data) => {
        PitchSlider.setValue(data.pitch)
        YawSlider.setValue(data.yaw)
    })
}

$(function () {
    $("#btnDemo").on("click", () => {
        get("/api/demo");
    })
    $("#btnSit").on("click", () => {
        post(`/api/pose/sit`, null);
    })
    $("#btnCrouch").on("click", () => {
        post(`/api/pose/crouch`, null);
    })
    $("#btnReady").on("click", () => {
        post(`/api/pose/ready`, null);
    })
    $("#btnLevel").on("click", () => {
        post("/api/level")
    });
    //setInterval(getStats, 1000);
});

