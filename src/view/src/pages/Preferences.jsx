import Header from "../components/Header/Header.jsx";
import PreferenceSetter from "../components/PreferenceSetter/PreferenceSetter.jsx";

function Preferences () {
    const appliances = [{name: "Washing Machine", id: 0},
                    {name: "Dishwasher", id: 1},
                    {name: "Dryer", id: 2},
                    {name: "Electric Vehicle", id: 3},
                    {name: "Heating System", id: 4},
                    {name: "Kitchen Appliances", id: 5},
    ]
    return (
        <div>
            <Header />
            <div className = "preferences-grid">
                {appliances.map((appliance) => (
                <PreferenceSetter appliance={appliance} key={appliance.id} />
            ))}
            </div>
        </div>
    )
}

export default Preferences;