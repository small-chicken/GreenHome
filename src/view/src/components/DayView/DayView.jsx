import React from "react";
import { format, addDays } from "date-fns";
import "./DayView.css"; 

function DayView({ today, events }) {
  // Get today's date
  const currentDate = today ? new Date() : addDays(new Date(), 1); 

  return (
    <div className="dayview">
      <h2 className="dayview-title">{today ? "Today" : "Tomorrow"}</h2>
      <div className="dayview-date">
        <p>{format(currentDate, "EEEE")}</p>
        <p>{format(currentDate, "MMMM d, yyyy")}</p>
      </div>

      <div className="dayview-events">
        <h3>Events</h3>
        <ul>
          {events.length > 0 ? (
            events.map((event, index) => (
              <li key={index}>{event}</li>
            ))
          ) : (
            <li>No events for today!</li>
          )}
        </ul>
      </div>
    </div>
  );
}

export default DayView;
