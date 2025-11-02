import React from "react";
import { format, addDays, parse, isSameDay, isBefore } from "date-fns";
import "./DayView.css"; 

function DayView({ today, events }) {
  const currentDate = today ? new Date() : addDays(new Date(), 1); 
  const now = new Date();
  const isTodayCard = isSameDay(currentDate, now);

  return (
    <div className="dayview">
      <div className="dayview-header">
        <h2 className="dayview-title">{today ? "Today" : "Tomorrow"}</h2>
        <div className="dayview-date">
          <p>{format(currentDate, "EEEE")}</p>
          <p>{format(currentDate, "MMMM d, yyyy")}</p>
        </div>
      </div>
      <div className="dayview-events">
        <h3>Events</h3>
        <ul>
          {events.length > 0 ? (
            events.map((event, index) => {
              const start = new Date(event.start_time);
              const isPast = isTodayCard && isBefore(start, now);

              return (
                <li key={index} className={`event-item ${isPast ? "is-past" : ""}`}>
                  <strong>{event.appliance_name}</strong> —{" "}
                  {format(start, "h:mm a")}
                </li>
              );
            })
          ) : (
            <li>No events for today!</li>
          )}
        </ul>
      </div>
    </div>
  );
}


export default DayView;
