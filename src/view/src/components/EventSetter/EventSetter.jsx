import React from "react";
import './EventSetter.css';

function EventSetter() {
    const appliances = [{name: "Washing Machine", id: 0},
                    {name: "Dishwasher", id: 1},
                    {name: "Dryer", id: 2},
                    {name: "Electric Vehicle", id: 3},
                    {name: "Heating System", id: 4},
                    {name: "Kitchen Appliances", id: 5},
    ]

  const buildSlots = (start = "00:00", end = "23:30", stepMin = 30) => {
  const toMin = (t) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  };
  const toHHMM = (mins) => {
    const h = String(Math.floor(mins / 60)).padStart(2, "0");
    const m = String(mins % 60).padStart(2, "0");
    return `${h}:${m}`;
  };

  const slots = [];
  for (let t = toMin(start); t <= toMin(end); t += stepMin) {
    slots.push(toHHMM(t));
  }
  return slots;
};



  const dayOptions = [
  { label: "Today",    value: "today" },
  { label: "Tomorrow", value: "tomorrow" },
  ];

   const slots = buildSlots("00:00", "23:30", 30);

   const [open, setOpen] = React.useState(false);
   const [label, setLabel] = React.useState("Choose an appliance");
   const [showTimeOption, setShowTimeOption] = React.useState(false);
   const [timePref, setTimePref] = React.useState(false);
   const [startTime, setStartTime] = React.useState("");      
   const [endTime, setEndTime] = React.useState("");     
   const [startDay, setStartDay] = React.useState(dayOptions[0].value);
   const [endDay, setEndDay] = React.useState(dayOptions[0].value); 
   const ref = React.useRef(null);

   React.useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
    }, []);


    const onSubmit = async(e) => {
        e.preventDefault();
        setError("");

        try {
      const response = await fetch("http://127.0.0.1:8000/scheduler/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username:username.trim(), password }),
      });

      if (!response.ok) {
      // DRF sends errors like { non_field_errors: ["Invalid credentials"] }
      const backendError =
        data.non_field_errors?.[0] ||
        data.detail ||
        data.error ||
        "Login failed";
      throw new Error(backendError);
    }

      const data = await response.json();
      console.log("✅ Logged in:", data);

      // Store tokens locally
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);

      // Save user in context
      setUser({
        username: data.user.username,
        email: data.user.email,
        access: data.access,
      });

      // Redirect to schedule
      navigate("/schedule");
    } catch (err) {
      console.error("Error:", err);
      setError(err.message || "Something went wrong");
    }
  };


    return (
    <div className="event-setter">

      <div
        className={`event-dropdown ${open ? "is-open" : ""}`}
        ref={ref}
      >
        <button
          type="button"
          className="event-dropdown__trigger"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={(e) => {
            setOpen(prev => {
              const next = !prev;
              if (!next) e.currentTarget.blur();   // close → remove focus ring
              return next;
            });
          }}
        >
          {label} ▾
        </button>

        <div className="event-dropdown__menu" role="menu">
          {appliances.map((a) => (
            <button
              key={a.id}
              type="button"
              role="menuitem"
              className="event-dropdown__item"
              onClick={() => {
                setLabel(a.name);
                setOpen(false);
                setShowTimeOption(true);
              }}
            >
              {a.name}
            </button>
          ))}
        </div>
        
      </div>
      {showTimeOption && (
        <label className="timepref">
          <input
            id="timePref"
            type="checkbox"
            checked={timePref}
            onChange={(e) => setTimePref(e.target.checked)}
          />
          <span>Select time preferences</span>
        </label>
      )}
      {timePref && (
        <div className="timepicker timepicker--range">
          <div className="timefield">
            <label>Start</label>
            <select
              id="startDay"
              value={startDay}
              onChange={(e) => setStartDay(e.target.value)}
            >
              {dayOptions.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
            </select>

            <select
            id="startTime"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          >
            <option value="" disabled>Pick a time…</option>
            {slots.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          </div>
          <div className="timefield">
            <label>End</label>
            <select
              id="endDay"
              value={endDay}
              onChange={(e) => setEndDay(e.target.value)}
            >
              {dayOptions.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
              </select>

            <select
              id="endTime"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            >
              <option value="" disabled>Pick a time…</option>
              {slots.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          
        </div>
      )} 
        <button type="submit">Add event</button>
    </div>
  );
}



export default EventSetter