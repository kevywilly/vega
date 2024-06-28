/*
<button class="button-blue">Forward L.</button>
            <button class="button-blue">Forward</button>
            <button class="button-blue">Forward R.</button>
            <button class="button-blue">Left</button>
            <button class="button-blue">Stop</button>
            <button class="button-blue">Right</button>
            <button class="button-blue col-span-3">Backward L</button>
            <button class="button-blue col-span-3">Backward</button>
            <button class="button-blue col-span-3">Backward R.</button>
 */

const ControlPanelParams = {
    onChange: (value) => {}
}

var ControlPanel = (function (id, params={}) {


    const {onChange} = {...ControlPanelParams, ...params};

    elem = document.getElementById(id);

    const buttons = [
        {value: "FORWARD_LT", label: "Forward LT"},
        {value: "FORWARD", label: "Forward"},
        {value: "FORWARD_RT", label: "Forward RT"},
        {value: "LEFT", label: "Left"},
        {value: "STOP", label: "Stop"},
        {value: "RIGHT", label: "Right"},
        {value: "BACKWARD_LT", label: "Backward LT"},
        {value: "BACKWARD", label: "Backward"},
        {value: "BACKWARD_RT", label: "Backward RT"},
    ]

    let cmd = null

    const handleClick = (e,value,index) => {
        if (value === cmd) {
            cmd = "STOP";
            e.target.style.opacity=1.0;
        } else {
            cmd = value;
            if(cmd !== "STOP") {
                e.target.style.opacity = 0.5;
            }
        }
        onChange(cmd)
    }

    for(i=0; i<buttons.length; i++) {
        const v = buttons[i].value;
        const l = buttons[i].label;
        let e = document.createElement("button");
        e.id=`controlButton${i}`
        e.innerText=buttons[i].label;
        e.className="button button-blue";
        if(v==="STOP") {
            e.style.background="#ff0000"
        }
        e.onclick = (e) => {handleClick(e,v,i)};
        elem.appendChild(e)
    }

});