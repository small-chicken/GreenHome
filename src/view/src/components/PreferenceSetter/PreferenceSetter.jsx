import {useState} from "react";

function PreferenceSetter({appliance}) {
    const [checked, setChecked] = useState(false);

    return (
        <div className = "preference-setter">
            <div className = "preference-name"> 
                <h3>{appliance.name}</h3>
            </div>
            <input className = "preference-toggle"
                type="checkbox"
                checked={checked}
                onChange={() => {   
                    setChecked(!checked);
                }}>
            </input>
        </div> 
    )
}

export default PreferenceSetter