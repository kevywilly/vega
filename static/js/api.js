let joy_id = 0;
let dir = null;

const joy1Data = {id: 1, x: 0, y: 0, dir: "C"};
const joy2Data = {id: 2, x: 0, y: 0, dir: "C"};


const displayStats = (data) => {
    $('#displayHeading').text(data.heading);
    $('#displayPitch').text(data.pitch);
    $('#displayYaw').text(data.yaw);
    $('#displayVoltage').text(data.voltage);
}

const displayOffsets = (data) => {

    $('input[name="l0_x"]').val(data[0][0]);
    $('input[name="l0_y"]').val(data[0][1]);
    $('input[name="l0_z"]').val(data[0][2]);
    $('input[name="l1_x"]').val(data[1][0]);
    $('input[name="l1_y"]').val(data[1][1]);
    $('input[name="l1_z"]').val(data[1][2]);
    $('input[name="l2_x"]').val(data[2][0]);
    $('input[name="l2_y"]').val(data[2][1]);
    $('input[name="l2_z"]').val(data[2][2]);
    $('input[name="l3_x"]').val(data[3][0]);
    $('input[name="l3_y"]').val(data[3][1]);
    $('input[name="l3_z"]').val(data[3][2]);
}

const displayPose = (data) => {
    $('input[name="pose_x0"]').val(data[0][0]);
    $('input[name="pose_y0"]').val(data[0][1]);
    $('input[name="pose_z0"]').val(data[0][2]);
    $('input[name="pose_x1"]').val(data[1][0]);
    $('input[name="pose_y1"]').val(data[1][1]);
    $('input[name="pose_z1"]').val(data[1][2]);
    $('input[name="pose_x2"]').val(data[2][0]);
    $('input[name="pose_y2"]').val(data[2][1]);
    $('input[name="pose_z2"]').val(data[2][2]);
    $('input[name="pose_x3"]').val(data[3][0]);
    $('input[name="pose_y3"]').val(data[3][1]);
    $('input[name="pose_z3"]').val(data[3][2]);
}

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

const getPose = () => {
    get('/api/pose', function (data){
        displayPose(data)
    })
}


const setPose = (pose) => {
    post('/api/pose',  pose,function (data){
        displayPose(data);
    })
}

const getOffsets = () => {
    get('/api/offsets', function (data){
        displayOffsets(data)
    })
}


const setOffsets = (offsets = p0) => {
    post('/api/offsets',  offsets,function (data){
        displayOffsets(data);
    })
}

const getStats = () => {
    get("api/stats", displayStats);
}

const postJoyData = (data) => {
    if (joy_id !== data.id || dir !== data.dir) {
        joy_id = data.id;
        dir = data.dir;
        post("api/joy", data);
    }
}


// Create JoyStick object into the DIV 'joy1Div'
const Joy1 = new JoyStick('joy1Div', {}, function (stickData) {
    joy1Data.x = stickData.x;
    joy1Data.y = stickData.y;
    joy1Data.dir = stickData.cardinalDirection;
    postJoyData(joy1Data);
});

const Joy2 = new JoyStick('joy2Div', {}, function (stickData) {
    joy2Data.x = stickData.x;
    joy2Data.y = stickData.y;
    joy2Data.dir = stickData.cardinalDirection;
    if (joy2Data.dir !== 'N' && joy2Data.dir !== 'S') {
        postJoyData(joy2Data);
    }
});


const updatePose = () => {
    setPose([
        [
            $('input[name="pose_x0"]').val(),
            $('input[name="pose_y0"]').val(),
            $('input[name="pose_z0"]').val()
        ],
        [
            $('input[name="pose_x1"]').val(),
            $('input[name="pose_y1"]').val(),
            $('input[name="pose_z1"]').val()
        ],
        [
            $('input[name="pose_x2"]').val(),
            $('input[name="pose_y2"]').val(),
            $('input[name="pose_z2"]').val()
        ],
        [
            $('input[name="pose_x3"]').val(),
            $('input[name="pose_y3"]').val(),
            $('input[name="pose_z3"]').val()
        ],
    ])
}

const updateOffsets = () => {
    setOffsets([
        [
            $('input[name="l0_x"]').val(),
            $('input[name="l0_y"]').val(),
            $('input[name="l0_z"]').val()
        ],
        [
            $('input[name="l1_x"]').val(),
            $('input[name="l1_y"]').val(),
            $('input[name="l1_z"]').val()
        ],
        [
            $('input[name="l2_x"]').val(),
            $('input[name="l2_y"]').val(),
            $('input[name="l2_z"]').val()],
        [
            $('input[name="l3_x"]').val(),
            $('input[name="l3_y"]').val(),
            $('input[name="l3_z"]').val()
        ]
    ])
}

const resetOffsets = () => {
    setOffsets([])
}

const resetPose = () => {
    setPose([])
}

setInterval(getStats, 2000);

$(function() {
    getOffsets();
    getPose();
    $( "#btnUpdateP0" ).on( "click", updateOffsets );
    $( "#btnResetP0" ).on( "click", resetOffsets );
    $( "#btnUpdatePose" ).on( "click", updatePose );
    $( "#btnResetPose" ).on( "click", resetPose );
});
