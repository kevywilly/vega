class JoyData {
  constructor() {
    this.px = 0;
    this.py = 0;
    this.dir = 0;
    this.x = 0;
    this.y = 0
  }
}

const joy1Data = { "x": 0, "y": 0, "dir": "C"};
const joy2Data = { "x": 0, "y": 0, "dir": "C"};


// Create JoyStick object into the DIV 'joy1Div'
const Joy1 = new JoyStick('joy1Div', {}, function(stickData) {
    joy1Data.x = stickData.x;
    joy1Data.y = stickData.y;
    joy1Data.dir = stickData.cardinalDirection;
    console.log(joy1Data);
});

const Joy2 = new JoyStick('joy2Div', {}, function(stickData) {
    joy2Data.x = stickData.x;
    joy2Data.y = stickData.y;
    joy2Data.dir = stickData.cardinalDirection;
    console.log(joy2Data);
});



