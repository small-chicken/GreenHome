import react from "react";
import DayView from "../DayView/DayView.jsx";
import "./DayViewContainer.css";

function DayViewContainer(){

    const todayEvents = [
    "🕒 9:00 AM — Morning meeting",
    "🍽️ 12:00 PM — Lunch break",
    "💻 3:00 PM — Code session",
    ];

    const tomorrowEvents = [
    "🕒 10:00 AM — Review meeting",
    "🍽️ 1:00 PM — Lunch with team",
    "💻 4:00 PM — Finalize project",
    ];

    return (
        <div className="dayview-container">
            <DayView today={true} events={todayEvents} />
            <DayView today={false} events={tomorrowEvents} />
        </div>
    )
}

export default DayViewContainer;

