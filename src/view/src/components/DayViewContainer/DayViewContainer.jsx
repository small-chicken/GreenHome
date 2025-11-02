import React, {useState, useEffect, useContext} from "react";
import DayView from "../DayView/DayView.jsx";
import "./DayViewContainer.css";
import {startOfDay, addDays, isSameDay} from 'date-fns'
import { AuthContext } from "../../Contexts/AuthContext.jsx";

function DayViewContainer(){
    const [events, setEvents] = useState([]);

    const {user, setUser} = useContext(AuthContext);
    useEffect(() => {
    const username = user.username;

    fetch(`http://127.0.0.1:8000/scheduler/events/?username=${username}`)
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched events:", data);
        setEvents(data);
      })
      .catch((err) => console.error("Error fetching events:", err));
  }, []);

    const today = startOfDay(new Date());
    const tomorrow = addDays(today, 1);

    const eventsToday = events.filter((e) =>
    isSameDay(new Date(e.start_time), today)
  );
  const eventsTomorrow = events.filter((e) =>
    isSameDay(new Date(e.start_time), tomorrow)
  );


    return (
        <div className="dayview-container">
            <DayView today={true} events={eventsToday} />
            <DayView today={false} events={eventsTomorrow} />
        </div>
    )
}

export default DayViewContainer;

