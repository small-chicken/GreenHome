import React from "react";
import { format, addDays, parse, isSameDay, isBefore } from "date-fns";
import "./DayView.css"; 

function DayView({ today, events }) {
  const currentDate = today ? new Date() : addDays(new Date(), 1); 
  
  const parseEventTime = (text, baseDate) => {
    const m12 = text.match(/\b(\d{1,2}:\d{2}\s*[AP]M)\b/i);
    if (m12) return parse(m12[1].toUpperCase(), "h:mm a", baseDate);

    const m24 = text.match(/\b([01]?\d|2[0-3]):[0-5]\d\b/);
    if (m24) return parse(m24[0], "HH:mm", baseDate);

    return null;
  };

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
              const eventTime = parseEventTime(event, currentDate);
              const isPast = isTodayCard && eventTime && isBefore(eventTime, now);
              return (
                <li key={index} className={`event-item ${isPast ? "is-past" : ""}`}>
                  {event}
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
