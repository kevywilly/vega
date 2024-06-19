let joy_id = 0;
let dir = null;

const joy1Data = {id: 1, x: 0, y: 0, dir: "C"};
const joy2Data = {id: 2, x: 0, y: 0, dir: "C"};

const postJoyData = (data) => {

    if (joy_id === data.id && dir === data.dir) {
        return;
    } else {
        joy_id = data.id;
        dir = data.dir;
    }

    payload = JSON.stringify(data);
    $.ajax({
        method: "POST",
        url: "api/joy",
        data: payload,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
    });
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
