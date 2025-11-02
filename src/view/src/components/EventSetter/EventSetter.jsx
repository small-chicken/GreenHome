import React from "react";
import './EventSetter.css';

function EventSetter() {
    const appliances = [
      {name: "Washing Machine", id: 0},
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
   const [appliance, setAppliance] = React.useState(null);
   const ref = React.useRef(null);

   React.useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)){
        setOpen(false);
        setTimeout(() => document.activeElement?.blur(), 0);
      }
    };
    const onKey = (e) => {
      if (e.key === "Escape"){
        setOpen(false);
        setTimeout(() => document.activeElement?.blur(), 0);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
    }, []);

  const timePrefValid = timePref ? startTime && endTime : true;
  const canSubmit = !!appliance && timePrefValid;
  const btnLabel = timePref
    ? startTime && endTime
      ? "Add event with time preferences"
      : "Select both times…"
    : "Add event with no time preferences";


  const handleSubmit = async () => {
  if (!canSubmit) return;

  let payload = {
    appliance: appliance ? { id: appliance.id, name: appliance.name } : null,
  };

  if (timePref) {
    payload = {
      ...payload,
      timePreferences: {
        start: {
          dayToken: startDay,
          time: startTime,                 // "HH:MM"
        },
        end: {
          dayToken: endDay,
          time: endTime,
        },
      },
    };
  } else {
    payload = { ...payload, timePreferences: null };
  }
  console.log("Submitting event →", payload);
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
              if (!next) e.currentTarget.blur(); 
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
                setAppliance(a);
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
        <button
          type="button"
          className="event-submit"
          onClick={handleSubmit}
          disabled={!canSubmit}
        >
          {btnLabel}
        </button>
    </div>
  );
}



export default EventSetter