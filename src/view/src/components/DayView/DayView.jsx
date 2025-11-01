// src/components/DayView.jsx
import React, { useState } from "react";
import { format, addDays, subDays, isToday } from "date-fns";
import "./DayView.css"; // 👈 Import the stylesheet

function DayView() {
  const [currentDate, setCurrentDate] = useState(new Date());

  const nextDay = () => setCurrentDate(addDays(currentDate, 1));
  const prevDay = () => setCurrentDate(subDays(currentDate, 1));

  return (
    <div className="dayview-container">
      {/* Header */}
      <div className="dayview-header">
        <button className="nav-button" onClick={prevDay}>
          ‹
        </button>
        <h2 className="dayview-title">
          {isToday(currentDate)
            ? "Today"
            : format(currentDate, "EEEE, MMMM d, yyyy")}
        </h2>
        <button className="nav-button" onClick={nextDay}>
          ›
        </button>
      </div>

      {/* Content */}
      <div className="dayview-content">
        <p className="dayview-date">
          {format(currentDate, "EEEE")} — {format(currentDate, "MMMM d, yyyy")}
        </p>

        <div className="dayview-events">
          <h3>Events</h3>
          <ul>
            <li>🕒 9:00 AM — Morning meeting</li>
            <li>🍽️ 12:00 PM — Lunch break</li>
            <li>💻 3:00 PM — Code session</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DayView;
